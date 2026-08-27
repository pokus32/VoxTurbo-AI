"""Windows-specific clipboard and native SendInput injection (Win32 API)."""

import os
import sys
import time
import logging
import threading
import pyperclip
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QClipboard

from src.system.base import BaseInputInjector
from src.config import LAST_INPUT_FILE

# Win32 Virtual Key Codes
VK_CONTROL = 0x11
VK_MENU = 0x12     # Alt
VK_SPACE = 0x20
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_V = 0x56

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001


class WindowsInputInjector(BaseInputInjector):
    """Native Windows input injector using Win32 SendInput for zero-latency pasting."""

    def __init__(self):
        self._user32 = None
        if sys.platform == "win32":
            import ctypes
            self._user32 = ctypes.windll.user32

    def is_available(self) -> bool:
        return sys.platform == "win32" and self._user32 is not None

    def release_modifiers(self) -> None:
        """Release Win, Alt, Ctrl, and Space keys via Win32 keybd_event/SendInput."""
        if not self._user32:
            return
        for vk in [VK_LWIN, VK_RWIN, VK_MENU, VK_SPACE, VK_CONTROL]:
            try:
                self._user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
            except Exception:
                pass

    def save_and_paste(self, text: str) -> None:
        """Save text to history, copy to Windows clipboard, and trigger Ctrl+V."""
        logging.info(f"[WindowsInput] Copying text to clipboard: '{text}'")
        try:
            # Persist to last input file
            os.makedirs(os.path.dirname(LAST_INPUT_FILE), exist_ok=True)
            with open(LAST_INPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(text)

            # Copy via pyperclip / Qt Clipboard
            pyperclip.copy(text)
            cb = QApplication.clipboard()
            if cb:
                cb.setText(text, QClipboard.Clipboard)

            threading.Thread(
                target=self._simulate_typing_worker,
                daemon=True,
                name="WinTypingWorker"
            ).start()
        except Exception as err:
            logging.error(f"[WindowsInput] Clipboard error: {err}", exc_info=True)

    def _simulate_typing_worker(self) -> None:
        """Release Win/Space modifiers and send Ctrl+V via Win32 keybd_event."""
        time.sleep(0.12)
        self.release_modifiers()
        time.sleep(0.04)

        if self._user32:
            try:
                logging.info("[WindowsInput] Emulating Ctrl+V via Win32 user32.keybd_event...")
                # Press Ctrl
                self._user32.keybd_event(VK_CONTROL, 0, 0, 0)
                # Press V
                self._user32.keybd_event(VK_V, 0, 0, 0)
                time.sleep(0.02)
                # Release V
                self._user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
                # Release Ctrl
                self._user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
                logging.info("[WindowsInput] Ctrl+V sent successfully.")
                return
            except Exception as e:
                logging.warning(f"[WindowsInput] Win32 keybd_event failed: {e}")

        # Fallback via pynput if user32 not loaded
        try:
            from pynput import keyboard
            kb = keyboard.Controller()
            with kb.pressed(keyboard.Key.ctrl):
                kb.press('v')
                kb.release('v')
            logging.info("[WindowsInput] Ctrl+V sent via pynput fallback.")
        except Exception as e:
            logging.error(f"[WindowsInput] pynput fallback failed: {e}")
