"""
    configuration settings for the NOVA Assistant
"""

#Audio Stream Settings
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000
CHANNELS = 1
DTYPE = "float32"

#silence/VAD detection
SILENCE_THRESHOLD = 0.05
SILENCE_DURATION_CHUNKS = 5

#whisper model configeration
WHISPER_MODEL_SIZE = "small"
WHISPER_DEVICE ="cuda"
WHISPER_COMPUTE_TYPE = "float16"
INITIAL_PROMPT = "Nova, Chrome, WhatsApp, Outlook, Excel, VS Code, GitHub"

#Wake word configuration
WAKE_WORD_MODEL = "alexa"
WAKE_WORD_THRESHOLD = 0.75