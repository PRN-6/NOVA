# 🌌 NOVA Voice Assistant

NOVA is a high-performance, locally-hosted AI voice assistant built in Python. Designed for speed and privacy, it uses local neural networks to listen for a wake word, transcribe your speech, and execute system commands or query local AI models (via Ollama)—all without sending your voice data to the cloud.

---

## ✨ Features
- **Lightning Fast Transcription**: Powered by `faster-whisper` and NVIDIA CUDA acceleration for near-instant speech-to-text.
- **Local AI Brain**: Integrates with `Ollama` for complex query resolution and conversational AI.
- **Continuous Listening**: Runs silently in the background using a dedicated audio thread and `sounddevice`.
- **Smart Voice Activity Detection (VAD)**: Uses `SileroVAD` to perfectly detect when you start and stop speaking, ignoring background noise.
- **Extensible Plugin System**: Easily add new skills (e.g., Open Google Chrome, Send WhatsApp message, Control Volume).
- **Non-Intrusive UI**: Features a Windows System Tray integration (`pystray`) and a beautiful floating HUD overlay for visual feedback.

---

## 🛠️ How It Works

1. **The Wake Word**: The audio stream continuously buffers short chunks of audio. It uses a lightweight Whisper scan to detect the wake word (`"Nova"` or `"Hey Nova"`).
2. **Active Listening**: Once awakened, the Neural VAD tracks your voice. It records until you stop speaking.
3. **Transcription**: The recorded audio is normalized and sent to the Whisper AI model to be converted into text.
4. **Execution**: The text is passed to the `ActionExecutor`, which matches it against available plugins or routes it to the Ollama AI for complex reasoning.

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- An NVIDIA GPU (Highly recommended for CUDA acceleration, though CPU fallback is supported)
- [Ollama](https://ollama.ai/) installed locally (if you wish to use the AI chat features)

### 1. Clone & Environment Setup
Clone the repository and create a Python virtual environment:
```powershell
git clone https://github.com/yourusername/NOVA.git
cd NOVA
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
Install all required packages from the requirements file:
```powershell
pip install -r requirements.txt
```

*(Note: If you have an NVIDIA GPU, the requirements file automatically installs the necessary `nvidia-cublas-cu12` and `nvidia-cudnn-cu12` libraries for GPU acceleration).*

### 3. Run NOVA
To launch the assistant, simply run:
```powershell
python app.py
```
You will see the NOVA icon appear in your Windows System Tray. Say *"Nova"* to wake it up!

---

## 📂 Project Structure
- `app.py`: The main entry point that starts the background threads and UI.
- `config.py`: Central configuration for model sizes, thresholds, and device selection.
- `speech/streamer.py`: The core audio engine handling the microphone stream and Whisper transcription.
- `speech/vad.py`: The Voice Activity Detection logic.
- `actions/executor.py`: Routes transcribed text to the correct plugin or AI model.
- `plugins/`: Directory containing all the executable skills and integrations.
- `ui/`: Contains the System Tray and Floating HUD interfaces.

---
*Built with ❤️ for local AI enthusiasts.*