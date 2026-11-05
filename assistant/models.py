"""Validation boundary between model output and local computer actions."""

from urllib.parse import urlsplit

from system.apps import FOLDERS, SITE_ALIASES, SITES, canonical_app


ACTION_FIELDS = {
    "reply": {"text"},
    "open_app": {"app"},
    "close_app": {"app"},
    "open_security": set(),
    "open_site": {"site"},
    "open_url": {"url"},
    "web_search": {"query"},
    "youtube_search": {"query"},
    "system_info": set(),
    "battery_info": set(),
    "date_time": set(),
    "open_folder": {"folder"},
    "save_note": {"title", "text"},
    "set_volume": {"percent"},
    "adjust_volume": {"delta"},
    "toggle_mute": set(),
    "set_brightness": {"percent"},
    "screenshot": set(),
    "media_control": {"control"},
    "switch_window": set(),
    "system_action": {"action"},
    "summarize_file": {"path"},
    "list_files": {"folder"},
    "create_folder": {"path"},
    "move_file": {"source", "destination_folder"},
    "cybersecurity_lesson": {"topic"},
}

SAFE_TEXT_LIMIT = 500


def _require_text(args, key, *, max_length=SAFE_TEXT_LIMIT):
    value = args.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise ValueError(f"Invalid or missing '{key}' value.")
    return value.strip()


def normalize_plan(plan):
    if not isinstance(plan, dict):
        raise ValueError("Assistant returned an invalid action plan.")
    action = plan.get("action")
    args = plan.get("args")
    if not isinstance(action, str) or action not in ACTION_FIELDS:
        raise ValueError("This action is not available in Aaru.")
    if not isinstance(args, dict):
        raise ValueError("Assistant returned invalid action arguments.")
    if set(args) != ACTION_FIELDS[action]:
        raise ValueError("Assistant returned unexpected action arguments.")

    clean = dict(args)
    if action == "reply":
        clean["text"] = _require_text(args, "text", max_length=4_000)
    elif action in {"open_app", "close_app"}:
        app_id = canonical_app(_require_text(args, "app", max_length=100))
        if app_id is None:
            raise ValueError("This application is not in Aaru's approved app list.")
        clean["app"] = app_id
    elif action == "open_site":
        site = _require_text(args, "site", max_length=100).casefold()
        site_id = SITE_ALIASES.get(site, site)
        if site_id not in SITES:
            raise ValueError("This website is not in Aaru's approved website list.")
        clean["site"] = site_id
    elif action == "open_folder":
        folder = _require_text(args, "folder", max_length=100).casefold()
        if folder not in FOLDERS:
            raise ValueError("This folder is not in Aaru's approved folder list.")
        clean["folder"] = folder
    elif action == "list_files":
        folder = _require_text(args, "folder", max_length=240)
        clean["folder"] = _safe_workspace_path(folder)
    elif action == "create_folder":
        clean["path"] = _safe_workspace_path(_require_text(args, "path", max_length=240))
    elif action == "move_file":
        clean["source"] = _safe_workspace_path(_require_text(args, "source", max_length=240))
        clean["destination_folder"] = _safe_workspace_path(
            _require_text(args, "destination_folder", max_length=240)
        )
    elif action in {"media_control", "system_action", "cybersecurity_lesson"}:
        key = next(iter(ACTION_FIELDS[action]))
        clean[key] = _require_text(args, key, max_length=100)
    elif action == "open_url":
        clean["url"] = _require_text(args, "url")
    elif action in {"web_search", "youtube_search"}:
        clean["query"] = _require_text(args, "query")
    elif action == "save_note":
        clean["title"] = _require_text(args, "title", max_length=80)
        clean["text"] = _require_text(args, "text", max_length=20_000)
    elif action in {"set_volume", "set_brightness"}:
        percent = args.get("percent")
        if isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 100:
            raise ValueError("Percent must be an integer from 0 to 100.")
    elif action == "adjust_volume":
        delta = args.get("delta")
        if isinstance(delta, bool) or not isinstance(delta, int) or not -100 <= delta <= 100:
            raise ValueError("Volume adjustment must be an integer from -100 to 100.")
    elif action == "summarize_file":
        clean["path"] = _safe_workspace_path(
            _require_text(args, "path", max_length=240)
        )

    if action == "media_control" and clean["control"] not in {"play_pause", "next", "previous"}:
        raise ValueError("This media control is not available.")
    if action == "system_action" and clean["action"] not in {"lock", "sleep", "shutdown", "restart"}:
        raise ValueError("This system action is not available.")
    if action == "cybersecurity_lesson" and clean["topic"] not in {
        "fundamentals", "linux", "networking", "nmap", "wireshark",
        "wifi", "cctv", "passwords", "privacy", "labs",
    }:
        raise ValueError("This cybersecurity lesson is not available.")
    if action == "open_url":
        candidate = clean["url"]
        parsed = urlsplit(candidate)
        if parsed.scheme and parsed.scheme not in {"http", "https"}:
            raise ValueError("Only ordinary HTTP/HTTPS website links can be opened.")
        if not parsed.scheme:
            candidate = f"https://{candidate}"
            clean["url"] = candidate
            parsed = urlsplit(candidate)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise ValueError("Only ordinary HTTP/HTTPS website links can be opened.")
    return {"action": action, "args": clean, "message": str(plan.get("message", ""))[:500]}


def _safe_workspace_path(value):
    from pathlib import Path

    candidate = Path(value)
    if candidate.is_absolute() or any(part == ".." for part in candidate.parts):
        raise ValueError("File actions are limited to relative paths inside Aaru AI Files.")
    if not value.strip() or len(value) > 240:
        raise ValueError("Invalid Aaru AI Files path.")
    return value
