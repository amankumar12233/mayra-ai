"""Application paths and non-secret settings for Aaru AI."""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


APP_NAME = "Aarohi AI"
APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env", override=False)
MODEL_NAME = "base"
WHISPER_DIR = "whisper-base"
VOSK_MODEL_NAME = "vosk-model-small-en-us-0.15"
WAKE_WORD = "aaru"
MAX_HISTORY_TURNS = 8
MAX_NOTE_CHARS = 20_000
MAX_TEXT_FILE_BYTES = 64_000


def user_data_dir():
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / "AaruAI"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "AaruAI"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "aaru-ai"


DATA_DIR = user_data_dir()
NOTES_DIR = DATA_DIR / "notes"
MODELS_DIR = DATA_DIR / "models"
WHISPER_MODEL_DIR = MODELS_DIR / WHISPER_DIR
VOSK_MODEL_DIR = MODELS_DIR / VOSK_MODEL_NAME
SAFE_FILES_DIR = Path.home() / "Documents" / "Aaru AI Files"
SETTINGS_PATH = DATA_DIR / "settings.json"
CUSTOM_APPS_PATH = DATA_DIR / "custom_apps.json"

DEFAULT_SETTINGS = {
    "provider": "offline",
    "ollama_model": "qwen2.5:1.5b",
    "ollama_url": "http://127.0.0.1:11434",
    "openai_model": "gpt-4o-mini",
    "openrouter_model": "openrouter/auto",
    "theme": "dark",
    "voice_enabled": True,
    "wallpaper_path": "",
    "assistant_icon_path": "",
}


def load_settings():
    settings = dict(DEFAULT_SETTINGS)
    if SETTINGS_PATH.is_file():
        try:
            stored = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            stored = {}
        if isinstance(stored, dict):
            for key in DEFAULT_SETTINGS:
                if key in stored and isinstance(stored[key], type(DEFAULT_SETTINGS[key])):
                    settings[key] = stored[key]
    provider = os.environ.get("AARU_PROVIDER")
    if provider in {"offline", "ollama", "openai", "openrouter"}:
        settings["provider"] = provider
    settings["ollama_url"] = settings["ollama_url"].rstrip("/")
    return settings


def save_settings(settings):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe_settings = {
        key: settings[key]
        for key in DEFAULT_SETTINGS
        if key in settings and isinstance(settings[key], type(DEFAULT_SETTINGS[key]))
    }
    SETTINGS_PATH.write_text(
        json.dumps(safe_settings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ensure_user_directories():
    for path in (DATA_DIR, NOTES_DIR, MODELS_DIR, SAFE_FILES_DIR):
        path.mkdir(parents=True, exist_ok=True)
