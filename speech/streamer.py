import os
import sys

# Ensure CUDA 12 runtime DLLs are discoverable
_venv_nvidia = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".venv", "Lib", "site-packages", "nvidia")
for _pkg in ["cublas", "cudnn", "cuda_nvrtc"]:
    _dll_path = os.path.join(_venv_nvidia, _pkg, "bin")
    if os.path.isdir(_dll_path):
        try:
            os.add_dll_directory(_dll_path)
            os.environ["PATH"] = _dll_path + os.pathsep + os.environ["PATH"]
        except Exception:
            pass

# openWakeWord replaced by Whisper-based wake detection
import logging
import re
import threading
import config
from faster_whisper import WhisperModel
from speech.vad import SileroVAD
import queue
import sounddevice as sd
import numpy as np
from typing import Callable

logging.basicConfig(level=logging.INFO , format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PRIVACY68.SpeechStreamer")

class SpeechStreamer:
    @staticmethod
    def _build_wake_pattern(wake_input: str) -> re.Pattern:
        """
        Builds a regex pattern from one or more custom wake words.
        Supports any arbitrary unique word or phrase (e.g. 'Zephyr', 'Bumblebee', 'Kratos', 'Aegis').
        """
        if not wake_input:
            wake_input = "sana"
        
        words = [w.strip() for w in wake_input.replace("/", ",").split(",") if w.strip()]
        if not words:
            words = ["sana"]

        aliases = set()
        for w in words:
            clean = re.sub(r'[^a-zA-Z0-9\s]', '', w).lower().strip()
            if not clean:
                continue
            aliases.add(clean)

        regex_parts = [r'\b' + re.escape(a) + r'\b' for a in sorted(aliases, key=len, reverse=True)]
        pattern_str = "|".join(regex_parts)
        return re.compile(pattern_str, re.IGNORECASE)

    def is_wake_word_detected(self, text: str) -> bool:
        """
        Generic, dynamic detector for ANY unique wake word.
        Uses exact regex matching + dynamic phonetic/fuzzy similarity (0.80 threshold)
        so any unique custom name (e.g. 'Zephyros', 'Bumblebee', 'Valkyrie') matches
        even if Whisper slightly mishears a single vowel or consonant.
        """
        if not text:
            return False

        # 1. Direct Regex / Substring check
        if self.wake_pattern.search(text):
            return True

        # 2. Dynamic Fuzzy Matching on word n-grams (handles arbitrary unique names)
        import difflib
        cleaned_words = [w.strip(".!?, \t\n").lower() for w in text.split()]
        target_wake_words = [w.strip().lower() for w in self.wake_word.replace("/", ",").split(",") if w.strip()]

        for target in target_wake_words:
            # Check single words
            for cw in cleaned_words:
                if not cw:
                    continue
                similarity = difflib.SequenceMatcher(None, target, cw).ratio()
                if similarity >= 0.82:
                    logger.info(f"Fuzzy wake word match: '{cw}' matches '{target}' (Similarity: {similarity:.2f})")
                    return True
            
            # Check 2-word ngrams (e.g. 'bumble bee' for 'bumblebee')
            target_no_spaces = target.replace(" ", "")
            for i in range(len(cleaned_words) - 1):
                bigram = cleaned_words[i] + cleaned_words[i+1]
                similarity = difflib.SequenceMatcher(None, target_no_spaces, bigram).ratio()
                if similarity >= 0.82:
                    logger.info(f"Fuzzy ngram wake word match: '{bigram}' matches '{target}' (Similarity: {similarity:.2f})")
                    return True

        return False

    def strip_wake_word(self, text: str) -> str:
        """Removes the wake word from one-shot inline commands for ANY unique name."""
        res = self.wake_pattern.sub('', text)
        # Also clean leading 'hey', 'ok', 'sana', etc.
        res = re.sub(r'^(hey|ok|okay|hi|hello)\s+', '', res, flags=re.IGNORECASE)
        return res.strip(".!?, \t\n")

    def __init__(self, wake_word: str = None) -> None:
        self.sample_rate = config.SAMPLE_RATE
        self.silence_threshold = getattr(config, "SILENCE_THRESHOLD", 0.008)
        self.silence_duration_chunks = config.SILENCE_DURATION_CHUNKS
        self.vad = SileroVAD(threshold=getattr(config, "VAD_THRESHOLD", 0.50))
        self.is_active = False

        # Load user-configured custom wake word (e.g. Nova, Leo, Serena, Sana)
        if wake_word:
            self.wake_word = wake_word
        else:
            try:
                from plugins.profile_manager import profile_manager
                self.wake_word = profile_manager.get("wake_word", getattr(config, "WAKE_WORD_MODEL", "sana"))
            except Exception:
                self.wake_word = getattr(config, "WAKE_WORD_MODEL", "sana")

        self.wake_pattern = self._build_wake_pattern(self.wake_word)
        logger.info(f"Custom Wake Word initialized: '{self.wake_word}' (Patterns: {self.wake_pattern.pattern})")

        logger.info(f"Loading whisper model {config.WHISPER_MODEL_SIZE} on {config.WHISPER_DEVICE}")

        try:
            self.model = WhisperModel(
                config.WHISPER_MODEL_SIZE,
                device=config.WHISPER_DEVICE,
                compute_type=config.WHISPER_COMPUTE_TYPE,
                num_workers=1,      # limit worker threads → less RAM overhead
                cpu_threads=2,      # cap CPU threads → pushes compute to GPU
            )
            # Warm up GPU inference so first command is instant
            _warmup = np.zeros(config.SAMPLE_RATE, dtype=np.float32)
            list(self.model.transcribe(_warmup, beam_size=1, without_timestamps=True)[0])
            logger.info(f"Whisper model warmed up on {config.WHISPER_DEVICE}.")
        except Exception as e:
            if config.WHISPER_DEVICE == "cuda":
                logger.warning(f"Failed to load Whisper model on CUDA ({e}). Falling back to multi-core CPU (int8)...")
                try:
                    self.model = WhisperModel(
                        config.WHISPER_MODEL_SIZE,
                        device="cpu",
                        compute_type="int8",
                        num_workers=1,
                        cpu_threads=4,
                    )
                    logger.info("Whisper model successfully loaded on CPU (int8 fallback mode).")
                except Exception as cpu_e:
                    logger.error(f"Failed to load Whisper model on CPU fallback: {cpu_e}")
                    raise
            else:
                logger.error(f"failed to load whisper model: {e}")
                raise

        
        self.is_muted = False
        self.audio_queue: queue.Queue = queue.Queue()
        self.stream = sd.InputStream(
            samplerate = self.sample_rate,
            channels = config.CHANNELS,
            dtype = config.DTYPE,
            blocksize = config.BLOCK_SIZE,
            callback = self._audio_callback,
        )

    def set_muted(self, muted: bool) -> None:
        """Sets the microphone mute state."""
        self.is_muted = muted
        if muted:
            self.is_active = False
            # Clear any pending audio
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
        logger.info(f"SpeechStreamer microphone {'MUTED' if muted else 'UNMUTED'}.")

    def toggle_mute(self) -> bool:
        """Toggles the microphone mute state. Returns new muted state."""
        self.set_muted(not self.is_muted)
        return self.is_muted

    def set_wake_word(self, wake_word: str) -> None:
        """Dynamically updates the active wake word(s)."""
        self.wake_word = wake_word.strip()
        self.wake_pattern = self._build_wake_pattern(self.wake_word)
        logger.info(f"Updated active wake word to: '{self.wake_word}' (Pattern: {self.wake_pattern.pattern})")

    def _audio_callback(self, indata: np.ndarray, frames: int, time: dict, status: sd.CallbackFlags) -> None:
        # callback executed for each audio buffer
        if status:
            logger.warning(f"Audio stream status flag set: {status}")
        # If muted, do not queue audio to whisper
        if not self.is_muted:
            self.audio_queue.put(indata.copy())
    
    def start(
        self,
        on_text_callback: Callable[[str], bool],
        on_wake_word_callback: Callable[[], None] = None,
        on_audio_energy_callback: Callable[[float], None] = None,
        on_sleep_callback: Callable[[], None] = None
    ) -> None:
        audio_buffer = []
        idle_buffer = []          # Short rolling buffer used for wake word detection
        silence_counter = 0
        has_spoken = False

        # Scan every 0.8 seconds (faster detection window)
        IDLE_WINDOW_CHUNKS = int(self.sample_rate * 0.8 / config.BLOCK_SIZE)
        # Overlap: keep last half of the buffer so wake word at window boundaries is never missed
        IDLE_OVERLAP_CHUNKS = IDLE_WINDOW_CHUNKS // 2

        logger.info(f"SANA Voice Assistant is online. Say '{self.wake_word}' to activate.")
        try:
            with self.stream:
                while self.stream.active:
                    if self.is_muted:
                        idle_buffer.clear()
                        audio_buffer.clear()
                        if on_audio_energy_callback:
                            on_audio_energy_callback(0.0)
                        import time as _t
                        _t.sleep(0.05)
                        continue

                    try:
                        chunk = self.audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    # 1. Idle state: Listen for custom wake word via Whisper
                    if not self.is_active:
                        # Accumulate audio into idle_buffer
                        idle_buffer.append(chunk)

                        if len(idle_buffer) >= IDLE_WINDOW_CHUNKS:

                            # Transcribe the short idle buffer using Whisper
                            idle_audio = np.concatenate(idle_buffer).flatten()

                            # Overlapping window — keep last half for next scan
                            idle_buffer = idle_buffer[IDLE_OVERLAP_CHUNKS:]

                            # Skip transcribing silence in idle mode
                            if float(np.max(np.abs(idle_audio))) < 0.012:
                                continue

                            segments, _ = self.model.transcribe(
                                idle_audio,
                                beam_size=2,
                                without_timestamps=True,
                                language='en',
                                vad_filter=False,
                            )
                            idle_text = " ".join([s.text.strip() for s in segments]).strip()

                            if idle_text:
                                logger.debug(f"Idle scan heard: '{idle_text}'")

                            # Check if user said the custom wake word (ANY unique name)
                            if self.is_wake_word_detected(idle_text):
                                logger.info(f"Wake word '{self.wake_word}' matched in: '{idle_text}'")

                                if on_wake_word_callback:
                                    on_wake_word_callback()

                                # Play activation beep (if enabled in config)
                                if getattr(config, "ENABLE_BEEP", False):
                                    try:
                                        import winsound
                                        threading.Thread(target=lambda: winsound.MessageBeep(winsound.MB_ICONASTERISK), daemon=True).start()
                                    except Exception:
                                        pass

                                # Check if the wake word was a one-shot command
                                # e.g. "Hey Zephyr open notepad" — strip wake phrase and execute directly
                                inline_command = self.strip_wake_word(idle_text)
                                if inline_command:
                                    logger.info(f"Inline command detected: '{inline_command}'")
                                    on_text_callback(inline_command)
                                    if on_sleep_callback:
                                        on_sleep_callback()
                                    with self.audio_queue.mutex:
                                        self.audio_queue.queue.clear()
                                    continue

                                # No inline command — activate full listening mode
                                self.is_active = True
                                self.vad.reset()
                                has_spoken = False
                                silence_counter = 0
                                audio_buffer.clear()
                        continue

                    # 2. Active state: Record voice command
                    audio_buffer.append(chunk)
                    volume = float(np.sqrt(np.mean(chunk**2)))

                    if on_audio_energy_callback:
                        on_audio_energy_callback(volume)

                    # Silero Neural VAD: check for actual human speech
                    is_voice = self.vad.is_speech(chunk)

                    if is_voice:
                        has_spoken = True
                        silence_counter = 0
                    else:
                        if has_spoken:
                            silence_counter += 1

                    # Check timeout if user never spoke after wake word
                    total_chunks = len(audio_buffer)
                    timeout_chunks = int(self.sample_rate * 5.0 / config.BLOCK_SIZE)
                    if not has_spoken and total_chunks >= timeout_chunks:
                        logger.info("No speech detected after wake word. Returning to sleep.")
                        audio_buffer.clear()
                        self.vad.reset()
                        self.is_active = False
                        if on_sleep_callback:
                            on_sleep_callback()
                        with self.audio_queue.mutex:
                            self.audio_queue.queue.clear()
                        continue

                    # Process command when speech finishes (silence detected) or max duration reached (8s)
                    max_chunks = int(self.sample_rate * 8.0 / config.BLOCK_SIZE)
                    # Require minimum silence pause of ~1.0s after speech before finalizing
                    silence_cutoff = max(self.silence_duration_chunks, 12)  # ~1.0 second
                    if (has_spoken and silence_counter >= silence_cutoff) or (has_spoken and total_chunks >= max_chunks):
                        logger.info("Processing speech command...")
                        full_audio = np.concatenate(audio_buffer).flatten()

                        # ── Anti-hallucination gate 1: RMS Energy & Peak Check ──
                        rms = float(np.sqrt(np.mean(full_audio**2)))
                        max_peak = float(np.max(np.abs(full_audio)))
                        
                        if rms < 0.004 or max_peak < 0.01:
                            logger.info(f"Audio energy too low (RMS: {rms:.4f}, Peak: {max_peak:.4f}). Ignoring background noise.")
                            audio_buffer.clear()
                            self.vad.reset()
                            self.is_active = False
                            if on_sleep_callback:
                                on_sleep_callback()
                            with self.audio_queue.mutex:
                                self.audio_queue.queue.clear()
                            continue

                        # Normalize audio volume so Whisper receives clean, high-gain signal
                        if max_peak > 0.005:
                            full_audio = (full_audio / max_peak) * 0.9

                        segments, info = self.model.transcribe(
                            full_audio,
                            beam_size=config.WHISPER_BEAM_SIZE,
                            temperature=0.0,
                            condition_on_previous_text=False,
                            without_timestamps=True,
                            language='en',
                            vad_filter=True,
                            initial_prompt=config.INITIAL_PROMPT,
                            hotwords=config.WHISPER_HOTWORDS,
                        )

                        # ── Anti-hallucination gate 2: no_speech_prob check ──
                        if info and getattr(info, "no_speech_prob", 0.0) > 0.65:
                            logger.info(f"Whisper flagged segment as non-speech (no_speech_prob={info.no_speech_prob:.2f}). Discarding.")
                            text = ""
                        else:
                            text = " ".join([segment.text.strip() for segment in segments]).strip()

                        # ── Anti-hallucination gate 3: Common silence artifacts filter ──
                        HALLUCINATION_PATTERNS = {
                            "thank you.", "thank you very much.", "thank you", "thanks for watching.",
                            "subtitles by", "you", "bye.", "bye", "okay.", "okay"
                        }
                        if text.lower().strip() in HALLUCINATION_PATTERNS and rms < 0.015:
                            logger.info(f"Filtered out hallucination artifact '{text}' on low-energy audio.")
                            text = ""

                        if text:
                            logger.info(f"Transcribed: '{text}'")
                            on_text_callback(text)
                        else:
                            logger.info("Could not recognize any speech.")
                        
                        # Return to sleep mode to avoid unwanted inputs
                        if on_sleep_callback:
                            on_sleep_callback()

                        # Reset state
                        audio_buffer.clear()
                        self.vad.reset()
                        silence_counter = 0
                        has_spoken = False
                        self.is_active = False

                        # Clear audio queue to avoid stale audio
                        with self.audio_queue.mutex:
                            self.audio_queue.queue.clear()
                        logger.info("Command completed. SANA is in sleep mode (Say 'Sana' to speak).")

        except Exception as e:
            logger.error(f"Error in streaming pipeline: {e}")
            raise