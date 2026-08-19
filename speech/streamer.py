from speech.recorder import device
import logging
import config
from faster_whisper import WhisperModel
import queue
import sounddevice as sd
import numpy as np
from typing import Callable

logging.basicConfig(level=logging.INFO , format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("NOVA.SpeechStreamer")

class SpeachStreamer:
    def __init__(self) -> None:
        self.sample_rate = config.SAMPLE_RATE
        self.silence_threshold = config.SILENCE_THRESHOLD
        self.silence_duration_chunks = config.SILENCE_DURATION_CHUNKS

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
        if status:
            logger.warning(f"Audio stream status flag set: {status}")
        
        self.audio_queue.put(indata.copy())
    
    def start(self, on_text_collback: Callable[[str], bool])-> None:
