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

from openwakeword.model import Model
import openwakeword.utils
import logging
import config
from faster_whisper import WhisperModel
import queue
import sounddevice as sd
import numpy as np
from typing import Callable

logging.basicConfig(level=logging.INFO , format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("NOVA.SpeechStreamer")

class SpeechStreamer:
    def __init__(self) -> None:
        self.sample_rate = config.SAMPLE_RATE
        self.silence_threshold = config.SILENCE_THRESHOLD
        self.silence_duration_chunks = config.SILENCE_DURATION_CHUNKS
        self.is_active = False

        # Automatically download pre-trained wake word models if not present
        openwakeword.utils.download_models()

        logger.info(f"Loading wake word model: {config.WAKE_WORD_MODEL}")
        self.oww_model = Model(wakeword_models=[config.WAKE_WORD_MODEL], inference_framework="onnx")

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
        silence_counter = 0
        has_spoken = False

        logger.info(f"NOVA is online. Say '{config.WAKE_WORD_MODEL}' to activate.")
        try:
            with self.stream:
                while self.stream.active:
                    chunk = self.audio_queue.get()

                    # 1. Idle state: Listen for wake word
                    if not self.is_active:
                        oww_chunk = (chunk.flatten() * 32767).astype(np.int16)
                        prediction = self.oww_model.predict(oww_chunk)

                        score = prediction.get(config.WAKE_WORD_MODEL, 0.0)
                        if score > config.WAKE_WORD_THRESHOLD:
                            logger.info(f"Wake word '{config.WAKE_WORD_MODEL}' detected! (Confidence: {score:.2f})")
                            
                            # Reset openWakeWord internal buffer so it does not loop
                            self.oww_model.reset()

                            if on_wake_word_callback:
                                on_wake_word_callback()

                            # Play an auditory beep asynchronously so it does not block the audio stream
                            try:
                                import winsound
                                threading.Thread(target=lambda: winsound.MessageBeep(winsound.MB_ICONASTERISK), daemon=True).start()
                            except Exception:
                                pass

                            self.is_active = True
                            has_spoken = False
                            silence_counter = 0
                            audio_buffer.clear()
                            audio_buffer.append(chunk)
                        continue

                    # 2. Active state: Record voice command
                    audio_buffer.append(chunk)
                    volume = float(np.sqrt(np.mean(chunk**2)))

                    if on_audio_energy_callback:
                        on_audio_energy_callback(volume)

                    # Detect speech energy
                    if volume < self.silence_threshold:
                        silence_counter += 1
                    else:
                        has_spoken = True
                        silence_counter = 0

                    # Check timeout if user never spoke after wake word
                    total_chunks = len(audio_buffer)
                    if not has_spoken and total_chunks > int(self.sample_rate * 4 / config.BLOCK_SIZE):
                        logger.info("No speech detected after wake word. Returning to sleep.")
                        audio_buffer.clear()
                        self.is_active = False
                        self.oww_model.reset()
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
                        silence_counter = 0
                        has_spoken = False
                        self.is_active = False
                        self.oww_model.reset()

                        # Clear audio queue to avoid stale audio
                        with self.audio_queue.mutex:
                            self.audio_queue.queue.clear()
                        logger.info(f"Waiting for wake word '{config.WAKE_WORD_MODEL}'...")

        except Exception as e:
            logger.error(f"Error in streaming pipeline: {e}")
            raise