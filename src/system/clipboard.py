"""Cross-platform clipboard management and keystroke injection."""

import logging
from src.system.input_backend import get_platform_injector

_active_injector = None


def _get_injector():
    global _active_injector
    if _active_injector is None:
        _active_injector = get_platform_injector()
    return _active_injector


class PasteManager:
    """Manage copying transcribed text to system clipboard and triggering native paste."""

    @staticmethod
    def save_and_paste(text: str):
        """Save text to history file, copy to clipboard, and simulate Ctrl+V / Cmd+V."""
        injector = _get_injector()
        injector.save_and_paste(text)
