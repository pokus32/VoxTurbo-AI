"""macOS-specific clipboard and Cmd+V keystroke injection."""

import os
import sys
import time
import logging
import threading
import subprocess
import pyperclip
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QClipboard

from src.system.base import BaseInputInjector
from src.config import LAST_INPUT_FILE


class MacOSInputInjector(BaseInputInjector):
    """Input injector for macOS using Quartz / AppleScript / pbcopy."""

    def is_available(self) -> bool:
        return sys.platform == "darwin"

    def release_modifiers(self) -> None:
        """Release Cmd, Option, and Space keys on macOS."""
        try:
            from pynput import keyboard
            kb = keyboard.Controller()
            for k in [keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
                      keyboard.Key.alt, keyboard.Key.space]:
                kb.release(k)
        except Exception:
            pass

    def save_and_paste(self, text: str) -> None:
        """Save text to history, copy to macOS pasteboard, and simulate Cmd+V."""
        logging.info(f"[MacOSInput] Copying text to pasteboard: '{text}'")
        try:
            # Persist to last input file
            os.makedirs(os.path.dirname(LAST_INPUT_FILE), exist_ok=True)
            with open(LAST_INPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(text)

            # Copy via pyperclip
            pyperclip.copy(text)

            # Also ensure via pbcopy
            try:
                proc = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                proc.communicate(text.encode('utf-8'))
            except Exception:
                pass

            cb = QApplication.clipboard()
            if cb:
                cb.setText(text, QClipboard.Clipboard)

            threading.Thread(
                target=self._simulate_typing_worker,
                daemon=True,
                name="MacOSTypingWorker"
            ).start()
        except Exception as err:
            logging.error(f"[MacOSInput] Clipboard error: {err}", exc_info=True)

    def _simulate_typing_worker(self) -> None:
        """Release Cmd/Space and trigger Cmd+V via AppleScript or pynput."""
        time.sleep(0.15)
        self.release_modifiers()
        time.sleep(0.05)

        # 1. Primary method: AppleScript system events (native keystroke "v" using command down)
        try:
            script = 'tell application "System Events" to keystroke "v" using command down'
            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                timeout=1.0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logging.info("[MacOSInput] Cmd+V sent via osascript.")
            return
        except Exception as e:
            logging.warning(f"[MacOSInput] osascript failed ({e}), attempting pynput fallback...")

        # 2. Fallback via pynput
        try:
            from pynput import keyboard
            kb = keyboard.Controller()
            with kb.pressed(keyboard.Key.cmd):
                kb.press('v')
                kb.release('v')
            logging.info("[MacOSInput] Cmd+V sent via pynput fallback.")
        except Exception as e:
            logging.error(f"[MacOSInput] pynput fallback failed: {e}")
