"""
    configuration settings for the NOVA Assistant
"""

#Audio Stream Settings
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000
CHANNELS = 1
DTYPE = "float32"

#silence/VAD detection
SILENCE_THRESHOLD = 0.1
SILENCE_DURATION_CHUNKS = 3

#whisper model configeration
WHISPER_MODEL_SIZE = "small"
WHISPER_DEVICE ="cpu"
WHISPER_COMPUTE_TYPE = "int8"
INITIAL_PROMPT = "Nova, Chrome, WhatsApp, Outlook, Excel, VS Code, GitHub"