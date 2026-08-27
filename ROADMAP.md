# 🗺️ VoxTurbo AI — Future Roadmap & Milestones

This document tracks planned architectural enhancements, upcoming features, and improvement milestones for **VoxTurbo AI**.

---

## 🎯 Milestone 1: Intelligent Punctuation & Capitalization for GigaAM v2
* **Background:** GigaAM v2 Conformer-CTC provides ultra-fast transcription (~0.2x–0.5x RTF), but outputs unpunctuated lowercase text.
* **Goal:** Integrate a lightweight neural post-processor (e.g. Silero Punctuation or compact ONNX-based model).
* **Benefits:** 
  - Restores full stops, commas, question marks, and capitalization.
  - Adds ~15–30ms latency while delivering Whisper-grade formatted text at GigaAM speed.

---

## 🎨 Milestone 2: Modern Floating Voice HUD / Waveform Overlay
* **Background:** Status indication currently relies on system tray icons and notifications.
* **Goal:** Implement an optional frameless, semi-transparent desktop overlay widget (PyQt5 / QPainter).
* **Features:**
  - Appears near the cursor or bottom-center screen during active recording.
  - Live audio waveform / volume amplitude visualization.
  - Smooth fade-in and fade-out animations.

---

## 🧠 Milestone 3: Local AI Voice Command & Polish Mode (Ollama Integration)
* **Background:** Dictation often contains raw conversational artifacts, repetitions, or unstructured thoughts.
* **Goal:** Secondary global hotkey (`Super + Shift + Space`) for AI-assisted dictation.
* **Features:**
  - Connects to local Ollama daemon (`localhost:11434`) running lightweight local LLMs (e.g., Qwen 2.5, Llama 3.2, Mistral).
  - Quick action modes:
    1. **Polish & Punctuate:** Clean up verbal pauses and grammar.
    2. **Summarize & Bulletize:** Transform brain dumps into structured markdown lists.
    3. **Translate to English:** Dictate in Russian/Kazakh $\rightarrow$ inject polished English text.

---

## 📥 Milestone 4: In-App Dynamic Model Downloader
* **Background:** Currently, optional GGML quantization variants (`Q8_0`, `small`, `base`) require manual download or bash script execution.
* **Goal:** Interactive background model fetching directly from the system tray menu.
* **Features:**
  - Non-blocking async downloader with download progress percentage in tray tooltip / notifications.
  - Integrity check (SHA256) after download before switching engines in RAM.

---

## ⚙️ Milestone 5: Custom Hotkeys & Audio Device Selector via GUI
* **Background:** Default shortcut `Super + Space` is hardcoded in configuration.
* **Goal:** Minimal preferences dialog for:
  - Custom global keybindings.
  - Explicit microphone input device selection (ALSA / PulseAudio / PipeWire device ID).
  - Configurable silence thresholds and max chunk lengths.
