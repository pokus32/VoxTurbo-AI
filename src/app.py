"""Main coordinator and entry point for VoxTurbo AI."""

import os
import sys
import uuid
import logging
import threading
from PyQt5.QtWidgets import QApplication

from src.config import (
    setup_logging,
    load_user_config,
    save_user_config,
)
from src.engine.server import WhisperServerManager
from src.engine.client import WhisperHttpClient
from src.engine.detector import LanguageDetector
from src.engine.pipeline import StreamingPipeline
from src.engine.gigaam_engine import GigaAMEngine
from src.audio.recorder import AudioRecorder
from src.system.hotkey import HotkeyManager
from src.system.clipboard import PasteManager
from src.ui.signals import SignalHelper
from src.ui.tray import TrayManager
from src.ui.hud import VoiceHUDWidget


class VoiceTurboApp:
    """Main application class: orchestrate UI, audio capture, Whisper C++ daemon and GigaAM."""

    def __init__(self):
        # Configure logging
        setup_logging()
        logging.info("=== Starting VoxTurbo AI (GigaAM + Whisper Edition) ===")

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Configuration
        self.cfg = load_user_config()
        self.model_quant = self.cfg.get("model_quant", "gigaam_v2")
        self.cpu_threads = self.cfg.get("threads", 4)
        self.target_language = self.cfg.get("language", "auto")
        self.flash_attn = self.cfg.get("flash_attn", True)
        self.enable_punctuation = self.cfg.get("enable_punctuation", True)
        self.enable_hud = self.cfg.get("enable_hud", True)

        self.current_session_id = None
        self.detected_lang_in_flight = None

        # Initialize signals
        self.signals = SignalHelper()
        self.signals.toggle_signal.connect(self.toggle_recording)
        self.signals.update_signal.connect(self.on_processing_complete)
        self.signals.notify_signal.connect(self.show_notification)
        self.signals.paste_signal.connect(self.do_paste)
        self.signals.state_signal.connect(self.set_ui_state)
        self.signals.amplitude_signal.connect(self._on_amplitude_signal)

        # Floating HUD Overlay
        self.hud = VoiceHUDWidget() if self.enable_hud else None

        # Engine components
        self.server_mgr = WhisperServerManager()
        self.http_client = WhisperHttpClient()
        self.gigaam_engine = GigaAMEngine(
            model_name="v2_ctc",
            cpu_threads=self.cpu_threads,
            enable_punctuation=self.enable_punctuation
        )
        self.detector = LanguageDetector()

        # Streaming pipeline with dynamic engine dispatching
        self.pipeline = StreamingPipeline(
            http_client=self.http_client,
            transcribe_fn=self._transcribe_audio_chunk,
            on_session_finished=self._on_pipeline_session_finished,
            get_current_language=self._resolve_current_language
        )

        # Audio recorder with live amplitude feedback
        self.recorder = AudioRecorder(
            on_chunk_ready=self._on_audio_chunk_ready,
            on_bg_lang_detect=self._on_bg_detect_lang,
            on_amplitude=self.signals.amplitude_signal.emit
        )

        # UI System Tray
        self.tray_mgr = TrayManager(
            parent_app=self.app,
            on_toggle_recording=self.toggle_recording,
            on_change_quant=self.set_quant,
            on_change_threads=self.set_threads,
            on_change_language=self.set_language,
            on_toggle_punctuation=self.toggle_punctuation,
            on_toggle_hud=self.toggle_hud,
            on_quit=self.quit_app
        )
        self.tray_mgr.update_checks(
            self.model_quant,
            self.cpu_threads,
            self.target_language,
            self.enable_punctuation,
            self.enable_hud
        )
        self.tray_mgr.show()

        # Global hotkey Super+Space
        self.hotkey_mgr = HotkeyManager(on_hotkey_pressed=self.signals.toggle_signal.emit)
        self.hotkey_mgr.start()

        # Background backend warmup
        threading.Thread(target=self._init_backend, daemon=True, name="TurboInitThread").start()

    def _on_amplitude_signal(self, amp: float):
        """Pass live amplitude to HUD overlay."""
        if self.hud and self.enable_hud:
            self.hud.set_amplitude(amp)

    def _transcribe_audio_chunk(self, chunk_frames: list, language: str) -> str:
        """Route transcription to active engine (GigaAM or Whisper)."""
        if self.model_quant == "gigaam_v2":
            return self.gigaam_engine.transcribe_frames(chunk_frames, language=language)
        else:
            return self.http_client.send_audio(chunk_frames, language=language)

    def _resolve_current_language(self) -> str:
        """Resolve effective language code for active request."""
        if self.target_language == "auto":
            return self.detected_lang_in_flight or "ru"
        return self.target_language

    def _init_backend(self):
        """Initialize active engine backend (GigaAM or whisper-server)."""
        self.signals.state_signal.emit("loading", "")

        # 1. Preload language detector for Whisper
        if self.model_quant != "gigaam_v2":
            try:
                self.detector.preload()
            except Exception as e:
                logging.error(f"Language detector initialization error: {e}")

        # 2. Initialize chosen engine
        if self.model_quant == "gigaam_v2":
            self.server_mgr.stop()
            self.gigaam_engine.preload()
            self.signals.notify_signal.emit("VoxTurbo", "GigaAM v2 ready in RAM")
        else:
            server_ok = self.server_mgr.ensure_running(
                model_quant=self.model_quant,
                cpu_threads=self.cpu_threads,
                flash_attn=self.flash_attn
            )
            if server_ok:
                self.signals.notify_signal.emit("VoxTurbo", f"Whisper ({self.model_quant.upper()}) ready in RAM")

        self.signals.state_signal.emit("idle", "")

    def set_ui_state(self, state_name: str, extra: str = ""):
        self.tray_mgr.set_state(
            state_name=state_name,
            model_quant=self.model_quant,
            cpu_threads=self.cpu_threads,
            language=self.target_language
        )
        if self.hud and self.enable_hud:
            model_label = "GigaAM v2" if self.model_quant == "gigaam_v2" else f"Whisper {self.model_quant.upper()}"
            self.hud.set_state(state_name, model_label=model_label, detail=extra)

    def show_notification(self, title: str, message: str):
        self.tray_mgr.show_notification(title, message)

    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if self.recorder.is_recording:
            return

        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        self.detected_lang_in_flight = None

        logging.info(
            f"Recording started [Session: {session_id[:8]}] "
            f"(Model: {self.model_quant}, Threads: {self.cpu_threads}, Lang: {self.target_language})"
        )

        self.signals.state_signal.emit("recording", "")

        # Start session pipeline
        self.pipeline.start_session(session_id)

        # Start audio capture
        enable_auto = (self.target_language == "auto" and self.model_quant != "gigaam_v2")
        # For Whisper Large (q5_0, q8_0), use full_window mode (up to 28s) for maximum context;
        # for GigaAM and smaller models (small, base), use stream mode (pause-based 5-8s chunks).
        chunk_strategy = "full_window" if self.model_quant in ("q5_0", "q8_0") else "stream"
        self.recorder.start(session_id, enable_auto_lang=enable_auto, chunk_strategy=chunk_strategy)

    def stop_recording(self):
        if not self.recorder.is_recording:
            return

        session_id = self.current_session_id
        logging.info(f"Recording stopped [Session: {session_id[:8]}]. Finalizing...")

        self.signals.state_signal.emit("processing", "")

        # Stop audio capture and pass final trailing frames
        final_chunk = self.recorder.stop()
        self.pipeline.enqueue_chunk(session_id, final_chunk, is_final=True)

    def _on_audio_chunk_ready(self, session_id: str, chunk_frames: list, is_final: bool):
        self.pipeline.enqueue_chunk(session_id, chunk_frames, is_final)

    def _on_bg_detect_lang(self, frames_snapshot: list):
        lang = self.detector.detect(frames_snapshot)
        self.detected_lang_in_flight = lang

    def _on_pipeline_session_finished(self, session_id: str, full_text: str, success: bool):
        if success and session_id == self.current_session_id:
            self.signals.paste_signal.emit(full_text)
        self.signals.update_signal.emit(full_text, success)

    def do_paste(self, text: str):
        PasteManager.save_and_paste(text)

    def on_processing_complete(self, text: str, success: bool):
        self.tray_mgr.update_last_text(text, success, self.model_quant)
        self.tray_mgr.update_checks(
            self.model_quant,
            self.cpu_threads,
            self.target_language,
            self.enable_punctuation,
            self.enable_hud
        )
        if success:
            self.signals.state_signal.emit("success", text)
        else:
            self.signals.state_signal.emit("idle", "")

    def set_quant(self, quant_type: str):
        self.model_quant = quant_type
        self.cfg["model_quant"] = quant_type
        save_user_config(self.cfg)

        logging.info(f"Selected model: {quant_type}")
        self.tray_mgr.update_checks(
            self.model_quant,
            self.cpu_threads,
            self.target_language,
            self.enable_punctuation,
            self.enable_hud
        )
        label = "GigaAM v2" if quant_type == "gigaam_v2" else f"Whisper {quant_type.upper()}"
        self.show_notification("VoxTurbo", f"Active Engine: {label}")
        threading.Thread(target=self._init_backend, daemon=True, name="EngineSwitchThread").start()

    def set_threads(self, thread_count: int):
        self.cpu_threads = thread_count
        self.cfg["threads"] = thread_count
        save_user_config(self.cfg)

        logging.info(f"Selected CPU threads: {thread_count}")
        self.gigaam_engine.cpu_threads = thread_count
        self.tray_mgr.update_checks(
            self.model_quant,
            self.cpu_threads,
            self.target_language,
            self.enable_punctuation,
            self.enable_hud
        )
        self.show_notification("VoxTurbo", f"CPU Threads: {thread_count}")
        threading.Thread(target=self._init_backend, daemon=True, name="ThreadSwitchThread").start()

    def set_language(self, lang_code: str):
        self.target_language = lang_code
        self.cfg["language"] = lang_code
        save_user_config(self.cfg)

        logging.info(f"Selected language: {lang_code.upper()}")
        self.tray_mgr.update_checks(
            self.model_quant,
            self.cpu_threads,
            self.target_language,
            self.enable_punctuation,
            self.enable_hud
        )
        labels = {
            "auto": "⚡ Auto-detection",
            "ru": "🇷🇺 Russian",
            "kk": "🇰🇿 Kazakh",
            "en": "🇬🇧 English"
        }
        self.show_notification("VoxTurbo", f"Language: {labels.get(lang_code, lang_code)}")

    def toggle_punctuation(self, enabled: bool):
        self.enable_punctuation = enabled
        self.cfg["enable_punctuation"] = enabled
        self.gigaam_engine.enable_punctuation = enabled
        save_user_config(self.cfg)

        logging.info(f"Smart Punctuation toggled: {enabled}")
        self.tray_mgr.update_checks(
            self.model_quant,
            self.cpu_threads,
            self.target_language,
            self.enable_punctuation,
            self.enable_hud
        )
        status_str = "Enabled" if enabled else "Disabled"
        self.show_notification("VoxTurbo", f"Smart Punctuation: {status_str}")

    def toggle_hud(self, enabled: bool):
        self.enable_hud = enabled
        self.cfg["enable_hud"] = enabled
        save_user_config(self.cfg)

        if enabled and self.hud is None:
            self.hud = VoiceHUDWidget()
        elif not enabled and self.hud is not None:
            self.hud.hide()

        logging.info(f"Floating Voice HUD toggled: {enabled}")
        self.tray_mgr.update_checks(
            self.model_quant,
            self.cpu_threads,
            self.target_language,
            self.enable_punctuation,
            self.enable_hud
        )
        status_str = "Enabled" if enabled else "Disabled"
        self.show_notification("VoxTurbo", f"Voice HUD: {status_str}")

    def quit_app(self):
        logging.info("Exiting VoxTurbo AI")
        self.server_mgr.stop()
        self.hotkey_mgr.stop()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec_())


def main():
    app = VoiceTurboApp()
    app.run()


if __name__ == "__main__":
    main()
