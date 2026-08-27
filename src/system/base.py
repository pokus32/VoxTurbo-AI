"""Abstract base interfaces for platform-specific input injection and hotkey handling."""

import abc
import logging


class BaseInputInjector(abc.ABC):
    """Abstract interface for system-level text injection and clipboard pasting."""

    @abc.abstractmethod
    def save_and_paste(self, text: str) -> None:
        """Copy text to system clipboard and trigger native Paste (Ctrl+V / Cmd+V)."""
        pass

    @abc.abstractmethod
    def release_modifiers(self) -> None:
        """Release any held modifier keys (Super, Cmd, Alt, Shift, Space)."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if this platform injector is available and operational."""
        pass
