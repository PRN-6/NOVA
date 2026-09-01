import logging
import numpy as np
from faster_whisper.vad import get_vad_model

logger = logging.getLogger("NOVA.SileroVAD")

class SileroVAD:
    """
    Lightweight streaming Voice Activity Detector powered by Silero VAD (ONNX).
    Processes continuous 16kHz float32 audio chunks in 512-sample frames (~32ms)
    and predicts human speech probability.
    """
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.frame_size = 512  # 32ms at 16kHz
        self.residual = np.zeros(0, dtype=np.float32)
        try:
            self.model = get_vad_model()
            logger.info("Silero VAD (ONNX) initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            raise

    def reset(self) -> None:
        """Clears any cached audio frames between listening sessions."""
        self.residual = np.zeros(0, dtype=np.float32)

    def get_speech_probability(self, chunk: np.ndarray) -> float:
        """
        Computes the maximum speech probability across all 512-sample frames in the chunk.
        """
        audio = chunk.flatten().astype(np.float32)
        if len(self.residual) > 0:
            audio = np.concatenate((self.residual, audio))

        num_frames = len(audio) // self.frame_size
        if num_frames == 0:
            self.residual = audio
            return 0.0

        process_len = num_frames * self.frame_size
        to_process = audio[:process_len]
        self.residual = audio[process_len:]

        try:
            probs = self.model(to_process, num_samples=self.frame_size)
            if len(probs) == 0:
                return 0.0
            return float(np.max(probs))
        except Exception as e:
            logger.debug(f"Error during VAD inference: {e}")
            return 0.0

    def is_speech(self, chunk: np.ndarray) -> bool:
        """
        Returns True if human speech probability meets or exceeds threshold.
        """
        prob = self.get_speech_probability(chunk)
        return prob >= self.threshold
