"""Linux-specific clipboard and keystroke injection (X11 & Wayland)."""

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

from src.system.base import BaseInputInjector
from src.config import LAST_INPUT_FILE


class LinuxInputInjector(BaseInputInjector):
    """Input injector for Linux environments supporting X11 and Wayland."""

    def is_available(self) -> bool:
        return True

    def release_modifiers(self) -> None:
        """Release Super/Cmd, Alt and Space keys via pynput."""
        kb = keyboard.Controller()
        for k in [keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
                  keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
                  keyboard.Key.space]:
            try:
                kb.release(k)
            except Exception:
                pass

    def save_and_paste(self, text: str) -> None:
        """Save text to history, copy to system clipboard, and simulate Ctrl+V."""
        logging.info(f"[LinuxInput] Copying text to clipboard: '{text}'")
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
                target=self._simulate_typing_worker,
                daemon=True,
                name="LinuxTypingWorker"
            ).start()
        except Exception as err:
            logging.error(f"[LinuxInput] Clipboard error: {err}", exc_info=True)

    def _simulate_typing_worker(self) -> None:
        """Release modifiers and trigger Ctrl+V with fallbacks."""
        time.sleep(0.15)
        self.release_modifiers()
        time.sleep(0.05)

        kb = keyboard.Controller()

        # 1. Primary method: pynput
        try:
            logging.info("[LinuxInput] Emulating Ctrl+V via pynput...")
            with kb.pressed(keyboard.Key.ctrl):
                kb.press('v')
                kb.release('v')
            logging.info("[LinuxInput] Ctrl+V sent via pynput.")
            return
        except Exception as e:
            logging.warning(f"[LinuxInput] pynput keystroke failed ({e}), trying fallbacks...")

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
                logging.info("[LinuxInput] Ctrl+V sent via xdotool fallback.")
                return
            except Exception as e:
                logging.warning(f"[LinuxInput] xdotool fallback failed: {e}")

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
                logging.info("[LinuxInput] Ctrl+V sent via wtype fallback.")
                return
            except Exception as e:
                logging.warning(f"[LinuxInput] wtype fallback failed: {e}")
