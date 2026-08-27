#!/usr/bin/env python3
"""
VoxTurbo AI — Modular Entry Point.
Engines: GigaAM v2 Conformer CTC + Whisper.cpp Large-v3-Turbo resident in RAM.
"""

import sys
import os

# Add project root directory to sys.path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from src.app import main, VoiceTurboApp

if __name__ == "__main__":
    main()
