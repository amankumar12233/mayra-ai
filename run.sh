#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Aaru is not set up yet. Run ./setup.sh first." >&2
  exit 1
fi
exec .venv/bin/python main.py
