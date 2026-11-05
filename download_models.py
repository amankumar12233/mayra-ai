"""Install small optional offline voice models from their official sources."""

import argparse
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from config import (
    MODELS_DIR,
    MODEL_NAME,
    VOSK_MODEL_DIR,
    VOSK_MODEL_NAME,
    ensure_user_directories,
)


VOSK_MODEL_URL = (
    "https://alphacephei.com/vosk/models/"
    "vosk-model-small-en-us-0.15.zip"
)
MAX_WAKE_MODEL_BYTES = 250 * 1024 * 1024


def _safe_extract(archive, destination):
    root = destination.resolve()
    with zipfile.ZipFile(archive) as zipped:
        total_size = 0
        for item in zipped.infolist():
            resolved = (root / item.filename).resolve()
            try:
                resolved.relative_to(root)
            except ValueError as exc:
                raise ValueError("The voice model archive contains an unsafe path.") from exc
            total_size += item.file_size
            if total_size > MAX_WAKE_MODEL_BYTES:
                raise ValueError("The extracted wake-word model exceeds the size limit.")
        zipped.extractall(destination)


def download_wake_model():
    if (VOSK_MODEL_DIR / "conf" / "model.conf").is_file():
        print(f"Wake-word model is already installed: {VOSK_MODEL_DIR}")
        return
    ensure_user_directories()
    with tempfile.TemporaryDirectory(prefix="aaru-wake-") as work:
        work_dir = Path(work)
        archive = work_dir / "wake-model.zip"
        request = urllib.request.Request(
            VOSK_MODEL_URL,
            headers={"User-Agent": "AaruAI/1.0 offline-model-setup"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_WAKE_MODEL_BYTES:
                raise ValueError("Wake-word model download exceeded the size limit.")
            downloaded = 0
            with archive.open("wb") as target:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if downloaded > MAX_WAKE_MODEL_BYTES:
                        raise ValueError("Wake-word model download exceeded the size limit.")
                    target.write(chunk)
        extracted = work_dir / "extracted"
        extracted.mkdir()
        _safe_extract(archive, extracted)
        model = extracted / VOSK_MODEL_NAME
        if not (model / "conf" / "model.conf").is_file():
            raise ValueError("The downloaded archive did not contain the expected model.")
        if VOSK_MODEL_DIR.exists():
            raise FileExistsError(f"Refusing to overwrite existing model folder: {VOSK_MODEL_DIR}")
        shutil.move(str(model), str(VOSK_MODEL_DIR))
    print(f"Wake-word model installed: {VOSK_MODEL_DIR}")


def download_speech_model():
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Run `python -m pip install -r requirements.txt`."
        ) from exc
    ensure_user_directories()
    print(f"Downloading the {MODEL_NAME} multilingual Whisper model...")
    WhisperModel(
        MODEL_NAME,
        device="cpu",
        compute_type="int8",
        cpu_threads=2,
        download_root=str(MODELS_DIR),
    )
    print(f"{MODEL_NAME.capitalize()} multilingual offline speech model is ready.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wake-word", action="store_true", help="Download the English wake-word model.")
    parser.add_argument("--speech", action="store_true", help="Download the multilingual command transcription model.")
    args = parser.parse_args()
    if not (args.wake_word or args.speech):
        parser.error("Choose --wake-word, --speech, or both.")
    if args.wake_word:
        download_wake_model()
    if args.speech:
        download_speech_model()


if __name__ == "__main__":
    main()
