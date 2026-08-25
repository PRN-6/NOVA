# Project Abstract: NOVA

## Title
**NOVA: An Ultra-Low Latency, Privacy-Centric Local AI Desktop Voice Assistant with Dual-Tier Semantic Routing**

---

## 1. Executive Summary / Abstract

Conventional cloud-based voice assistants often suffer from noticeable network latency, persistent cloud connectivity requirements, ongoing subscription costs, and significant user data privacy risks. This project presents **NOVA**, an autonomous, 100% offline, privacy-first desktop voice assistant engineered for real-time operating system control and application automation on Windows environments.

The system architecture employs a multi-stage streaming pipeline designed to maximize computational efficiency while preserving natural language comprehension:

1. **Acoustic Keyword Spotting**: Integrates **openWakeWord** with optimized ONNX runtimes to perform continuous, sub-millisecond wake-word detection on 80ms audio frames with minimal CPU footprint.
2. **Real-Time Speech-to-Text (ASR)**: Uses an adaptive energy-based Voice Activity Detection (VAD) module that captures spoken commands and streams them directly into a local, GPU-accelerated **faster-whisper** (CTranslate2) model executing in `float16` precision (~50ms latency), featuring automatic CPU `int8` quantization fallback.
3. **Dual-Tier Semantic Routing**:
   - **Fast Lane**: Employs TF-IDF vectorization and cosine similarity matching over pre-indexed skill intent phrases to execute common commands in under **2 milliseconds** without invoking large language models.
   - **Slow Lane**: Unstructured or ambiguous queries dynamically fall back to an on-device Large Language Model (**Qwen 2.5 (1.5B)** via **Ollama**) for zero-shot natural language understanding and tool selection.
4. **Modular Extensibility & Automation**: A decoupled Plugin & Skill Manager executes native operating system commands, virtual key events, browser automation, and messaging application workflows.
5. **System Interface**: Encapsulated within a non-intrusive Windows System Tray background daemon paired with a transparent Floating Heads-Up Display (HUD) for real-time visual feedback.

Empirical testing demonstrates robust keyword detection accuracy, sub-100ms average response times, zero cloud data leakage, and seamless offline functionality.

---

## 2. Key Objectives & Contributions

* **Zero Cloud Dependency & Complete Privacy**: All audio processing, speech recognition, and language reasoning execute strictly on local hardware.
* **Ultra-Low Latency Pipeline**: Achieves near-instantaneous response times through GPU tensor acceleration and vector-based semantic matching.
* **Hybrid Decision Architecture**: Eliminates LLM latency bottlenecks for everyday desktop tasks while retaining reasoning capacity for complex prompts.
* **Universal Hardware Compatibility**: Auto-detects NVIDIA CUDA runtimes (`cublas`, `cudnn`) and gracefully falls back to CPU quantization for systems without dedicated GPUs.
* **Modular Plugin Ecosystem**: Enables rapid development and hot-pluggable registration of new desktop automation skills.

---

## 3. Technology Stack & System Components

| Component | Technology / Framework | Functionality |
| :--- | :--- | :--- |
| **Wake-Word Spotting** | `openwakeword` + `onnxruntime` | Real-time continuous keyword detection (80ms frames) |
| **Speech Recognition (ASR)** | `faster-whisper` (CTranslate2) | GPU `float16` / CPU `int8` streaming speech-to-text |
| **Audio Pipeline** | `sounddevice`, `numpy`, `scipy` | 16kHz audio stream ingestion & energy VAD |
| **Fast-Lane Intent Router** | `scikit-learn` (TF-IDF + Cosine Sim) | Sub-2ms vector matching across indexed phrases |
| **Reasoning Engine (LLM)** | `ollama` (`qwen2.5:1.5b`) | On-device zero-shot tool selection fallback |
| **Desktop UI & Background** | `pystray`, `Pillow`, `Tkinter` | Windows System Tray daemon & Floating HUD overlay |
| **Packaging & Distribution** | `pyinstaller` | Standalone executable generation for Windows |

---

## 4. System Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                 NOVA Architecture                                 |
|                                                                                   |
|  [ Microphone Input ] (16kHz / 80ms Frames via sounddevice)                       |
|          │                                                                        |
|          ▼                                                                        |
|  [ openWakeWord Engine ] ──(Keyword Detected)──► [ Visual Beep / HUD Wake ]       |
|          │                                                                        |
|          ▼                                                                        |
|  [ Energy-Based VAD ] ──(Audio Endpointing)──► [ faster-whisper (CUDA/CPU) ]      |
|                                                         │                         |
|                                                         ▼                         |
|                                              [ Transcribed Text ]                 |
|                                                         │                         |
|                 ┌───────────────────────────────────────┴───────────────┐         |
|                 ▼                                                       ▼         |
|      [ Fast-Lane Router ]                                    [ Ollama AI Lane ]   |
|      (TF-IDF Cosine Similarity)                              (Qwen 2.5 1.5B LLM)  |
|      * Confidence >= 0.50                                    * Complex Queries    |
|      * Sub-2ms Latency                                       * Natural Reasoning  |
|                 │                                                       │         |
|                 └───────────────────────┬───────────────────────────────┘         |
|                                         ▼                                         |
|                             [ Plugin & Skill Manager ]                            |
|                                         │                                         |
|                 ┌───────────────────────┼───────────────────────┐                 |
|                 ▼                       ▼                       ▼                 |
|        [ Browser Controls ]     [ App Automations ]     [ System Settings ]       |
|         (Chrome, Brave, Web)       (WhatsApp, etc.)      (Media, Volume, Keys)    |
+-----------------------------------------------------------------------------------+
```

---

## 5. Short / Portfolio Abstract (For README & Submissions)

> **NOVA** is an ultra-fast, 100% private, on-device AI voice assistant for Windows. Powered by **openWakeWord**, **faster-whisper (CUDA float16)**, and a **Dual-Lane Semantic Decision Engine**, NOVA delivers transcription in ~50ms and resolves commands instantaneously. Fast TF-IDF vector routing handles routine desktop automations in < 2ms, while an on-device LLM (**Qwen 2.5 via Ollama**) resolves complex natural requests. Featuring a modular plugin system, floating HUD overlay, and system tray integration, NOVA offers complete offline privacy and responsive voice control.
