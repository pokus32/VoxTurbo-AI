"""Streaming pipeline for chunk aggregation and speech transcription."""

import queue
import logging
import threading
from typing import Callable, Optional
from src.engine.client import WhisperHttpClient


class StreamingPipeline:
    """Manage audio chunk queues and assemble final recognized text."""

    def __init__(
        self,
        http_client: Optional[WhisperHttpClient] = None,
        transcribe_fn: Optional[Callable[[list, str], str]] = None,
        on_session_finished: Optional[Callable[[str, str, bool], None]] = None,
        get_current_language: Optional[Callable[[], str]] = None,
    ):
        self.http_client = http_client
        self.transcribe_fn = transcribe_fn
        self.on_session_finished = on_session_finished
        self.get_current_language = get_current_language or (lambda: "ru")

        self.chunk_queue = queue.Queue()
        self.session_results = {}
        self.current_session_id = None
        self._worker_thread = None

    def start_session(self, session_id: str):
        """Initialize a new recording session."""
        self.current_session_id = session_id
        self.session_results[session_id] = []

        # Clear any obsolete chunks in the queue
        while not self.chunk_queue.empty():
            try:
                self.chunk_queue.get_nowait()
            except Exception:
                break

        self._worker_thread = threading.Thread(
            target=self._streaming_worker,
            args=(session_id,),
            daemon=True,
            name=f"Turbo-Worker-{session_id[:8]}"
        )
        self._worker_thread.start()

    def enqueue_chunk(self, session_id: str, chunk_frames: list, is_final: bool = False):
        """Add an audio chunk to the processing queue."""
        self.chunk_queue.put((session_id, chunk_frames, is_final))

    def _streaming_worker(self, session_id: str):
        """Worker thread for asynchronous audio chunk transcription."""
        logging.info(f"[StreamingPipeline] Started worker for session {session_id[:8]}")

        while True:
            try:
                item = self.chunk_queue.get(timeout=45.0)
            except queue.Empty:
                logging.warning(f"[StreamingPipeline] Timeout waiting for chunks in session {session_id[:8]}")
                break

            if item is None:
                break

            item_session_id, chunk_frames, is_final = item

            # Skip obsolete chunks from previous sessions
            if item_session_id != self.current_session_id:
                logging.info(f"[StreamingPipeline] Discarded obsolete chunk for session {item_session_id[:8]}")
                continue

            if chunk_frames and item_session_id == self.current_session_id:
                lang = self.get_current_language()
                if self.transcribe_fn:
                    text_piece = self.transcribe_fn(chunk_frames, lang)
                elif self.http_client:
                    text_piece = self.http_client.send_audio(chunk_frames, language=lang)
                else:
                    text_piece = ""

                if text_piece and item_session_id in self.session_results:
                    self.session_results[item_session_id].append(text_piece)

            if is_final:
                logging.info(f"[StreamingPipeline] Final chunk processed for session {session_id[:8]}. Assembling...")
                chunks = self.session_results.get(session_id, [])
                full_text = " ".join(chunks).strip()
                while "  " in full_text:
                    full_text = full_text.replace("  ", " ")

                success = bool(full_text)
                if not full_text:
                    full_text = "Speech recognition failed or audio was empty"

                logging.info(f"🏆 [Turbo Result] Session {session_id[:8]}: '{full_text}'")

                self.session_results.pop(session_id, None)

                if self.on_session_finished and session_id == self.current_session_id:
                    self.on_session_finished(session_id, full_text, success)
                break
