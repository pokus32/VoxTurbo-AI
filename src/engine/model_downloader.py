"""Model downloader and integrity manager for VoxTurbo AI."""

import os
import time
import logging
import urllib.request
from typing import Callable, Optional
from PyQt5.QtCore import QThread, pyqtSignal

from src.config import (
    WHISPER_CPP_MODELS_DIR,
    WAKEWORDS_DIR,
)

# Registry of models and official download links
MODELS_CATALOG = {
    # Whisper models (whisper.cpp GGML format)
    "small": {
        "name": "Whisper Small (Многоязычная, быстрая)",
        "type": "whisper",
        "size_mb": 465,
        "filename": "ggml-small.bin",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
        "description": "Оптимальный баланс для повседневной работы (русский, английский, турецкий, казахский)."
    },
    "base": {
        "name": "Whisper Base (Ультралегкая)",
        "type": "whisper",
        "size_mb": 142,
        "filename": "ggml-base.bin",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
        "description": "Минимальное потребление памяти, молниеносный отклик на слабых ПК."
    },
    "large-v3-turbo-q5_0": {
        "name": "Whisper Large v3 Turbo (Q5_0 Квантованная)",
        "type": "whisper",
        "size_mb": 560,
        "filename": "ggml-large-v3-turbo-q5_0.bin",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin",
        "description": "Максимальное качество распознавания терминов и шумов при умеренном размере."
    },
    # VAD model
    "silero_vad": {
        "name": "Silero VAD v5 (Детектор активности голоса)",
        "type": "vad",
        "size_mb": 2,
        "filename": "ggml-silero-v5.1.2.bin",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-silero-v5.1.2.bin",
        "description": "Отсечение фонового шума и пауз в whisper.cpp."
    }
}


def is_model_installed(model_key: str) -> bool:
    """Check if model binary exists on disk with non-zero size."""
    if model_key not in MODELS_CATALOG:
        return False
    info = MODELS_CATALOG[model_key]
    path = os.path.join(WHISPER_CPP_MODELS_DIR, info["filename"])
    if os.path.exists(path) and os.path.getsize(path) > 1024 * 1024:
        return True
    return False


def get_installed_whisper_models() -> list:
    """Return list of keys of all installed whisper models."""
    installed = []
    for key, info in MODELS_CATALOG.items():
        if info["type"] == "whisper" and is_model_installed(key):
            installed.append(key)
    return installed


class ModelDownloadWorker(QThread):
    """Background download worker with progress signals."""

    progress_changed = pyqtSignal(int, float, float)  # percent, downloaded_mb, total_mb
    download_finished = pyqtSignal(str, bool, str)     # model_key, success, error_msg

    def __init__(self, model_key: str, parent=None):
        super().__init__(parent)
        self.model_key = model_key
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        if self.model_key not in MODELS_CATALOG:
            self.download_finished.emit(self.model_key, False, "Неизвестный идентификатор модели")
            return

        info = MODELS_CATALOG[self.model_key]
        os.makedirs(WHISPER_CPP_MODELS_DIR, exist_ok=True)
        dest_path = os.path.join(WHISPER_CPP_MODELS_DIR, info["filename"])
        temp_path = dest_path + ".download"

        url = info["url"]
        logging.info(f"[Downloader] Starting download: {url} -> {dest_path}")

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "VoxTurbo-AI/1.0 (Windows; x64)"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.info().get("Content-Length", 0))
                total_mb = total_size / (1024 * 1024) if total_size > 0 else info["size_mb"]

                downloaded = 0
                block_size = 1024 * 256  # 256 KB chunk
                last_emit = 0

                with open(temp_path, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            f.close()
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            self.download_finished.emit(self.model_key, False, "Загрузка отменена пользователем")
                            return

                        buffer = response.read(block_size)
                        if not buffer:
                            break

                        downloaded += len(buffer)
                        f.write(buffer)

                        downloaded_mb = downloaded / (1024 * 1024)
                        percent = int((downloaded / total_size) * 100) if total_size > 0 else 0

                        now = time.time()
                        if now - last_emit > 0.1 or downloaded == total_size:
                            self.progress_changed.emit(percent, downloaded_mb, total_mb)
                            last_emit = now

            # Atomically rename temp file to target
            if os.path.exists(dest_path):
                os.remove(dest_path)
            os.rename(temp_path, dest_path)

            logging.info(f"[Downloader] Successfully downloaded {self.model_key} to {dest_path}")
            self.download_finished.emit(self.model_key, True, "")

        except Exception as e:
            logging.error(f"[Downloader] Download failed for {self.model_key}: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            self.download_finished.emit(self.model_key, False, str(e))
