# ==============================================================================
# VoxTurbo AI - Windows PowerShell Automated Setup Script
# ==============================================================================
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "       🚀 Установка VoxTurbo AI под Windows           " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Check Python installation
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "[!] Python не найден в системе." -ForegroundColor Red
    Write-Host "[*] Установка Python через winget..." -ForegroundColor Yellow
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

Write-Host "[✓] Python обнаружен: $($pythonCmd.Source)" -ForegroundColor Green

# 2. Setup Virtual Environment
$venvPath = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[*] Создание изолированного виртуального окружения .venv..." -ForegroundColor Yellow
    & python -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
$venvPip = Join-Path $venvPath "Scripts\pip.exe"

# 3. Upgrade Pip & Wheel
Write-Host "[*] Обновление менеджера пакетов pip..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip setuptools wheel

# 4. Install PyTorch with CUDA / CPU auto-detection
Write-Host "[*] Проверка поддержки NVIDIA CUDA..." -ForegroundColor Yellow
$hasNvidia = Get-CimInstance Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" }

if ($hasNvidia) {
    Write-Host "[✓] Обнаружена видеокарта NVIDIA: $($hasNvidia.Name). Установка PyTorch CUDA 12.1..." -ForegroundColor Green
    & $venvPip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
} else {
    Write-Host "[!] NVIDIA GPU не найдена. Установка оптимизированного PyTorch CPU..." -ForegroundColor Yellow
    & $venvPip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
}

# 5. Install requirements
Write-Host "[*] Установка основных зависимостей из requirements.txt..." -ForegroundColor Yellow
& $venvPip install -r (Join-Path $PSScriptRoot "requirements.txt")

# 6. Ensure Windows whisper.cpp binaries
$binDir = Join-Path $PSScriptRoot "bin"
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir | Out-Null
}

$whisperServerExe = Join-Path $binDir "whisper-server.exe"
if (-not (Test-Path $whisperServerExe)) {
    Write-Host "[*] Загрузка оптимизированного бинарника whisper-server.exe (Windows AVX2)..." -ForegroundColor Yellow
    $whisperZipUrl = "https://github.com/ggml-org/whisper.cpp/releases/download/b4938/whisper-bin-x64.zip"
    $tempZip = Join-Path $env:TEMP "whisper-bin.zip"
    Invoke-WebRequest -Uri $whisperZipUrl -OutFile $tempZip
    Expand-Archive -Path $tempZip -DestinationPath $binDir -Force
    Remove-Item $tempZip -Force
}

# 7. Create Desktop Shortcut
$desktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$shortcutPath = Join-Path $desktopPath "VoxTurbo AI.lnk"
$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $venvPath "Scripts\pythonw.exe"
$shortcut.Arguments = "`"$((Join-Path $PSScriptRoot 'voxturbo.py'))`""
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Description = "VoxTurbo AI — Голосовой ввод и транскрибация"
$shortcut.Save()

Write-Host "=====================================================" -ForegroundColor Green
Write-Host " [✓] Установка успешно завершена!                    " -ForegroundColor Green
Write-Host " Ярлык создан на Рабочем столе: 'VoxTurbo AI'        " -ForegroundColor Green
Write-Host " Для запуска выполните: .\run.bat                   " -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
