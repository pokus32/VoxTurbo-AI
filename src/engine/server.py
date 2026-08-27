"""Lifecycle management for the whisper-server C++ daemon."""

import os
import time
import logging
import subprocess
import urllib.request
from src.config import (
    WHISPER_CPP_SERVER_BIN,
    WHISPER_CPP_VAD_MODEL,
    TURBO_PORT,
    get_model_path,
)


class WhisperServerManager:
    """Manager for the background C++ whisper-server process."""

    def __init__(
        self,
        server_bin: str = WHISPER_CPP_SERVER_BIN,
        vad_model: str = WHISPER_CPP_VAD_MODEL,
        port: int = TURBO_PORT,
    ):
        self.server_bin = server_bin
        self.vad_model = vad_model
        self.port = port
        self.server_process = None
        self.server_current_model_path = None
        self.server_ready = False

    def is_alive(self) -> bool:
        """Check if HTTP server is responsive via health-check endpoint."""
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{self.port}/", method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def ensure_running(self, model_quant: str, cpu_threads: int, flash_attn: bool = True) -> bool:
        """Launch whisper-server with optimal CPU flags if not already running."""
        model_path = get_model_path(model_quant)

        if (
            self.server_process
            and self.server_process.poll() is None
            and self.server_current_model_path == model_path
            and self.server_ready
        ):
            logging.info(f"[WhisperServer] Server is already running with model {model_path}")
            return True

        self.stop()
        logging.info(
            f"[WhisperServer] Launching Turbo server in RAM "
            f"(Model: {model_path}, Threads: {cpu_threads}, Port: {self.port})..."
        )

        try:
            cmd = [
                self.server_bin,
                "-m", model_path,
                "--host", "127.0.0.1",
                "--port", str(self.port),
                "-t", str(cpu_threads),
                "-p", "1",
                "-nt",
                "-bo", "1",
                "-bs", "1",
                "-nf",
                "-ac", "768"
            ]

            if flash_attn:
                cmd.append("-fa")

            # Enable Silero VAD if model file is present
            if os.path.exists(self.vad_model):
                cmd += [
                    "--vad",
                    "-vm", self.vad_model,
                    "-vt", "0.5",
                    "-vsd", "300",
                    "-vp", "50"
                ]
                logging.info("[WhisperServer] Silero VAD enabled.")

            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.server_current_model_path = model_path
            self.server_ready = False

            # Await server readiness
            for _ in range(35):
                time.sleep(0.3)
                if self.is_alive():
                    self.server_ready = True
                    logging.info("✅ Turbo whisper-server daemon is ready in RAM!")
                    return True

            logging.warning("[WhisperServer] Server startup timed out.")
            return False
        except Exception as e:
            logging.error(f"[WhisperServer] Startup error: {e}", exc_info=True)
            return False

    def stop(self):
        """Gracefully terminate whisper-server."""
        if self.server_process:
            try:
                logging.info("[WhisperServer] Stopping whisper-server daemon...")
                self.server_process.terminate()
                self.server_process.wait(timeout=2.0)
            except Exception:
                try:
                    self.server_process.kill()
                except Exception:
                    pass
            self.server_process = None
            self.server_current_model_path = None
            self.server_ready = False
