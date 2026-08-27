"""Global hotkey listener using pynput."""

import logging
from typing import Callable
from pynput import keyboard


class HotkeyManager:
    """Manage global hotkey shortcuts (e.g. Super+Space / Win+Space)."""

    def __init__(self, on_hotkey_pressed: Callable[[], None], hotkey_combo: str = "<cmd>+<space>"):
        self.on_hotkey_pressed = on_hotkey_pressed
        self.hotkey_combo = hotkey_combo
        self._listener = None

    def start(self):
        """Start keyboard listener in a background thread."""
        def _handle_hotkey():
            logging.info(f"Hotkey pressed: {self.hotkey_combo}")
            if self.on_hotkey_pressed:
                self.on_hotkey_pressed()

        try:
            self._listener = keyboard.GlobalHotKeys({
                self.hotkey_combo: _handle_hotkey
            })
            self._listener.daemon = True
            self._listener.start()
            logging.info(f"Global hotkey listener for {self.hotkey_combo} started.")
        except Exception as e:
            logging.error(f"Failed to start hotkey listener: {e}", exc_info=True)

    def stop(self):
        """Stop keyboard listener."""
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
