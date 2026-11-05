$ErrorActionPreference = "Stop"

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
    throw "Flutter is not installed or is not available on PATH."
}
if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
    throw "Firebase CLI is not installed. Install it with: npm install -g firebase-tools"
}
if (-not (Test-Path "firebase.json")) {
    throw "Run this script from the Aaru-Play project root."
}

flutter pub get
if ($LASTEXITCODE -ne 0) {
    throw "flutter pub get failed."
}

flutter build web --release --base-href "/"
if ($LASTEXITCODE -ne 0) {
    throw "Flutter web release build failed."
}

Copy-Item -Path "icon.svg" -Destination "build\web\icon.svg" -Force

firebase deploy --only hosting
if ($LASTEXITCODE -ne 0) {
    throw "Firebase Hosting deployment failed."
}
