"""Fast in-flight language identification."""

import time
import logging
import numpy as np
from faster_whisper import WhisperModel


class LanguageDetector:
    """Detect spoken language on the fly using a lightweight model."""

    def __init__(self, model_size: str = "tiny", cpu_threads: int = 2):
        self.model_size = model_size
        self.cpu_threads = cpu_threads
        self._model = None

    def preload(self):
        """Preload the detector model into RAM."""
        if not self._model:
            logging.info("[LanguageDetector] Preloading language detector (tiny)...")
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
                cpu_threads=self.cpu_threads
            )
            logging.info("✅ Language detector is ready.")

    def detect(self, frames_snapshot: list) -> str:
        """Detect spoken language from a short audio buffer snapshot."""
        if not frames_snapshot:
            return "ru"

        try:
            raw_bytes = b"".join(frames_snapshot)
            audio_np = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            if not self._model:
                self.preload()

            t0 = time.time()
            segments, info = self._model.transcribe(audio_np, beam_size=1, without_timestamps=True)
            for _ in segments:
                break

            if info.language_probability >= 0.75:
                detected_lang = info.language
            else:
                detected_lang = "ru"

            logging.info(
                f"[LanguageDetector] Language detected: '{detected_lang}' "
                f"(raw={info.language}, prob={info.language_probability:.2f}) in {time.time()-t0:.2f}s"
            )
            return detected_lang
        except Exception as e:
            logging.warning(f"[LanguageDetector] Language detection error: {e}")
            return "ru"
