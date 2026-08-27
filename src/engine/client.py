"""HTTP client for sending audio to whisper-server."""

import http.client
import io
import time
import uuid
import json
import urllib.error
import wave
import logging
import urllib.request
from src.config import TURBO_PORT


class WhisperHttpClient:
    """Client for communicating with whisper-server over HTTP."""

    def __init__(self, port: int = TURBO_PORT):
        self.port = port
        self.default_prompt = "Python, Linux, API, Docker, Git, code, script, function, bug. Hello, how are you."

    def send_audio(self, frames_list: list, language: str = "ru", prompt: str = None) -> str:
        """Send a list of audio frames (PCM 16kHz mono) to whisper-server in-memory."""
        if not frames_list:
            return ""

        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"".join(frames_list))
        wav_bytes = wav_io.getvalue()

        if not prompt:
            prompt = self.default_prompt

        try:
            t0 = time.time()
            boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"

            body = []
            body.append(f"--{boundary}\r\n".encode())
            body.append(b'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n')
            body.append(b'Content-Type: audio/wav\r\n\r\n')
            body.append(wav_bytes)
            body.append(b'\r\n')

            body.append(f"--{boundary}\r\n".encode())
            body.append(b'Content-Disposition: form-data; name="language"\r\n\r\n')
            body.append(language.encode('utf-8'))
            body.append(b'\r\n')

            body.append(f"--{boundary}\r\n".encode())
            body.append(b'Content-Disposition: form-data; name="response_format"\r\n\r\n')
            body.append(b'json\r\n')
            body.append(b'\r\n')

            body.append(f"--{boundary}\r\n".encode())
            body.append(b'Content-Disposition: form-data; name="prompt"\r\n\r\n')
            body.append(prompt.encode('utf-8'))
            body.append(b'\r\n')

            body.append(f"--{boundary}--\r\n".encode())
            payload = b"".join(body)

            req = urllib.request.Request(
                f"http://127.0.0.1:{self.port}/inference",
                data=payload,
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Content-Length": str(len(payload))
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=25.0) as resp:
                resp_text = resp.read().decode('utf-8').strip()
                elapsed = time.time() - t0

                try:
                    parsed_json = json.loads(resp_text)
                    if isinstance(parsed_json, dict) and "text" in parsed_json:
                        text = parsed_json["text"].strip()
                    else:
                        text = str(parsed_json).strip()
                except Exception:
                    lines = [
                        line.strip()
                        for line in resp_text.split("\n")
                        if line.strip() and not line.startswith("read_audio_data")
                    ]
                    text = " ".join(lines).strip()

                dur_audio = len(wav_bytes) / (16000 * 2)
                logging.info(f"[Turbo HTTP] Audio {dur_audio:.1f}s → '{text}' in {elapsed:.2f}s")
                return text

        except (urllib.error.URLError, http.client.RemoteDisconnected, TimeoutError) as e:
            logging.warning(f"[Turbo HTTP] Request interrupted or timed out: {e}")
            return ""
        except Exception as e:
            logging.error(f"[Turbo HTTP] Server request error: {e}", exc_info=True)
            return ""
