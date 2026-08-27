# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for VoxTurbo AI (Windows x64).
Creates a lightweight standalone distribution without shipping heavy weight binaries.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
PROJECT_DIR = os.path.abspath(SPECPATH)

# Collect required asset files (excluding large model weights)
datas = [
    (os.path.join(PROJECT_DIR, 'src'), 'src'),
    (os.path.join(PROJECT_DIR, 'models', 'wakewords'), 'models/wakewords'),
]

# Collect pre-built binaries if present in bin/
binaries = []
bin_dir = os.path.join(PROJECT_DIR, 'bin')
if os.path.exists(bin_dir):
    for f in os.listdir(bin_dir):
        if f.endswith('.exe') or f.endswith('.dll'):
            binaries.append((os.path.join(bin_dir, f), 'bin'))

hiddenimports = [
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtWidgets',
    'PyQt5.QtGui',
    'sounddevice',
    'pyaudio',
    'pyperclip',
    'pynput',
    'pynput.keyboard',
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
    'numpy',
    'requests',
    'openwakeword',
    'onnxruntime',
    'gigaam',
    'torch',
    'torchaudio',
    'ctranslate2',
    'faster_whisper',
] + collect_submodules('openwakeword')

a = Analysis(
    ['voxturbo.py'],
    pathex=[PROJECT_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VoxTurbo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_DIR, 'assets', 'icon.ico') if os.path.exists(os.path.join(PROJECT_DIR, 'assets', 'icon.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VoxTurbo',
)
