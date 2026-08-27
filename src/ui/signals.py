"""PyQt5 signal definitions for inter-thread communication."""

from PyQt5.QtCore import QObject, pyqtSignal


class SignalHelper(QObject):
    """Qt signal helper for thread-safe UI updates from worker threads."""

    toggle_signal = pyqtSignal()
    update_signal = pyqtSignal(str, bool)
    notify_signal = pyqtSignal(str, str)
    paste_signal = pyqtSignal(str)
    state_signal = pyqtSignal(str, str)
