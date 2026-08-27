#!/usr/bin/env python3
"""Cross-platform packaging and compilation helper for VoxTurbo AI."""

import os
import sys
import shutil
import argparse
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_for_platform(target_platform: str):
    """Build standalone package using PyInstaller with platform module exclusions."""
    print(f"🚀 Building VoxTurbo AI for target platform: {target_platform.upper()}...")

    dist_dir = os.path.join(PROJECT_ROOT, "dist", target_platform)
    build_dir = os.path.join(PROJECT_ROOT, "build", target_platform)
    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)

    # Exclusions based on target OS
    excludes = []
    if target_platform == "linux":
        excludes.extend(["src.system.windows_input", "src.system.macos_input", "win32api", "win32gui", "AppKit", "Quartz"])
    elif target_platform == "windows":
        excludes.extend(["src.system.linux_input", "src.system.macos_input", "AppKit", "Quartz"])
    elif target_platform == "macos":
        excludes.extend(["src.system.linux_input", "src.system.windows_input", "win32api", "win32gui"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=voxturbo",
        "--onedir",
        "--windowed",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--add-data={os.path.join(PROJECT_ROOT, 'whisper.cpp')}:whisper.cpp",
        os.path.join(PROJECT_ROOT, "voxturbo.py")
    ]

    for exc in excludes:
        cmd.extend(["--exclude-module", exc])

    print(f"Executing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Build successful! Output located at: {dist_dir}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="VoxTurbo Packaging Script")
    parser.add_argument(
        "--target",
        choices=["linux", "windows", "macos", "auto"],
        default="auto",
        help="Target operating system for the build (default: auto-detect)"
    )
    args = parser.parse_args()

    target = args.target
    if target == "auto":
        if sys.platform == "win32":
            target = "windows"
        elif sys.platform == "darwin":
            target = "macos"
        else:
            target = "linux"

    build_for_platform(target)


if __name__ == "__main__":
    main()
