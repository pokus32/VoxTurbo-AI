#!/usr/bin/env bash
# ==============================================================================
# VoxTurbo AI — Production Installer & Build Script
# ==============================================================================
set -e

echo "============================================================"
echo " 🚀 Installing VoxTurbo AI (GigaAM + Whisper.cpp)"
echo "============================================================"
echo ""

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
WHISPER_CPP_DIR="${APP_DIR}/whisper.cpp"
VENV_DIR="${APP_DIR}/.venv"

mkdir -p "${BIN_DIR}" "${DESKTOP_DIR}" "${WHISPER_CPP_DIR}/models"

# 1. System prerequisites notice
echo "[1/6] Checking system tools..."
for tool in cmake make git; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "  ⚠️ Warning: '$tool' not found. Please install build essentials (e.g. sudo apt install build-essential cmake)."
    fi
done

# 2. Virtual Environment Setup
echo "[2/6] Setting up Python virtual environment in ${VENV_DIR}..."
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi

VENV_PYTHON="${VENV_DIR}/bin/python3"
VENV_PIP="${VENV_DIR}/bin/pip"

# Install/upgrade pip & requirements
"${VENV_PIP}" install --upgrade pip -q
echo "  Installing Python dependencies from requirements.txt..."
"${VENV_PIP}" install -r "${APP_DIR}/requirements.txt" -q
echo "  ✅ Python virtual environment ready."

# 3. Build C++ Whisper Engine
echo "[3/6] Compiling whisper.cpp server daemon with AVX2/FMA/OpenMP..."
if [ ! -d "${WHISPER_CPP_DIR}" ] || [ ! -f "${WHISPER_CPP_DIR}/CMakeLists.txt" ]; then
    echo "  Cloning official whisper.cpp repository (v1.7.4)..."
    git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git "${WHISPER_CPP_DIR}"
fi

if [ ! -f "${WHISPER_CPP_DIR}/build/bin/whisper-server" ]; then
    cmake -B "${WHISPER_CPP_DIR}/build" -S "${WHISPER_CPP_DIR}" \
        -DGGML_BLAS=ON \
        -DGGML_BLAS_VENDOR=OpenBLAS \
        -DGGML_NATIVE=ON \
        -DGGML_AVX2=ON \
        -DGGML_FMA=ON
    cmake --build "${WHISPER_CPP_DIR}/build" -j "$(nproc 2>/dev/null || echo 4)" --config Release
    echo "  ✅ whisper-server daemon compiled successfully."
else
    echo "  ✅ whisper-server binary already exists."
fi

# 4. Check & Download Default Whisper Models
echo "[4/6] Checking Whisper GGML models..."
SILERO_VAD="${WHISPER_CPP_DIR}/models/ggml-silero-v5.1.2.bin"
TURBO_Q5="${WHISPER_CPP_DIR}/models/ggml-large-v3-turbo-q5_0.bin"

if [ ! -f "${SILERO_VAD}" ]; then
    echo "  Downloading Silero VAD model..."
    curl -L "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-silero-v5.1.2.bin" -o "${SILERO_VAD}" --progress-bar || true
fi

if [ ! -f "${TURBO_Q5}" ]; then
    echo "  Downloading Whisper Large-v3-Turbo Q5_0 model (~548 MB)..."
    curl -L "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin" -o "${TURBO_Q5}" --progress-bar || true
fi

# 5. Generate Portable Executable Launcher
echo "[5/6] Creating launcher in ${BIN_DIR}/voxturbo..."
cat << EOF > "${BIN_DIR}/voxturbo"
#!/usr/bin/env bash
PROJECT_DIR="${APP_DIR}"
VENV_PYTHON="\${PROJECT_DIR}/.venv/bin/python3"

if [ ! -f "\${VENV_PYTHON}" ]; then
    VENV_PYTHON="python3"
fi

exec "\${VENV_PYTHON}" "\${PROJECT_DIR}/voxturbo.py" "\$@"
EOF

chmod +x "${BIN_DIR}/voxturbo"
chmod +x "${APP_DIR}/voxturbo.py"
echo "  ✅ Launcher installed to ${BIN_DIR}/voxturbo"

# 6. Install Desktop Entry
echo "[6/6] Installing desktop application shortcut..."
sed -e "s|Exec=.*|Exec=${BIN_DIR}/voxturbo|" \
    -e "s|Path=.*|Path=${APP_DIR}|" \
    "${APP_DIR}/voxturbo.desktop" > "${DESKTOP_DIR}/voxturbo.desktop"
chmod +x "${DESKTOP_DIR}/voxturbo.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${DESKTOP_DIR}" || true
fi
echo "  ✅ Desktop launcher installed to ${DESKTOP_DIR}/voxturbo.desktop"

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  🎉 VoxTurbo AI Installation Complete!                             ║"
echo "╠════════════════════════════════════════════════════════════════════╣"
echo "║  Launch:                                                           ║"
echo "║    voxturbo &                                                      ║"
echo "║                                                                    ║"
echo "║  Global Shortcut:                                                  ║"
echo "║    Super + Space (Win + Space)                                     ║"
echo "║                                                                    ║"
echo "║  Models directory:                                                 ║"
echo "║    ${WHISPER_CPP_DIR}/models/                                      ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
