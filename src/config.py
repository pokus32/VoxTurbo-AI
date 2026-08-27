"""Configuration, paths, and constants for VoxTurbo AI."""

import os
import json
import logging
from pathlib import Path

# Base directories
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WHISPER_CPP_DIR = os.path.join(APP_DIR, 'whisper.cpp')
WHISPER_CPP_SERVER_BIN = os.path.join(WHISPER_CPP_DIR, 'build', 'bin', 'whisper-server')
WHISPER_CPP_MODELS_DIR = os.path.join(WHISPER_CPP_DIR, 'models')
WHISPER_CPP_VAD_MODEL = os.path.join(WHISPER_CPP_MODELS_DIR, 'ggml-silero-v5.1.2.bin')
TURBO_PORT = 8091

# Standard XDG paths for user configuration and state data
XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
XDG_STATE_HOME = os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))

USER_CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "voxturbo")
USER_STATE_DIR = os.path.join(XDG_STATE_HOME, "voxturbo")

CONFIG_FILE = os.path.join(USER_CONFIG_DIR, 'config.json')
LOG_FILE = os.path.join(USER_STATE_DIR, 'voxturbo.log')
LAST_INPUT_FILE = os.path.join(USER_STATE_DIR, 'last_voice_input.txt')

DEFAULT_CONFIG = {
    "engine": "gigaam",         # "gigaam" or "whisper"
    "model_quant": "gigaam_v2", # "gigaam_v2", "q5_0", "q8_0", "small", "base"
    "threads": 4,               # CPU threads (e.g. 4 or 6)
    "language": "auto",         # "auto", "ru", "kk", "en"
    "flash_attn": True,
    "enable_punctuation": True, # Silero TE neural post-processing for GigaAM
    "enable_hud": True          # Modern floating voice HUD overlay
}


def setup_logging():
    """Configure file-based logging."""
    os.makedirs(USER_STATE_DIR, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_user_config() -> dict:
    """Load user configuration with fallback defaults."""
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                cfg.update(saved)
                logging.info(f"Loaded user config: {cfg}")
                return cfg
        except Exception as e:
            logging.error(f"Failed to read config file: {e}")
    return cfg


def save_user_config(cfg: dict):
    """Save user configuration to JSON file."""
    try:
        os.makedirs(USER_CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        logging.info(f"Config saved successfully: {cfg}")
    except Exception as e:
        logging.error(f"Failed to save config: {e}")


def get_model_path(model_quant: str) -> str:
    """Resolve the path to the whisper model binary with fallback mechanisms."""
    if model_quant == "small":
        small_path = os.path.join(WHISPER_CPP_MODELS_DIR, "ggml-small.bin")
        if os.path.exists(small_path):
            return small_path
    elif model_quant == "base":
        base_path = os.path.join(WHISPER_CPP_MODELS_DIR, "ggml-base.bin")
        if os.path.exists(base_path):
            return base_path

    filename = f"ggml-large-v3-turbo-{model_quant}.bin"
    path = os.path.join(WHISPER_CPP_MODELS_DIR, filename)
    if os.path.exists(path):
        return path

    # Fallback to q5_0
    fallback = os.path.join(WHISPER_CPP_MODELS_DIR, "ggml-large-v3-turbo-q5_0.bin")
    if os.path.exists(fallback):
        return fallback
    return os.path.join(WHISPER_CPP_MODELS_DIR, "ggml-small.bin")
