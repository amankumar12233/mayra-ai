#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
"$PYTHON" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ is required"'
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
printf "Download offline voice models now? This needs an Internet connection (Y/n): "
read answer
case "$answer" in
  n|N|no|NO) ;;
  *)
    .venv/bin/python download_models.py --wake-word --speech
    ;;
esac
echo "Setup complete. Start Aaru with ./run.sh"
