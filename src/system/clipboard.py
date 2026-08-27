"""Clipboard management and automated Ctrl+V / Paste injection."""

import os
import time
import shutil
import logging
import threading
import subprocess
import pyperclip
from pynput import keyboard
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QClipboard
from src.config import LAST_INPUT_FILE


class PasteManager:
    """Manage copying transcribed text to system clipboard and triggering paste."""

    @staticmethod
    def save_and_paste(text: str):
        """Save text to history file, copy to clipboard, and simulate Ctrl+V."""
        logging.info(f"[PasteManager] Copying text to clipboard: '{text}'")
        try:
            # Persist to last input file
            os.makedirs(os.path.dirname(LAST_INPUT_FILE), exist_ok=True)
            with open(LAST_INPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(text)

            # Copy via pyperclip
            pyperclip.copy(text)

            # Copy via Qt Clipboard (supporting both Clipboard and Primary Selection)
            cb = QApplication.clipboard()
            if cb:
                cb.setText(text, QClipboard.Clipboard)
                cb.setText(text, QClipboard.Selection)

            threading.Thread(
                target=PasteManager._simulate_typing_worker,
                daemon=True,
                name="TypingWorker"
            ).start()
        except Exception as err:
            logging.error(f"[PasteManager] Clipboard error: {err}", exc_info=True)

    @staticmethod
    def _simulate_typing_worker():
        """Release modifier keys and simulate Ctrl+V keystroke with fallback."""
        time.sleep(0.15)
        kb = keyboard.Controller()

        # Release Super/Cmd and Space modifiers if still held
        for k in [keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r, keyboard.Key.space]:
            try:
                kb.release(k)
            except Exception:
                pass
        time.sleep(0.05)

        # 1. Primary injection method: pynput
        try:
            logging.info("[TypingWorker] Emulating Ctrl+V keystroke...")
            with kb.pressed(keyboard.Key.ctrl):
                kb.press('v')
                kb.release('v')
            logging.info("[TypingWorker] Ctrl+V sent via pynput.")
            return
        except Exception as e:
            logging.warning(f"[TypingWorker] pynput keystroke failed ({e}), attempting system fallbacks...")

        # 2. Fallback for X11: xdotool
        if shutil.which("xdotool"):
            try:
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
                    check=True,
                    timeout=1.0,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logging.info("[TypingWorker] Ctrl+V sent via xdotool fallback.")
                return
            except Exception as e:
                logging.warning(f"[TypingWorker] xdotool fallback failed: {e}")

        # 3. Fallback for Wayland: wtype
        if shutil.which("wtype"):
            try:
                subprocess.run(
                    ["wtype", "-M", "ctrl", "-k", "v", "-m", "ctrl"],
                    check=True,
                    timeout=1.0,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logging.info("[TypingWorker] Ctrl+V sent via wtype fallback.")
                return
            except Exception as e:
                logging.warning(f"[TypingWorker] wtype fallback failed: {e}")
