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
        on_wakeword_detected: Optional[Callable[[], None]] = None,
        on_auto_silence: Optional[Callable[[], None]] = None,
        rate: int = 16000,
        channels: int = 1,
        frames_per_buffer: int = 1024,
        silence_threshold: float = 400.0,
    ):
        self.on_chunk_ready = on_chunk_ready
        self.on_bg_lang_detect = on_bg_lang_detect
        self.on_amplitude = on_amplitude
        self.on_wakeword_detected = on_wakeword_detected
        self.on_auto_silence = on_auto_silence
        self.rate = rate
        self.channels = channels
        self.frames_per_buffer = frames_per_buffer
        self.silence_threshold = silence_threshold

        self.is_recording = False
        self.is_wakeword_listening = False
        self.wakeword_detector = None
        self.auto_silence_duration = 0.8
        self.is_auto_silence_active = False

        self.current_session_id = None
        self.frames = []
        self.current_chunk_frames = []

        self._audio_thread = None
        self._bg_listener_thread = None
        self._pyaudio_inst = None
        self._stream = None

    def start_wakeword_listening(self, wakeword_detector):
        """Start background microphone monitoring for wake word triggers."""
        self.wakeword_detector = wakeword_detector
        if self.is_wakeword_listening:
            return
        self.is_wakeword_listening = True
        self._bg_listener_thread = threading.Thread(
            target=self._wakeword_listen_loop,
            daemon=True,
            name="WakeWordListener"
        )
        self._bg_listener_thread.start()

    def stop_wakeword_listening(self):
        """Stop background wake word monitoring."""
        self.is_wakeword_listening = False

    def start(
        self,
        session_id: str,
        enable_auto_lang: bool = False,
        chunk_strategy: str = "stream",
        enable_auto_silence: bool = False,
        silence_duration: float = 0.8
    ):
        """Start the background audio recording thread.
        
        chunk_strategy:
            - 'stream': pause-based chunking (5-8s) for ultra-fast CTC/Small model inference.
            - 'full_window': accumulate up to 28.0s to preserve context for Whisper Large.
        """
        if self.is_recording:
            return

        self.is_recording = True
        self.is_auto_silence_active = enable_auto_silence
        self.auto_silence_duration = silence_duration
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

    def _wakeword_listen_loop(self):
        """Continuous background audio stream for wake word spotting while idle."""
        pyaudio_inst = None
        stream = None
        # openWakeWord expects 1280 samples at 16kHz
        chunk_samples = 1280
        try:
            pyaudio_inst = pyaudio.PyAudio()
            stream = pyaudio_inst.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=chunk_samples
            )
            logging.info("[AudioRecorder] Wake Word background listener started.")

            while self.is_wakeword_listening:
                if self.is_recording:
                    import time
                    time.sleep(0.1)
                    continue

                try:
                    data = stream.read(chunk_samples, exception_on_overflow=False)
                except Exception:
                    continue

                if self.wakeword_detector and self.wakeword_detector.is_ready:
                    if self.wakeword_detector.process_frame(data):
                        logging.info("[AudioRecorder] Wake Word triggered! Emitting event...")
                        if self.on_wakeword_detected:
                            self.on_wakeword_detected()

        except Exception as e:
            logging.error(f"[AudioRecorder] Error in Wake Word listen loop: {e}", exc_info=True)
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            if pyaudio_inst:
                try:
                    pyaudio_inst.terminate()
                except Exception:
                    pass
            logging.info("[AudioRecorder] Wake Word background listener stopped.")

    def _record_loop(self, session_id: str, enable_auto_lang: bool, chunk_strategy: str):
        """Main recording loop reading PCM frames with neural VAD silence tracking."""
        try:
            # Initialize lightweight neural VAD for robust silence detection
            vad = None
            try:
                from openwakeword.vad import VAD
                vad = VAD()
            except Exception as e:
                logging.warning(f"[AudioRecorder] Could not initialize neural VAD: {e}")

            # 960 samples = 60ms (2x 480 frames for Silero VAD)
            buffer_samples = 960
            self._pyaudio_inst = pyaudio.PyAudio()
            self._stream = self._pyaudio_inst.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=buffer_samples
            )

            lang_detection_triggered = False
            consecutive_silence_frames = 0
            has_detected_speech = False

            # Each frame is 960 / 16000 = 0.060s
            frames_per_sec = self.rate / buffer_samples
            max_silence_frames_for_auto_stop = max(3, int(self.auto_silence_duration * frames_per_sec))

            while self.is_recording and self.current_session_id == session_id:
                data = self._stream.read(buffer_samples, exception_on_overflow=False)
                self.frames.append(data)
                self.current_chunk_frames.append(data)

                frame_arr = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(frame_arr.astype(np.float32) ** 2))

                if self.on_amplitude:
                    norm_amp = min(1.0, max(0.0, (rms - 100.0) / 2500.0))
                    self.on_amplitude(float(norm_amp))

                # Neural VAD speech probability check
                is_speech = False
                if vad is not None:
                    try:
                        speech_prob = vad.predict(frame_arr, frame_size=480)
                        # Threshold for speech presence: prob > 0.35
                        is_speech = (speech_prob >= 0.35)
                    except Exception:
                        is_speech = (rms >= self.silence_threshold)
                else:
                    is_speech = (rms >= self.silence_threshold)

                if is_speech:
                    has_detected_speech = True
                    consecutive_silence_frames = 0
                else:
                    consecutive_silence_frames += 1

                # Check auto-stop on silence:
                # Trigger only after user has spoken at least once, or after 1.2s of total audio
                if (
                    self.is_auto_silence_active
                    and (has_detected_speech or len(self.frames) >= int(frames_per_sec * 1.2))
                    and consecutive_silence_frames >= max_silence_frames_for_auto_stop
                ):
                    dur_silence = consecutive_silence_frames / frames_per_sec
                    logging.info(
                        f"[AudioRecorder] Neural VAD Auto-silence stop triggered! "
                        f"({consecutive_silence_frames} frames / {dur_silence:.2f}s silence >= {self.auto_silence_duration}s)"
                    )
                    if self.on_auto_silence:
                        self.on_auto_silence()
                    break

                # Trigger background language detector during initial speech frames
                if (
                    enable_auto_lang
                    and not lang_detection_triggered
                    and len(self.frames) >= 20
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
