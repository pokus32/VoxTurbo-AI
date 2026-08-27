"""Speech recognition engine for GigaAM (SaluteSpeech) based on Conformer-CTC."""

import time
import logging
import numpy as np
import torch

# Patch for torch.load compatibility with recent PyTorch versions
_orig_torch_load = torch.load


def _patched_torch_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _orig_torch_load(*args, **kwargs)


torch.load = _patched_torch_load


from src.engine.punctuator import SileroPunctuator


class GigaAMEngine:
    """Local resident GigaAM v2 CTC engine with neural punctuation in RAM."""

    def __init__(
        self,
        model_name: str = "v2_ctc",
        cpu_threads: int = 4,
        enable_punctuation: bool = True
    ):
        self.model_name = model_name
        self.cpu_threads = cpu_threads
        self.enable_punctuation = enable_punctuation
        self._model = None
        self._is_ready = False
        self.punctuator = SileroPunctuator()

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def preload(self):
        """Preload GigaAM model weights and Silero punctuator into RAM."""
        if self._model is None:
            logging.info(f"[GigaAMEngine] Loading GigaAM model ({self.model_name}) into RAM...")
            t0 = time.time()
            try:
                import gigaam

                torch.set_num_threads(self.cpu_threads)
                self._model = gigaam.load_model(self.model_name)
                self._is_ready = True
                logging.info(f"✅ GigaAM ({self.model_name}) loaded into RAM in {time.time()-t0:.2f}s")
            except Exception as e:
                logging.error(f"[GigaAMEngine] Failed to load GigaAM model: {e}", exc_info=True)
                self._is_ready = False

        if self.enable_punctuation:
            try:
                self.punctuator.preload()
            except Exception as e:
                logging.warning(f"[GigaAMEngine] Failed to preload punctuator: {e}")

    def transcribe_frames(self, frames_list: list, language: str = "ru") -> str:
        """Direct zero-disk in-memory inference with optional neural punctuation."""
        if not frames_list:
            return ""

        if self._model is None:
            self.preload()

        if self._model is None:
            logging.error("[GigaAMEngine] Model is not initialized")
            return ""

        try:
            t0 = time.time()
            raw_bytes = b"".join(frames_list)
            audio_np = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            dur_audio = len(audio_np) / 16000.0

            wav_tensor = torch.from_numpy(audio_np).float().unsqueeze(0)
            length_tensor = torch.tensor([wav_tensor.shape[-1]])

            with torch.inference_mode():
                encoded, encoded_len = self._model.forward(wav_tensor, length_tensor)
                raw_text = self._model.decoding.decode(self._model.head, encoded, encoded_len)[0]

            text = raw_text.strip()
            if text:
                if self.enable_punctuation and self.punctuator.is_ready:
                    # Neural punctuation & capitalization
                    text = self.punctuator.punctuate(text, lang=language if language in ("ru", "en", "de", "es") else "ru")
                else:
                    # Basic capitalization fallback
                    text = text[0].upper() + text[1:]

            elapsed = time.time() - t0
            rtf = elapsed / dur_audio if dur_audio > 0 else 0
            logging.info(f"[GigaAM Direct] Audio {dur_audio:.1f}s → '{text}' in {elapsed:.2f}s (RTF: {rtf:.2f}x)")
            return text

        except Exception as e:
            logging.error(f"[GigaAMEngine] Inference error: {e}", exc_info=True)
            return ""

