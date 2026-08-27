# 🚀 VoxTurbo AI

> **High-performance, cross-platform voice typing assistant and speech recognition system for Linux desktops.**
> Powered by **GigaAM v2 Conformer-CTC** and **Whisper.cpp (Large-v3-Turbo)** resident in RAM.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux%20(X11%20%26%20Wayland)-green.svg)]()
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()
[![C++ Engine: whisper.cpp](https://img.shields.io/badge/C%2B%2B-whisper.cpp%20AVX2%2FFMA-orange.svg)]()

---

## ⚡ Key Highlights

1. **Dual State-of-the-Art Engines:**
   - **GigaAM v2 (Conformer-CTC):** SOTA Russian speech recognition running in **~0.5x Real-Time Factor (RTF)** directly in Python memory.
   - **Whisper Large-v3-Turbo (C++ daemon):** Compiled with **AVX2**, **FMA**, and **OpenMP** instructions for multi-language accuracy and deep semantic context, supporting Russian, Kazakh, English, and Turkish.

2. **Zero-Disk Streaming & Resident Memory:**
   - Preloads neural weights into RAM: **0.0s startup latency** per recording.
   - Full in-memory audio pipeline (PCM $\rightarrow$ RAM inference $\rightarrow$ Clipboard $\rightarrow$ Target App).

3. **Adaptive Context & Silence Chunking:**
   - **Full-Window Mode:** Accumulates up to 28 seconds of speech for Whisper Large, preserving rich context, punctuation, and capital letters.
   - **Streaming Mode:** Splits audio dynamically across pauses ($\ge 0.38$s) for fast response models.

4. **Hardware Voice Activity Detection (Silero VAD v5.1):**
   - Cuts background silence before passing audio to heavy transformer decoders.

5. **In-Flight Language Detection & Fallback Routing:**
   - Detects spoken language on the fly (Russian, Turkish 🇹🇷, Kazakh 🇰🇿, English 🇬🇧).
   - Intelligently routes Russian to GigaAM (~0.5x RTF) and foreign languages to Whisper Large-v3-Turbo resident daemon.

6. **Hands-Free Voice Wake Word (openWakeWord ONNX):**
   - Optional keyword activation (*Hey Jarvis*, *Alexa*, *Okay Google*, *Hey Siri*) with CPU load < 1%.
   - Auto-finish hands-free speech dictation on voice pauses ($\ge 0.8$s).
   - Custom `.onnx` models directory for any arbitrary user keywords.

7. **Seamless Desktop Integration:**
   - **Global Hotkey:** `Super + Space` (`Win + Space`) toggles recording (press to start, press again to finish; allows arbitrary pauses).
   - **Auto-Paste:** Immediately types or injects recognized text into the active cursor position (X11 & Wayland).
   - **System Tray & Settings:** Rich menu and full-featured preferences dialog with audio VU-meter.

---

## 📦 Quick Installation

### Prerequisites (Ubuntu / Debian / Mint / Pop!_OS)
```bash
sudo apt update
sudo apt install -y build-essential cmake portaudio19-dev libopenblas-dev xdotool python3-venv git
```

### Installation
```bash
git clone https://github.com/your-username/voxturbo.git
cd voxturbo
chmod +x install.sh
./install.sh
```

The installer will:
- Create an isolated Python virtual environment (`.venv`).
- Compile `whisper.cpp` server with hardware CPU optimizations (`-DGGML_AVX2=ON -DGGML_FMA=ON`).
- Download Silero VAD and Whisper Large-v3-Turbo models automatically.
- Register desktop menu entries and the `voxturbo` CLI executable.

---

## 📖 User Guides (Руководства пользователя)

Choose your language for the step-by-step user manual:
* 🇷🇺 **[Русский — Руководство пользователя](file:///home/user/dev/antigravity-voice-turbo/USER_GUIDE.md)**
* 🇬🇧 **[English — User Guide](file:///home/user/dev/antigravity-voice-turbo/USER_GUIDE_EN.md)**
* 🇹🇷 **[Türkçe — Kullanıcı Kılavuzu](file:///home/user/dev/antigravity-voice-turbo/USER_GUIDE_TR.md)**
* 🇰🇿 **[Қазақша — Пайдаланушы нұсқаулығы](file:///home/user/dev/antigravity-voice-turbo/USER_GUIDE_KK.md)**

---

## 🎮 Usage

* **Desktop Application Menu:** Open **Sound & Video $\rightarrow$ VoxTurbo AI**
* **Terminal:**
  ```bash
  voxturbo &
  ```

### How to Dictate:
1. Press `Win + Space` (`Super + Space`) anywhere in your system.
2. Speak your thought into your microphone.
3. Press `Win + Space` again to stop.
4. The transcribed text will be automatically pasted into your active input field (terminal, IDE, browser, messenger).

---

## ⚙️ Configuration & Paths

Standard XDG file locations:
* **Configuration:** `~/.config/voxturbo/config.json`
* **Log File:** `~/.local/state/voxturbo/voxturbo.log`
* **Last Transcribed Text:** `~/.local/state/voxturbo/last_voice_input.txt`

### Example `config.json`:
```json
{
  "engine": "gigaam",
  "model_quant": "gigaam_v2",
  "threads": 4,
  "language": "auto",
  "flash_attn": true
}
```

---

## 🏗️ Architecture Overview

```
[ Microphone (PyAudio) ]
           │
     [ Silero VAD ] ──► (In-Flight Language Detector: Whisper Tiny)
           │
   [ Adaptive Chunking ]
    ├──► Mode: 'stream'      ──► [ GigaAM v2 Conformer-CTC (RAM) ]
    └──► Mode: 'full_window' ──► [ Whisper.cpp Large-v3-Turbo (HTTP Daemon) ]
                                            │
                                  [ Transcribed Text ]
                                            │
                    [ System Clipboard + Synthetic Keystroke / Paste ]
                                            │
                               [ Active Window / Cursor ]
```

---

## 📄 License
This project is licensed under the MIT License.
