# 🗺️ VoxTurbo AI — Future Roadmap & Milestones

This document tracks planned architectural enhancements, upcoming features, and improvement milestones for **VoxTurbo AI**.

---

## ✅ Milestone 1: Intelligent Punctuation & Capitalization for GigaAM v2 [COMPLETED]
* **Status:** Implemented in `src/engine/punctuator.py` via resident Silero TE package (`v2_4lang_q.pt`).
* **Performance:** ~30–50ms neural inference latency in RAM.
* **Benefits:** 
  - Restores full stops, commas, question marks, and capitalization in real time.
  - Full support for `ru`, `en`, `de`, `es` with graceful fallback.
  - Toggleable via system tray menu (`🔤 Smart Punctuation (Silero TE)`).

---

## ✅ Milestone 2: Modern Floating Voice HUD / Waveform Overlay [COMPLETED]
* **Status:** Implemented in `src/ui/hud.py` via `VoiceHUDWidget` (PyQt5).
* **Features:**
  - Frameless, translucent glassmorphic overlay widget positioned at bottom-center of active screen.
  - Live 7-bar audio waveform / amplitude equalizer with smoothed physics and reactive color gradients.
  - Smooth fade-in (160ms) and fade-out (220ms) animations via `QPropertyAnimation`.
  - Multi-state indication: 🔴 Listening with elapsed timer, ⏳ Transcribing, ✅ Text Pasted confirmation.
  - Toggleable via system tray menu (`✨ Floating Voice HUD (Waveform)`).

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
