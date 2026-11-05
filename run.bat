@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Aarohi AI is not set up yet. Right-click setup.ps1 and run with PowerShell,
  echo or use: powershell -ExecutionPolicy Bypass -File .\setup.ps1
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" ".\main.py"
