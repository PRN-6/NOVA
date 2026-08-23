from openwakeword.model import Model
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

        logger.info(f"Loading wake word model: {config.WAKE_WORD_MODEL}")
        self.oww_model = Model(wakeword_models=[config.WAKE_WORD_MODEL],inference_framework="onnx")

        logger.info(f"Loading whisper model {config.WHISPER_MODEL_SIZE} on {config.WHISPER_DEVICE}")

        try:
            self.model = WhisperModel(
                config.WHISPER_MODEL_SIZE,
                device=config.WHISPER_DEVICE,
                compute_type=config.WHISPER_COMPUTE_TYPE
            )
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
    
    def start(self, on_text_collback: Callable[[str], bool])-> None:

        audio_buffer = []
        silence_counter = 0

        logger.info("NOVA is actively listening. speak now")
        try:
            with self.stream:
                logger.info("Nova is actively listening. Speak now.")
                while self.stream.active:
                    chunk = self.audio_queue.get()

                    if not self.is_active:
                        oww_chunk = (chunk.flatten() * 32767).astype(np.int16)

                        prediction = self.oww_model.predict(oww_chunk)

                        if prediction[config.WAKE_WORD_MODEL] > config.WAKE_WORD_THRESHOLD:
                            logger.info(f"wake word '{config.WAKE_WORD_MODEL}'dected! waking")
                            
                            # Play an auditory beep so the user knows it's listening
                            import winsound
                            winsound.MessageBeep(winsound.MB_ICONASTERISK)

                            self.is_active = True
                        continue

                    #compute root mean square for energy threshold detection
                    volume = np.sqrt(np.mean(chunk**2))

                    #silence threshold fi the value of the volume is greater than the silence_threshold
                    if volume < self.silence_threshold:
                        silence_counter += 1
                    else:
                        silence_counter = 0
                    
                    if silence_counter >= self.silence_duration_chunks:
                        if len(audio_buffer) > 0:
                            audio_buffer.clear()
                            logger.debug("VAD threshold met: clearing audio buffer")
                            continue

                    audio_buffer.append(chunk)
                    full_audio = np.concatenate(audio_buffer).flatten()

                    #prevent buffer overflow
                    if len(full_audio) > self.sample_rate * 10:
                        audio_buffer = audio_buffer[-20:]
                        full_audio = np.concatenate(audio_buffer).flatten()

                    #transcribe current audio buffer
                    segments, _ = self.model.transcribe(
                        full_audio,
                        beam_size = 3,
                        language='en',
                        vad_filter = True,
                        initial_prompt = config.INITIAL_PROMPT
                    )

                    text = " ".join([segment.text.strip() for segment in segments]).strip()

                    if text:
                        command_executed = on_text_collback(text)

                        audio_buffer.clear()
                        silence_counter = 0

                        logger.info("command finished going back to sleep")
                        
                        # Clear the background audio queue to prevent instant false-wakeups from old audio
                        with self.audio_queue.mutex:
                            self.audio_queue.queue.clear()
                            
                        self.is_active = False

        except Exception as e:
            logger.error(f"Error in streaming pipeline: {e}")
            raise