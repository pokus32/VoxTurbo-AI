# 🎙️ VoxTurbo AI — User Guide

**VoxTurbo AI** is your smart desktop voice typing assistant. It instantly turns your spoken words into text and automatically types or pastes it into any open application (messengers, browsers, email clients, word processors, spreadsheets, and terminal).

All speech processing happens **100% locally on your computer**, keeping your data completely private without sending audio to the cloud.

---

## ⚡ 1. Two Ways to Dictate

You can use VoxTurbo in two convenient ways: using a keyboard shortcut or completely hands-free using your voice.

### Option A. Shortcut / Button Dictation (Classic)
1. Place your mouse cursor inside any text field (e.g., Telegram message box, Word document, or browser search bar).
2. Press **`Win + Space`** (`Super + Space`) or click the tray menu action.
   - *The visual HUD indicator will appear, and the system tray icon will turn red.*
3. Speak naturally into your microphone. You can take any pauses between sentences — recording will not auto-stop on silence.
4. Press **`Win + Space`** again (second press) to stop recording.
5. Your formatted text with smart punctuation and capital letters will be typed into the cursor position immediately.

---

### Option B. Hands-Free Voice Activation (Wake Word)
*Perfect when your hands are busy typing, coding, or holding a cup of coffee.*

1. Say the wake phrase clearly: **"Hey Jarvis"** (or another configured wake word like *Alexa*).
   - *The recording indicator activates automatically.*
2. Dictate your sentence or thought at your regular pace.
3. Once finished, **simply pause and stay quiet for about 1 second**.
4. The intelligent voice activity detector will detect the silence, stop recording, and type your text automatically.

---

## 🌐 2. Supported Languages & Auto-Detection

VoxTurbo AI supports several languages:
* 🇷🇺 **Russian (ru)** — Powered by the ultra-fast GigaAM engine (~0.5x real-time factor).
* 🇹🇷 **Turkish (tr / Türkçe)** — High accuracy including special characters (*ç, ğ, ı, ö, ş, ü*) and punctuation.
* 🇬🇧 **English (en)** — Deep semantic punctuation and vocabulary.
* 🇰🇿 **Kazakh (kk / Қазақша)**
* ⚡ **Auto-detect (Auto)** — The assistant automatically recognizes what language you are speaking and routes it to the optimal AI model.

---

## ⚙️ 3. System Tray Control (Near the Clock)

In the bottom right corner of your screen (system tray), you will see the circular VoxTurbo icon:
* 🟢 **Green:** Ready in RAM — waiting for your voice or shortcut.
* 🔴 **Red:** Currently recording audio.
* 🟡 **Yellow:** AI is processing speech and inserting text.

### Right-Click Menu:
Right-click the tray icon to quickly:
1. **🌟 Engine & Model:** Switch between GigaAM (ultra-fast Russian) and Whisper (multilingual).
2. **🌐 Language:** Change target language (Russian, Turkish, English, Kazakh, or Auto).
3. **🗣️ Wake Word:** Enable or disable hands-free voice activation (*Hey Jarvis, Alexa*, etc.).
4. **🔤 Smart Punctuation:** Toggle automatic comma, period, and question mark insertion.
5. **✨ Floating Voice HUD:** Toggle the animated floating volume waveform on your screen.
6. **⚙️ Settings...:** Open the full graphical preferences window.

---

## 🎛️ 4. Settings Window (Tab Overview)

To open settings, right-click the tray icon and select **"⚙️ Settings..."**.

### 🎙️ Audio Tab
* **Input Device:** Select your active microphone (built-in laptop mic, USB headset, or wireless earbuds).
* **Mic Test:** Click *“▶ Test Microphone”* and speak — the green bar displays your live voice volume.

### ⚡ Engine Tab
* **Active Model:** Choose between ultra-fast GigaAM v2 and high-accuracy Whisper Large-v3-Turbo.
* **Dictation Language:** Select your default language or Auto mode.
* **CPU Threads:** Allocate CPU threads (recommended: 4 or 6).
* **Smart Punctuation:** Automatically structure spoken words into grammatically correct sentences.

### 🗣️ Wake Word Tab (Hands-Free)
* **Enable Wake Word:** Check to keep background listening active.
* **Trigger Keyword:** Select your preferred wake word (*Hey Jarvis, Alexa, Hey Mycroft, Weather, Timer*).
* **Sensitivity (Threshold):** Adjust trigger sensitivity (lower = easier trigger, higher = stricter noise rejection).
* **Auto-Silence Duration:** How long to wait in silence before finishing dictation (default: 0.8 seconds). *Note:* Auto-silence only applies when triggered hands-free via Wake Word; shortcut/button recording always waits for a manual second press.
* **Beep on Trigger:** Play an audio feedback tone when the wake word is detected.
* **Custom Models:** Drop any custom trained `.onnx` models into `models/wakewords/`.

### ⌨️ Hotkeys Tab
* Customize your shortcut key:
  - `Super + Space` (`Win + Space`) — Default standard.
  - `Alt + Space`
  - `Ctrl + Shift + Space`
  - `F8` (Single key)

---

## 💡 5. Tips for Best Results

1. **Speak Naturally:** Continuous, natural speech provides better context for the neural network than robotic single-word pauses.
2. **Spoken Punctuation:** You can let the AI place punctuation automatically, or dictate explicitly by saying *"comma"*, *"period"*, *"question mark"*, or *"new line"*.
3. **Background Noise:** The built-in Silero VAD neural filter effectively isolates human speech from fan noise and room ambiance.

---

## ❓ Frequently Asked Questions (FAQ)

**Q: Where does the transcribed text get inserted?**  
**A:** Exactly where your cursor is currently blinking (the same as pressing `Ctrl + V`).

**Q: What if the text did not paste automatically?**  
**A:** The last transcribed text is always safely stored in your system clipboard (`Ctrl + V`) and can also be viewed in the tray menu under `💬 Last: ...`.

**Q: How do I completely exit the application?**  
**A:** Right-click the system tray icon and click **"❌ Quit VoxTurbo AI"**.
