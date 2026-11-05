"""Small cross-platform application and website allowlists."""

import os
import json
import re
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

from config import CUSTOM_APPS_PATH


APP_ALIAS_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,59}\Z")

APPS = {
    "chrome": ("chrome", "google chrome", "google chrome browser"),
    "edge": ("edge", "microsoft edge", "edge browser"),
    "notepad": ("notepad", "text editor"),
    "calculator": ("calculator", "calc"),
    "paint": ("paint", "mspaint"),
    "word": ("word", "microsoft word", "ms word"),
    "excel": ("excel", "microsoft excel"),
    "powerpoint": ("powerpoint", "microsoft powerpoint", "ppt"),
    "vscode": ("vscode", "vs code", "visual studio code"),
    "task_manager": ("task manager", "taskmgr", "system monitor", "activity monitor"),
    "settings": ("settings", "windows settings", "system settings"),
    "control_panel": ("control panel",),
    "snipping_tool": ("snipping tool", "screenshot tool"),
    "camera": ("camera", "webcam"),
    "explorer": ("file explorer", "explorer", "files"),
}

SITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "youtube settings": "https://www.youtube.com/account",
    "youtube account": "https://www.youtube.com/account",
    "youtube studio": "https://studio.youtube.com/",
    "youtube channel": "https://studio.youtube.com/",
    "gmail": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "chatgpt": "https://chatgpt.com",
    "claude": "https://claude.ai",
    "maps": "https://maps.google.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "github": "https://github.com",
}

SITE_ALIASES = {
    "google": "google",
    "youtube": "youtube",
    "youtube settings": "youtube settings",
    "youtube account": "youtube account",
    "youtube account settings": "youtube settings",
    "youtube channel settings": "youtube settings",
    "youtube studio": "youtube studio",
    "youtube creator studio": "youtube studio",
    "youtube channel": "youtube channel",
    "channel dashboard": "youtube studio",
    "gmail": "gmail",
    "whatsapp": "whatsapp",
    "whatsapp web": "whatsapp",
    "instagram": "instagram",
    "facebook": "facebook",
    "chatgpt": "chatgpt",
    "chat gpt": "chatgpt",
    "claude": "claude",
    "google maps": "maps",
    "maps": "maps",
    "amazon": "amazon",
    "amazon india": "amazon",
    "flipkart": "flipkart",
    "github": "github",
}

FOLDERS = {
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "desktop": Path.home() / "Desktop",
    "pictures": Path.home() / "Pictures",
    "photos": Path.home() / "Pictures",
    "music": Path.home() / "Music",
    "videos": Path.home() / "Videos",
}

WINDOWS_APPS = {
    "chrome": ("chrome.exe",),
    "edge": ("msedge.exe",),
    "notepad": ("notepad.exe",),
    "calculator": ("calc.exe",),
    "paint": ("mspaint.exe",),
    "vscode": ("code.exe", "code"),
    "task_manager": ("taskmgr.exe",),
    "settings": ("ms-settings:",),
    "control_panel": ("control.exe",),
    "snipping_tool": ("SnippingTool.exe",),
    "camera": ("microsoft.windows.camera:",),
    "explorer": ("explorer.exe",),
    "word": ("winword.exe",),
    "excel": ("excel.exe",),
    "powerpoint": ("powerpnt.exe",),
}

WINDOWS_PATHS = {
    "chrome": (
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        / "Google/Chrome/Application/chrome.exe",
    ),
    "edge": (
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        / "Microsoft/Edge/Application/msedge.exe",
    ),
    "vscode": (
        Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        / "Programs/Microsoft VS Code/Code.exe",
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        / "Microsoft VS Code/Code.exe",
    ),
}

for _office_app, _office_executable in (
    ("word", "WINWORD.EXE"),
    ("excel", "EXCEL.EXE"),
    ("powerpoint", "POWERPNT.EXE"),
):
    WINDOWS_PATHS[_office_app] = tuple(
        program_files / office_path / _office_executable
        for program_files in (
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")),
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")),
        )
        for office_path in (
            "Microsoft Office/root/Office16",
            "Microsoft Office/Office16",
            "Microsoft Office/Office15",
        )
    )

WINDOWS_SYSTEM_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "task_manager": "taskmgr.exe",
    "control_panel": "control.exe",
    "snipping_tool": "SnippingTool.exe",
    "explorer": "explorer.exe",
}

WINDOWS_PROCESS_NAMES = {
    "chrome": ("chrome.exe",),
    "edge": ("msedge.exe",),
    "notepad": ("notepad.exe",),
    "paint": ("mspaint.exe",),
    "word": ("winword.exe",),
    "excel": ("excel.exe",),
    "powerpoint": ("powerpnt.exe",),
    "vscode": ("code.exe",),
    "task_manager": ("taskmgr.exe",),
    "control_panel": ("control.exe",),
    "snipping_tool": ("snippingtool.exe",),
    "explorer": ("explorer.exe",),
}

OTHER_COMMANDS = {
    "darwin": {
        "chrome": ("Google Chrome",),
        "edge": ("Microsoft Edge",),
        "notepad": ("TextEdit",),
        "calculator": ("Calculator",),
        "paint": ("Preview",),
        "word": ("Microsoft Word",),
        "excel": ("Microsoft Excel",),
        "powerpoint": ("Microsoft PowerPoint",),
        "vscode": ("Visual Studio Code",),
        "task_manager": ("Activity Monitor",),
        "camera": ("Photo Booth",),
    },
    "linux": {
        "chrome": ("google-chrome", "chromium", "chromium-browser"),
        "edge": ("microsoft-edge", "microsoft-edge-stable"),
        "notepad": ("gedit", "xed", "mousepad", "kate"),
        "calculator": ("gnome-calculator", "kcalc", "galculator"),
        "paint": ("pinta", "kolourpaint"),
        "word": ("libreoffice",),
        "excel": ("libreoffice",),
        "powerpoint": ("libreoffice",),
        "vscode": ("code",),
        "task_manager": ("gnome-system-monitor", "ksysguard"),
        "camera": ("cheese",),
        "explorer": ("nautilus", "dolphin", "thunar"),
    },
}


def _app_key(name):
    normalized = _normalize_alias(name)
    for app_id, aliases in APPS.items():
        if normalized == app_id.replace("_", " ") or normalized in aliases:
            return app_id
    return None


def _normalize_alias(name):
    normalized = name.strip().casefold().replace("-", " ").replace("_", " ")
    return " ".join(normalized.split())


@lru_cache(maxsize=1)
def custom_apps():
    if not CUSTOM_APPS_PATH.is_file():
        return {}
    data = json.loads(CUSTOM_APPS_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("The saved custom-app list is invalid.")
    apps = {}
    for alias, raw_path in data.items():
        if (
            not isinstance(alias, str)
            or not alias.strip()
            or not APP_ALIAS_PATTERN.fullmatch(alias.strip())
            or not isinstance(raw_path, str)
            or len(raw_path) > 1_000
        ):
            raise ValueError("The saved custom-app list has an invalid entry.")
        path = Path(raw_path)
        if not path.is_absolute():
            raise ValueError("Saved custom app paths must be absolute.")
        key = _normalize_alias(alias).replace(" ", "_")
        if key in apps:
            raise ValueError("The saved custom-app list contains duplicate aliases.")
        if _app_key(alias):
            raise ValueError("The saved custom-app list shadows a built-in app alias.")
        apps[key] = path
    return apps


def available_apps():
    return list(APPS) + sorted(alias.replace("_", " ") for alias in custom_apps())


def canonical_app(name):
    if not isinstance(name, str):
        return None
    raw_name = name.strip().casefold()
    custom = custom_apps()
    if raw_name.startswith("custom:"):
        custom_key = _normalize_alias(raw_name[len("custom:"):]).replace(" ", "_")
        return f"custom:{custom_key}" if custom_key in custom else None
    normalized = _normalize_alias(raw_name)
    built_in = _app_key(normalized)
    if built_in:
        return built_in
    custom_key = normalized.replace(" ", "_")
    if custom_key in custom:
        return f"custom:{custom_key}"
    return None


def windows_process_names(name):
    app_id = canonical_app(name)
    if app_id is None:
        raise ValueError(f"{name!r} is not in Aaru's approved app list.")
    if app_id.startswith("custom:"):
        target = custom_apps().get(app_id.split(":", 1)[1])
        if target is None:
            raise FileNotFoundError("The saved custom app is no longer available.")
        return (target.name.casefold(),)
    return WINDOWS_PROCESS_NAMES.get(app_id, ())


def register_custom_app(alias, path):
    if not isinstance(alias, str) or not APP_ALIAS_PATTERN.fullmatch(alias.strip()):
        raise ValueError("Choose an app alias between 1 and 60 characters.")
    key = _normalize_alias(alias)
    if _app_key(key) or key.replace(" ", "_") in custom_apps():
        raise ValueError("That name is already in Aaru's app list.")
    path = Path(path).expanduser().resolve()
    if sys.platform == "win32":
        if path.suffix.casefold() != ".exe" or not path.is_file():
            raise ValueError("On Windows, choose an installed .exe application.")
    elif sys.platform == "darwin":
        if path.suffix.casefold() != ".app" or not path.is_dir():
            raise ValueError("On macOS, choose an installed .app application.")
    elif not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError("Choose an installed executable application.")

    custom = dict(custom_apps())
    custom_alias = key.replace(" ", "_")
    custom[custom_alias] = path
    CUSTOM_APPS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=CUSTOM_APPS_PATH.parent,
            suffix=".tmp",
            delete=False,
        ) as temporary:
            json.dump(
                {name: str(target) for name, target in custom.items()},
                temporary,
                indent=2,
            )
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, CUSTOM_APPS_PATH)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
    custom_apps.cache_clear()
    return key


def _launch(program, *arguments):
    try:
        subprocess.Popen([str(program), *map(str, arguments)], shell=False)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Required application was not found: {program}") from exc


def open_app(name):
    app_id = canonical_app(name)
    if app_id is None:
        raise ValueError(f"{name!r} is not in Aaru's approved app list.")
    if app_id.startswith("custom:"):
        alias = app_id.split(":", 1)[1]
        target = custom_apps().get(alias)
        if target is None or not target.exists():
            raise FileNotFoundError(f"The saved app for {alias!r} is no longer installed.")
        if sys.platform == "darwin":
            _launch("/usr/bin/open", "-a", target)
        else:
            _launch(target)
        return alias.replace("_", " ")

    if sys.platform == "win32":
        target = WINDOWS_APPS.get(app_id)
        if target is None:
            raise FileNotFoundError(f"{name} is not configured for Windows.")
        if target[0].endswith(":"):
            if not hasattr(os, "startfile"):
                raise OSError("Windows application protocol is unavailable.")
            os.startfile(target[0])
            return app_id
        candidates = []
        system_name = WINDOWS_SYSTEM_APPS.get(app_id)
        if system_name:
            system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
            candidates.append(system_root / "System32" / system_name)
        candidates.append(shutil.which(target[0]))
        candidates.extend(WINDOWS_PATHS.get(app_id, ()))
        program = next((candidate for candidate in candidates if candidate and Path(candidate).is_file()), None)
        if program is None:
            raise FileNotFoundError(f"{name} does not appear to be installed.")
        _launch(program)
        return app_id

    if app_id in {"settings", "control_panel", "snipping_tool"}:
        raise NotImplementedError(f"{name} is not available on this operating system.")
    if sys.platform == "darwin":
        app = OTHER_COMMANDS["darwin"].get(app_id)
        if app:
            _launch("/usr/bin/open", "-a", app[0])
            return app_id
    else:
        options = OTHER_COMMANDS["linux"].get(app_id, ())
        program = next((shutil.which(option) for option in options if shutil.which(option)), None)
        if program:
            arguments = []
            if app_id in {"word", "excel", "powerpoint"}:
                arguments.append("--writer" if app_id == "word" else "--calc" if app_id == "excel" else "--impress")
            _launch(program, *arguments)
            return app_id
    raise FileNotFoundError(f"{name} does not appear to be installed.")


def open_folder(name):
    folder_name = name.strip().casefold()
    path = FOLDERS.get(folder_name)
    if path is None:
        raise ValueError("Aaru can open Downloads, Documents, Desktop, Pictures, Music, or Videos.")
    if not path.is_dir():
        raise FileNotFoundError(f"The {folder_name} folder does not exist.")
    if sys.platform == "win32":
        if not hasattr(os, "startfile"):
            raise OSError("The Windows folder opener is unavailable.")
        os.startfile(str(path))
    elif sys.platform == "darwin":
        _launch("/usr/bin/open", path)
    else:
        opener = shutil.which("xdg-open")
        if not opener:
            raise FileNotFoundError("xdg-open was not found.")
        _launch(opener, path)
    return path
