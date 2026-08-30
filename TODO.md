# 📋 NOVA Feature Roadmap & TO-DO List

This document outlines the planned improvements, bug fixes, new plugins, and architectural upgrades for the **NOVA Assistant** project.

---

## 🔴 1. Immediate Fixes & High Priority

- [ ] **Fix WhatsApp Launch Mechanism (`whatsapp_plugin.py`)**
  - Current `start whatsapp:` fails if protocol handler isn't registered.
  - Add fallback sequence: Protocol URI (`whatsapp:`) $\rightarrow$ App Execution Alias (`WhatsApp.exe`) $\rightarrow$ Windows Store package lookup $\rightarrow$ WhatsApp Web in browser.
- [ ] **Text-To-Speech (TTS) Voice Responses**
  - Add offline, low-latency TTS (e.g., `pyttsx3`, `edge-tts`, or `piper-tts`) so NOVA can speak back to confirm actions (e.g., *"Opening Chrome"*, *"Volume set to 50%"*).
- [ ] **Wake-Word Sensitivity & Noise Calibration**
  - Add an automatic ambient noise calibration step on startup to dynamically adjust `SILENCE_THRESHOLD`.

---

## 🧩 2. New Plugins & Automation Skills

### 🎵 Media & Entertainment
- [ ] **Spotify Plugin (`spotify_plugin.py`)**
  - Commands: *"Play/Pause"*, *"Next track"*, *"Previous track"*, *"Play [song name]"*.
  - Use Windows Media keys or Spotify Local/Web API.
- [ ] **YouTube Direct Search Plugin**
  - Commands: *"Search YouTube for [topic]"*, *"Play lo-fi music on YouTube"*.
  - Auto-open direct search URL and focus video player.

### 💻 System Controls & Utilities
- [ ] **Volume & Brightness Controller**
  - Commands: *"Set volume to 80%"*, *"Mute audio"*, *"Increase brightness"*.
  - Use `pycaw` (Python Core Audio Windows) and `screen-brightness-control`.
- [ ] **Screenshot & Screen Recording Utility**
  - Commands: *"Take a screenshot"*, *"Capture active window"*.
  - Save directly to `%USERPROFILE%/Pictures/Screenshots` and copy to clipboard.
- [ ] **System Health & Battery Stats**
  - Commands: *"Check battery percentage"*, *"How is CPU usage?"*, *"Check available RAM"*.
  - Use `psutil` to query battery and hardware stats.
- [ ] **Windows Window Management**
  - Commands: *"Minimize all windows"*, *"Snap window to left/right"*, *"Switch to next desktop"*, *"Lock computer"*.

### 📝 Productivity & Office
- [ ] **Notepad / Quick Notes Plugin (`notepad_plugin.py`)**
  - Integrate user-created Notepad plugin into main release with note-taking support: *"Take note: meeting at 3 PM"*.
- [ ] **Clipboard Manager**
  - Commands: *"Read clipboard"*, *"Clear clipboard"*, *"Save clipboard to notes"*.
- [ ] **Smart Calculator & Unit Converter**
  - Commands: *"What is 15% of 450?"*, *"Convert 50 USD to INR"*, *"What is 100 kilometers in miles?"*.

---

## 🖐️ 3. Multimodal Computer Vision (Hand Gesture Engine)

- [ ] **Real-Time Hand Landmark Tracking (`gesture_service.py`)**
  - Integrate **Google MediaPipe Hands** + **OpenCV** running on CPU (30–60 FPS) with negligible compute overhead.
  - Add optional toggle via voice (*"Nova, enable/disable gesture mode"*) or hotkey to conserve resources when camera is unneeded.
- [ ] **Air Gesture Controls:**
  - ✋ **Open Palm $\rightarrow$ ✊ Fist:** Play / Pause active media.
  - 🤏 **Thumb-Index Pinch & Move:** Continuous smooth system volume adjustment.
  - 👈 / 👉 **Horizontal Air Swipe:** Switch active browser tabs or virtual desktops.
  - ✌️ **Two Fingers Point Up/Down:** Smooth document / webpage scrolling.
  - 🤫 **Index Finger to Lips:** Instant audio mute / put NOVA to sleep.
- [ ] **HUD Gesture Feedback Overlay:**
  - Display subtle hand tracking skeleton or visual icon on the floating HUD when camera mode is engaged.

---

## 🧠 4. AI & Natural Language Processing (NLP)

- [ ] **Conversation Context & Multi-turn Memory**
  - Remember previous context (e.g., User: *"Search for Paris"*, then: *"What is the weather there?"*).
- [ ] **Live Streaming LLM Responses in HUD**
  - Stream tokens from local Ollama LLM directly onto the floating HUD canvas in real time instead of waiting for full response.
- [ ] **Custom System Prompt Profiles**
  - Allow users to choose AI personality / speed mode (e.g., *Fast Desktop Assistant* vs. *In-depth Conversational Assistant*).

---

## 🎨 5. UI / UX & Audio Presentation

- [ ] **Floating HUD Polish & Customization**
  - Add customizable themes (Cyberpunk Neon, Glassmorphism Dark, Minimalist Light).
  - Add adjustable HUD positioning (Top-Center, Bottom-Right, Draggable).
- [ ] **Sound Effects Pack**
  - High-tech audio chimes for: Wake-up, Command Recognized, Action Completed, and Error.
- [ ] **Visualizer Waveform Improvements**
  - Smooth 60 FPS sine-wave or frequency bar visualizer during active listening.

---

## 📦 6. Deployment, Packaging & Distribution

- [ ] **Start with Windows (Auto-Start)**
  - Add optional toggle in System Tray to launch NOVA automatically on Windows boot.
- [ ] **Standalone One-Click Installer**
  - Build signed `.exe` installer using `PyInstaller` and `Inno Setup` bundling CUDA DLLs and default models.
- [ ] **Automatic Dependency & Model Downloader**
  - On first run, check if Ollama is running and automatically pull `qwen2.5:0.5b` if missing.

---

## 📅 Roadmap Milestones

| Milestone | Target | Description |
| :--- | :--- | :--- |
| **v1.1** | *Core Polish* | Fix WhatsApp launcher, add pyttsx3 voice feedback, tune VAD. |
| **v1.2** | *Media & System* | Spotify plugin, Volume/Brightness controls, Screenshot tool. |
| **v1.3** | *Vision Multimodal* | MediaPipe hand gestures (Air swipe, Pinch volume, Play/Pause). |
| **v1.4** | *Intelligence* | Multi-turn conversation memory, streaming HUD text. |
| **v2.0** | *Production Release* | Complete Inno Setup installer with Auto-start and settings GUI. |
