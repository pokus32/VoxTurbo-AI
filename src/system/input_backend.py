"""Platform factory and lazy resolution of the active system input injector."""

import sys
import logging
from src.system.base import BaseInputInjector


def get_platform_injector() -> BaseInputInjector:
    """Instantiate and return the appropriate input injector for the current OS."""
    if sys.platform == "win32":
        try:
            from src.system.windows_input import WindowsInputInjector
            logging.info("[InputBackend] Selected WindowsInputInjector (Win32 SendInput).")
            return WindowsInputInjector()
        except Exception as e:
            logging.warning(f"[InputBackend] Could not load WindowsInputInjector: {e}")

    elif sys.platform == "darwin":
        try:
            from src.system.macos_input import MacOSInputInjector
            logging.info("[InputBackend] Selected MacOSInputInjector (CoreGraphics/AppleScript).")
            return MacOSInputInjector()
        except Exception as e:
            logging.warning(f"[InputBackend] Could not load MacOSInputInjector: {e}")

    # Default to Linux (X11 / Wayland)
    from src.system.linux_input import LinuxInputInjector
    logging.info("[InputBackend] Selected LinuxInputInjector (X11/Wayland).")
    return LinuxInputInjector()
