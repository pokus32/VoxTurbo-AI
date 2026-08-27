"""Audio stream capture using PyAudio, RMS calculation, and dynamic chunking."""

import logging
import threading
from typing import Callable, Optional
import numpy as np
import pyaudio


class AudioRecorder:
    """Microphone audio capture manager with dynamic chunking."""

    def __init__(
        self,
        on_chunk_ready: Callable[[str, list, bool], None],
        on_bg_lang_detect: Optional[Callable[[list], None]] = None,
        on_amplitude: Optional[Callable[[float], None]] = None,
        rate: int = 16000,
        channels: int = 1,
        frames_per_buffer: int = 1024,
        silence_threshold: float = 400.0,
    ):
        self.on_chunk_ready = on_chunk_ready
        self.on_bg_lang_detect = on_bg_lang_detect
        self.on_amplitude = on_amplitude
        self.rate = rate
        self.channels = channels
        self.frames_per_buffer = frames_per_buffer
        self.silence_threshold = silence_threshold

        self.is_recording = False
        self.current_session_id = None
        self.frames = []
        self.current_chunk_frames = []

        self._audio_thread = None
        self._pyaudio_inst = None
        self._stream = None

    def start(self, session_id: str, enable_auto_lang: bool = False, chunk_strategy: str = "stream"):
        """Start the background audio recording thread.
        
        chunk_strategy:
            - 'stream': pause-based chunking (5-8s) for ultra-fast CTC/Small model inference.
            - 'full_window': accumulate up to 28.0s to preserve context for Whisper Large.
        """
        if self.is_recording:
            return

        self.is_recording = True
        self.current_session_id = session_id
        self.frames = []
        self.current_chunk_frames = []

        self._audio_thread = threading.Thread(
            target=self._record_loop,
            args=(session_id, enable_auto_lang, chunk_strategy),
            daemon=True,
            name=f"AudioRecord-{session_id[:8]}"
        )
        self._audio_thread.start()

    def stop(self) -> list:
        """Stop recording and return remaining uncommitted audio frames."""
        if not self.is_recording:
            return []

        self.is_recording = False
        final_audio = list(self.current_chunk_frames)
        self.current_chunk_frames = []
        return final_audio

    def _record_loop(self, session_id: str, enable_auto_lang: bool, chunk_strategy: str):
        """Main recording loop reading PCM frames from microphone."""
        try:
            self._pyaudio_inst = pyaudio.PyAudio()
            self._stream = self._pyaudio_inst.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.frames_per_buffer
            )

            lang_detection_triggered = False
            consecutive_silence_frames = 0

            while self.is_recording and self.current_session_id == session_id:
                data = self._stream.read(self.frames_per_buffer, exception_on_overflow=False)
                self.frames.append(data)
                self.current_chunk_frames.append(data)

                frame_arr = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(frame_arr.astype(np.float32) ** 2))

                if self.on_amplitude:
                    norm_amp = min(1.0, max(0.0, (rms - 100.0) / 2500.0))
                    self.on_amplitude(float(norm_amp))

                if rms < self.silence_threshold:
                    consecutive_silence_frames += 1
                else:
                    consecutive_silence_frames = 0

                # Trigger background language detector during initial speech frames
                if (
                    enable_auto_lang
                    and not lang_detection_triggered
                    and len(self.frames) >= 28
                    and self.on_bg_lang_detect
                ):
                    lang_detection_triggered = True
                    snapshot = list(self.frames)
                    threading.Thread(
                        target=self.on_bg_lang_detect,
                        args=(snapshot,),
                        daemon=True,
                        name="BgLangDetector"
                    ).start()

                chunk_len = len(self.current_chunk_frames)

                # 1. 'stream' mode (GigaAM / Small): pause-based chunking (5-8 seconds)
                if chunk_strategy == "stream":
                    is_pause_chunk = chunk_len >= 80 and consecutive_silence_frames >= 6
                    is_max_len_chunk = chunk_len >= 125  # ~8.0s

                    if is_pause_chunk or is_max_len_chunk:
                        chunk_to_process = list(self.current_chunk_frames)
                        self.current_chunk_frames = []
                        consecutive_silence_frames = 0
                        dur = chunk_len * self.frames_per_buffer / self.rate
                        reason = "pause" if is_pause_chunk else "max_len"
                        logging.info(f"[AudioRecorder] Stream chunk ({dur:.2f}s, reason: {reason}) enqueued...")
                        self.on_chunk_ready(session_id, chunk_to_process, False)

                # 2. 'full_window' mode (Whisper Large Turbo): accumulate up to 28s for rich context
                elif chunk_strategy == "full_window":
                    # 437 frames * 1024 / 16000 = ~28.0 seconds (fits safely into 30s Whisper window)
                    if chunk_len >= 437:
                        chunk_to_process = list(self.current_chunk_frames)
                        self.current_chunk_frames = []
                        consecutive_silence_frames = 0
                        dur = chunk_len * self.frames_per_buffer / self.rate
                        logging.info(f"[AudioRecorder] Large window ({dur:.2f}s, reached 28s limit) enqueued...")
                        self.on_chunk_ready(session_id, chunk_to_process, False)

        except Exception as e:
            logging.error(f"Error in PyAudio recording loop: {e}", exc_info=True)
        finally:
            if self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except Exception:
                    pass
            if self._pyaudio_inst:
                try:
                    self._pyaudio_inst.terminate()
                except Exception:
                    pass
