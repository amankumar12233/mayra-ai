"""Local-only notes with safe filenames and no cloud sync."""

import re
from pathlib import Path

from config import MAX_NOTE_CHARS, NOTES_DIR, ensure_user_directories


def save_note(title, text):
    if not isinstance(title, str) or not title.strip() or len(title) > 80:
        raise ValueError("Note title must be 1-80 characters.")
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_NOTE_CHARS:
        raise ValueError(f"Note text must be 1-{MAX_NOTE_CHARS} characters.")
    safe_title = re.sub(r"[^A-Za-z0-9 _-]", "", title).strip().replace(" ", "_")
    if not safe_title:
        raise ValueError("The note title must include a letter or number.")
    ensure_user_directories()
    path = NOTES_DIR / f"{safe_title[:60]}.txt"
    if path.exists() or path.is_symlink():
        raise FileExistsError("A note with that title already exists.")
    path.write_text(text, encoding="utf-8")
    return path


def safe_text_file(relative_path, base_dir):
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise ValueError("Use a path inside the Aaru AI Files folder.")
    root = Path(base_dir).resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("The requested file is outside the Aaru AI Files folder.") from exc
    if not resolved.is_file():
        raise FileNotFoundError("The requested text file was not found.")
    if resolved.stat().st_size > 64_000:
        raise ValueError("Text files must be 64 KB or smaller.")
    try:
        return resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Only UTF-8 text files can be summarized.") from exc
