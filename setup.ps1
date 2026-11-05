$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$launcher = Get-Command py.exe -ErrorAction SilentlyContinue
if ($launcher) {
    $pythonCommand = $launcher.Source
    $pythonArguments = @("-3")
} else {
    $launcher = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $launcher) {
        throw "Python 3.10 or newer is required. Install Python and enable the Python Launcher."
    }
    $pythonCommand = $launcher.Source
    $pythonArguments = @()
}

$versionOutput = & $pythonCommand @pythonArguments -c "import sys; print('%d.%d' % sys.version_info[:2])"
if ($LASTEXITCODE -ne 0) {
    throw "Could not start Python. Install Python 3.10 or newer and try again."
}

$pythonVersion = [version]$versionOutput
if ($pythonVersion -lt [version]"3.10") {
    throw "Python 3.10 or newer is required; found Python $pythonVersion."
}

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    & $pythonCommand @pythonArguments -m venv (Join-Path $root ".venv")
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the project virtual environment."
    }
}

if (-not (Test-Path $venvPython)) {
    throw "The project virtual environment was not created at $venvPython."
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Could not upgrade pip in the project virtual environment."
}

& $venvPython -m pip install -r (Join-Path $root "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Could not install the project requirements."
}

$downloadAnswer = Read-Host "Download offline voice models now? This needs an Internet connection (Y/n)"
if ($downloadAnswer -notmatch '^(n|no)$') {
    & $venvPython (Join-Path $root "download_models.py") --wake-word --speech
    if ($LASTEXITCODE -ne 0) {
        throw "Voice-model setup failed. You can retry later with download_models.py."
    }
}

$pythonw = Join-Path $root ".venv\Scripts\pythonw.exe"
if (Test-Path $pythonw) {
    $desktop = [Environment]::GetFolderPath("Desktop")
    if ($desktop) {
        $shortcutPath = Join-Path $desktop "Aarohi AI.lnk"
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $pythonw
        $shortcut.Arguments = "`"$((Join-Path $root 'main.py'))`""
        $shortcut.WorkingDirectory = $root
        $iconPath = Join-Path $root "aaru.ico"
        if (Test-Path $iconPath) {
            $shortcut.IconLocation = $iconPath
        }
        $shortcut.Save()
    }
}

Write-Output "Setup complete. Start Aaru with .\run.ps1 or run.bat."
