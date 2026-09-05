"""
    configuration settings for the NOVA Assistant
"""

import ctypes
import subprocess

def _cuda_available() -> bool:
    """Check if an NVIDIA CUDA-capable GPU is accessible at runtime."""
    try:
        ctypes.WinDLL("nvcuda.dll")
        return True
    except OSError:
        return False

_HAS_CUDA = _cuda_available()

# Audio Stream Settings (16kHz, 1280 samples = 80ms frames required by openWakeWord)
SAMPLE_RATE = 16000
BLOCK_SIZE = 1280
CHANNELS = 1
DTYPE = "float32"

# Silence / Voice Activity Detection (VAD)
VAD_THRESHOLD = 0.50             # Silero neural VAD speech probability threshold (0.0 to 1.0)
SILENCE_DURATION_CHUNKS = 8      # 8 chunks * 80ms = ~0.64s pause after speech for rapid cut-off
SILENCE_THRESHOLD = 0.008        # Fallback RMS noise floor

# Whisper model configuration (small.en: 3x accuracy of base.en, ~80ms on CUDA)
WHISPER_MODEL_SIZE = "small.en"
WHISPER_DEVICE      = "cuda"  if _HAS_CUDA else "cpu"   # auto-detected
WHISPER_COMPUTE_TYPE = "float16" if _HAS_CUDA else "int8"  # float16=GPU, int8=CPU fallback
WHISPER_BEAM_SIZE = 5
WHISPER_HOTWORDS = "Brave, Chrome, WhatsApp, YouTube, tab, close, open, search, volume, enter, screenshot, lock"
INITIAL_PROMPT = "Commands for Nova assistant to open apps like Brave, Chrome, WhatsApp, and search the web, Google, or YouTube."

# Wake word configuration
WAKE_WORD_MODEL = "nova"
WAKE_WORD_THRESHOLD = 0.50

# Audio feedback sounds (True = beep on wake, False = silent)
ENABLE_BEEP = False
