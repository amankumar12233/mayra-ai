$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $python)) {
    $python = Join-Path $root ".venv\Scripts\python.exe"
}
if (-not (Test-Path $python)) {
    throw "Aarohi AI is not set up yet. Run .\setup.ps1 first."
}
Set-Location $root
& $python .\main.py
