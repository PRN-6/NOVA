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
logger = logging.getLogger("NOVA.SpeechStreamer")

class SpeechStreamer:
    def __init__(self) -> None:
        self.sample_rate = config.SAMPLE_RATE
        self.silence_threshold = getattr(config, "SILENCE_THRESHOLD", 0.008)
        self.silence_duration_chunks = config.SILENCE_DURATION_CHUNKS
        self.vad = SileroVAD(threshold=getattr(config, "VAD_THRESHOLD", 0.50))
        self.is_active = False

        logger.info("Using Whisper-based 'Hey Nova' / 'Nova' wake word detection.")

        logger.info(f"Loading whisper model {config.WHISPER_MODEL_SIZE} on {config.WHISPER_DEVICE}")

        try:
            self.model = WhisperModel(
                config.WHISPER_MODEL_SIZE,
                device=config.WHISPER_DEVICE,
                compute_type=config.WHISPER_COMPUTE_TYPE
            )
            # Warm up GPU inference so first command is instant
            _warmup = np.zeros(config.SAMPLE_RATE, dtype=np.float32)
            list(self.model.transcribe(_warmup, beam_size=1, without_timestamps=True)[0])
            logger.info("Whisper model warmed up on GPU.")
        except Exception as e:
            logger.error(f"failed to load whisper model: {e}")
            raise
        
        self.audio_queue: queue.Queue = queue.Queue()
        self.stream = sd.InputStream(
            samplerate = self.sample_rate,
            channels = config.CHANNELS,
            dtype = config.DTYPE,
            blocksize = config.BLOCK_SIZE,
            callback = self._audio_callback,
        )

    def _audio_callback(self, indata: np.ndarray, frames: int, time: dict, status: sd.CallbackFlags) -> None:
        #callback executed for each audio buffer
        if status:
            logger.warning(f"Audio stream status flag set: {status}")
        #queue the audio buffer to be processed by the whisper model
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

        # FIX 2: Looser regex — also catches common Whisper mishearings of "Nova"
        # e.g. "Nora", "over", "mover", "nover" etc.
        WAKE_PATTERN = re.compile(
            r'\b(nova|nover|nova\'s|novah|nora)\b',
            re.IGNORECASE
        )

        # FIX 1: Scan every 0.8 seconds (faster detection window)
        IDLE_WINDOW_CHUNKS = int(self.sample_rate * 0.8 / config.BLOCK_SIZE)
        # Overlap: keep last half of the buffer so "Nova" at window boundaries is never missed
        IDLE_OVERLAP_CHUNKS = IDLE_WINDOW_CHUNKS // 2

        logger.info("NOVA is online. Say 'Nova' to activate.")
        try:
            with self.stream:
                while self.stream.active:
                    chunk = self.audio_queue.get()

                    # 1. Idle state: Listen for "Nova" via Whisper
                    if not self.is_active:
                        # Accumulate audio into idle_buffer
                        idle_buffer.append(chunk)

                        if len(idle_buffer) >= IDLE_WINDOW_CHUNKS:
                            # Transcribe the short idle buffer using Whisper
                            idle_audio = np.concatenate(idle_buffer).flatten()

                            # FIX 1: Overlapping window — keep last half for next scan
                            # so "Nova" spoken at a boundary is never split and missed
                            idle_buffer = idle_buffer[IDLE_OVERLAP_CHUNKS:]

                            segments, _ = self.model.transcribe(
                                idle_audio,
                                beam_size=2,          # FIX 3: beam_size=2 is more accurate than 1
                                without_timestamps=True,
                                language='en',
                                vad_filter=True,
                            )
                            idle_text = " ".join([s.text.strip() for s in segments]).strip()

                            if idle_text:
                                logger.debug(f"Idle scan heard: '{idle_text}'")

                            # Check if user said "Nova" or "Hey Nova"
                            if WAKE_PATTERN.search(idle_text):
                                logger.info(f"Wake word 'Nova' detected in: '{idle_text}'")

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
                                # e.g. "Hey Nova open notepad" — strip wake phrase and execute directly
                                inline_command = WAKE_PATTERN.sub('', idle_text).strip(".!?, \t\n")
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
                    if not has_spoken and total_chunks > int(self.sample_rate * 4 / config.BLOCK_SIZE):
                        logger.info("No speech detected after wake word. Returning to sleep.")
                        audio_buffer.clear()
                        self.vad.reset()
                        self.is_active = False
                        if on_sleep_callback:
                            on_sleep_callback()
                        with self.audio_queue.mutex:
                            self.audio_queue.queue.clear()
                        continue

                    # Process command when speech finishes (silence detected) or max duration reached (7s)
                    max_chunks = int(self.sample_rate * 7 / config.BLOCK_SIZE)
                    if (has_spoken and silence_counter >= self.silence_duration_chunks) or total_chunks >= max_chunks:
                        logger.info("Processing speech command...")
                        full_audio = np.concatenate(audio_buffer).flatten()

                        # Normalize audio volume so Whisper receives clean, high-gain signal
                        max_peak = np.max(np.abs(full_audio))
                        if max_peak > 0.005:
                            full_audio = (full_audio / max_peak) * 0.9

                        segments, _ = self.model.transcribe(
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

                        text = " ".join([segment.text.strip() for segment in segments]).strip()

                        if text:
                            logger.info(f"Transcribed: '{text}'")
                            on_text_callback(text)
                        else:
                            logger.info("Could not recognize any words.")
                            if on_sleep_callback:
                                on_sleep_callback()

                        # Reset state and sleep
                        audio_buffer.clear()
                        self.vad.reset()
                        silence_counter = 0
                        has_spoken = False
                        self.is_active = False

                        # Clear audio queue to avoid stale audio
                        with self.audio_queue.mutex:
                            self.audio_queue.queue.clear()
                        logger.info("Waiting for wake word 'Nova'...")

        except Exception as e:
            logger.error(f"Error in streaming pipeline: {e}")
            raise