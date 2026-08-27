"""Wake Word detection powered by openWakeWord and ONNX."""

import os
import glob
import logging
from typing import List, Optional
import numpy as np

from src.config import WAKEWORDS_DIR

# Actual verified openWakeWord pre-trained model names
BUILTIN_MODELS = [
    "hey_jarvis",
    "alexa",
    "hey_mycroft",
    "hey_rhasspy",
    "timer",
    "weather"
]


class WakeWordDetector:
    """Lightweight real-time keyword spotting detector."""

    def __init__(
        self,
        model_name: str = "hey_jarvis",
        threshold: float = 0.6,
        custom_dir: str = WAKEWORDS_DIR
    ):
        self.model_name = model_name
        self.threshold = threshold
        self.custom_dir = custom_dir
        self.model = None
        self.is_ready = False
        os.makedirs(self.custom_dir, exist_ok=True)
        self._load_model()

    def get_available_models(self) -> List[str]:
        """Return list of built-in models and any custom .onnx files found in custom_dir."""
        models = list(BUILTIN_MODELS)
        if os.path.exists(self.custom_dir):
            custom_files = glob.glob(os.path.join(self.custom_dir, "*.onnx"))
            for cf in custom_files:
                base = os.path.splitext(os.path.basename(cf))[0]
                if base not in models:
                    models.append(base)
        return models

    def _load_model(self):
        """Initialize openWakeWord model instance."""
        try:
            import openwakeword
            from openwakeword.model import Model

            # Check if custom model file exists
            custom_path = os.path.join(self.custom_dir, f"{self.model_name}.onnx")
            if os.path.exists(custom_path):
                target = [custom_path]
                logging.info(f"[WakeWord] Loading custom model: {custom_path}")
            else:
                # If model_name is not in builtin, fallback to hey_jarvis
                if self.model_name not in BUILTIN_MODELS:
                    logging.warning(f"[WakeWord] Model '{self.model_name}' not found, falling back to 'hey_jarvis'")
                    self.model_name = "hey_jarvis"
                target = [self.model_name]
                logging.info(f"[WakeWord] Loading built-in model: {self.model_name}")

            self.model = Model(wakeword_models=target, inference_framework="onnx")
            self.is_ready = True
            logging.info(f"✅ [WakeWord] Detector successfully loaded for model '{self.model_name}'")
        except Exception as e:
            logging.error(f"[WakeWord] Failed to initialize openWakeWord: {e}")
            self.model = None
            self.is_ready = False

    def reload(self, model_name: str, threshold: float = 0.6):
        """Reload detector with a new model and threshold."""
        self.model_name = model_name
        self.threshold = threshold
        self._load_model()

    def process_frame(self, pcm_bytes: bytes) -> bool:
        """Feed 16-bit PCM audio chunk and evaluate wake word prediction.
        
        openWakeWord expects 16-bit 16kHz PCM samples (usually 1280 samples per step).
        """
        if not self.is_ready or not self.model:
            return False

        try:
            audio_data = np.frombuffer(pcm_bytes, dtype=np.int16)
            prediction = self.model.predict(audio_data)

            for key, score in prediction.items():
                if score >= self.threshold:
                    logging.info(f"🎯 [WakeWord] TRIGGERED! Model '{key}' score: {score:.3f} >= {self.threshold}")
                    # Reset internal state to avoid immediate re-triggering
                    self.model.reset()
                    return True
        except Exception as e:
            logging.warning(f"[WakeWord] Prediction error: {e}")
        return False
