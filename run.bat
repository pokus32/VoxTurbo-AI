@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo [!] Окружение .venv не найдено. Запуск установки install.ps1...
    powershell -ExecutionPolicy Bypass -File install.ps1
)

start "" ".venv\Scripts\pythonw.exe" "voxturbo.py"
exit /b 0
