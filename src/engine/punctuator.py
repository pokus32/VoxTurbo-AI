"""Intelligent Neural Punctuation and Capitalization using Silero TE."""

import os
import time
import logging
import threading
import torch
from torch import package

SILERO_TE_URL = "https://models.silero.ai/te_models/v2_4lang_q.pt"
FALLBACK_CACHE_PATH = "/home/user/.cache/torch/hub/snakers4_silero-models_master/src/silero/model/v2_4lang_q.pt"


class SileroPunctuator:
    """Resident neural punctuation and capitalization model in RAM."""

    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.cache/voxturbo/models")
        self.cache_dir = cache_dir
        self.model_path = os.path.join(self.cache_dir, "v2_4lang_q.pt")
        self._model = None
        self._is_ready = False
        self._lock = threading.Lock()
        self.supported_languages = {"ru", "en", "de", "es"}

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def _resolve_model_file(self) -> str:
        """Ensure model file exists locally, checking caches or downloading."""
        if os.path.isfile(self.model_path) and os.path.getsize(self.model_path) > 1000000:
            return self.model_path

        # Check existing PyTorch hub fallback
        if os.path.isfile(FALLBACK_CACHE_PATH) and os.path.getsize(FALLBACK_CACHE_PATH) > 1000000:
            os.makedirs(self.cache_dir, exist_ok=True)
            import shutil
            try:
                shutil.copy2(FALLBACK_CACHE_PATH, self.model_path)
                logging.info(f"[Punctuator] Copied model from cache: {self.model_path}")
                return self.model_path
            except Exception as e:
                logging.warning(f"[Punctuator] Failed to copy fallback cache: {e}")
                return FALLBACK_CACHE_PATH

        # Download model if not available
        os.makedirs(self.cache_dir, exist_ok=True)
        logging.info(f"[Punctuator] Downloading Silero TE model from {SILERO_TE_URL}...")
        torch.hub.download_url_to_file(SILERO_TE_URL, self.model_path, progress=True)
        return self.model_path

    def preload(self):
        """Load Silero TE package into memory."""
        if self._model is not None:
            return

        with self._lock:
            if self._model is not None:
                return
            t0 = time.time()
            try:
                model_file = self._resolve_model_file()
                logging.info(f"[Punctuator] Loading Silero TE model from {model_file}...")
                importer = package.PackageImporter(model_file)
                self._model = importer.load_pickle("te_model", "model")
                self._is_ready = True
                logging.info(f"✅ Silero Punctuator loaded in {time.time()-t0:.2f}s")
            except Exception as e:
                logging.error(f"[Punctuator] Failed to load Silero TE model: {e}", exc_info=True)
                self._is_ready = False

    def punctuate(self, text: str, lang: str = "ru") -> str:
        """Enhance input text with neural punctuation and capitalization."""
        if not text or not text.strip():
            return ""

        cleaned = text.strip()

        # If language is not in supported set, perform basic title casing
        if lang not in self.supported_languages:
            return cleaned[0].upper() + cleaned[1:] if cleaned else ""

        if self._model is None:
            self.preload()

        if self._model is None:
            return cleaned[0].upper() + cleaned[1:]

        with self._lock:
            try:
                t0 = time.time()
                enhanced = self._model.enhance_text(cleaned, lan=lang)
                enhanced = enhanced.strip()
                dt_ms = (time.time() - t0) * 1000
                logging.info(f"[Punctuator] '{cleaned}' → '{enhanced}' in {dt_ms:.1f}ms (lang={lang})")
                return enhanced
            except Exception as e:
                logging.error(f"[Punctuator] Enhancement failed: {e}")
                return cleaned[0].upper() + cleaned[1:]
