"""Validated action dispatcher. The model can select only named local actions."""

import webbrowser
from urllib.parse import quote_plus

from assistant.models import normalize_plan
from config import MAX_TEXT_FILE_BYTES, SAFE_FILES_DIR
from security.confirmations import ask_for_confirmation, required_confirmation
from security.cybersecurity import get_lesson
from system import apps, controls, information, notes


def _open_browser(url):
    if not webbrowser.open(url):
        raise RuntimeError("No desktop browser accepted the requested web address.")


def execute_plan(client, raw_plan, *, confirm_action=None, output=None):
    plan = normalize_plan(raw_plan)
    action = plan["action"]
    args = plan["args"]
    notify = output or (lambda _text: None)

    if action == "close_app":
        windows = controls.find_app_windows(args["app"])
        if not windows:
            raise FileNotFoundError(f"No open windows were found for {args['app']}.")
        window_list = "\n".join(f"- {window.title}" for window in windows[:8])
        extra_count = len(windows) - 8
        if extra_count > 0:
            window_list += f"\n- and {extra_count} more window(s)"
        description = (
            f"Send a normal close request to {args['app']} window(s):\n{window_list}\n\n"
            "Unsaved-work prompts remain under the app's control; Aaru will not force-close it."
        )
        request = required_confirmation(action, args)
        if (
            request is None
            or confirm_action is None
            or confirm_action(description, request[0]) is not True
        ):
            notify("Action cancel kar diya. Koi change nahi hua.")
            return False
    elif not ask_for_confirmation(confirm_action, action, args):
        notify("Action cancel kar diya. Koi change nahi hua.")
        return False

    if action == "reply":
        notify(args["text"])
    elif action == "open_app":
        app_id = apps.open_app(args["app"])
        notify(f"{app_id.replace('_', ' ').title()} khol diya.")
    elif action == "close_app":
        closed = controls.request_window_close(windows)
        notify(
            f"{args['app'].replace('_', ' ').title()} ko {closed} window(s) "
            "band karne ka request bheja. Unsaved changes ka prompt aa sakta hai."
        )
    elif action == "open_security":
        controls.open_windows_security()
        notify(
            "Windows Security khol diya. Virus & threat protection mein "
            "Quick scan ya Scan options se Full scan chala sakte hain. "
            "Microsoft Defender hi detected threats ko quarantine/remove karega; "
            "Aaru protection settings off nahi karti."
        )
    elif action == "open_site":
        site = apps.SITE_ALIASES.get(args["site"].casefold())
        if site is None:
            raise ValueError("Yeh website approved list mein nahi hai.")
        _open_browser(apps.SITES[site])
        notify(f"{site.title()} khol diya.")
    elif action == "open_url":
        _open_browser(args["url"])
        notify(f"Website kholi: {args['url']}")
    elif action == "web_search":
        _open_browser("https://www.google.com/search?q=" + quote_plus(args["query"]))
        notify(f"Google par search khola: {args['query']}")
    elif action == "youtube_search":
        _open_browser(
            "https://www.youtube.com/results?search_query="
            + quote_plus(args["query"])
        )
        notify(f"YouTube par search khola: {args['query']}")
    elif action == "system_info":
        notify(information.system_text())
    elif action == "battery_info":
        notify(information.battery_text())
    elif action == "date_time":
        notify(information.date_time_text())
    elif action == "open_folder":
        folder = apps.open_folder(args["folder"])
        notify(f"{folder.name} folder khol diya.")
    elif action == "save_note":
        path = notes.save_note(args["title"], args["text"])
        notify(f"Note is device par locally save hua: {path}")
    elif action == "set_volume":
        controls.set_volume(args["percent"])
        notify(f"Volume {args['percent']}% set kiya.")
    elif action == "adjust_volume":
        controls.adjust_volume(args["delta"])
        notify("Volume badal diya.")
    elif action == "toggle_mute":
        controls.toggle_mute()
        notify("Mute setting toggle kar di.")
    elif action == "set_brightness":
        controls.set_brightness(args["percent"])
        notify(f"Brightness {args['percent']}% set ki.")
    elif action == "screenshot":
        path = controls.take_screenshot()
        notify(f"Screenshot device par locally save hua: {path}")
    elif action == "media_control":
        controls.media_control(args["control"])
        notify("Media control bhej diya.")
    elif action == "switch_window":
        controls.switch_window()
        notify("Next open window select ki.")
    elif action == "system_action":
        controls.system_action(args["action"])
        if args["action"] in {"shutdown", "restart"}:
            notify(
                f"{args['action'].title()} 60 seconds mein schedule hua. "
                "Cancel karne ke liye Windows Run mein `shutdown /a` type karein."
            )
        else:
            notify(f"{args['action'].title()} action shuru kiya.")
    elif action == "summarize_file":
        content = notes.safe_text_file(args["path"], SAFE_FILES_DIR)
        if len(content.encode("utf-8")) > MAX_TEXT_FILE_BYTES:
            raise ValueError("Text file is larger than Aaru's safe reading limit.")
        response = client.answer_file_summary(content)
        notify(response)
    elif action == "list_files":
        path = (SAFE_FILES_DIR / args["folder"]).resolve()
        try:
            path.relative_to(SAFE_FILES_DIR.resolve())
        except ValueError as exc:
            raise ValueError("File listing is limited to Aaru AI Files.") from exc
        if not path.is_dir():
            raise FileNotFoundError("The requested Aaru AI Files folder does not exist.")
        names = sorted(child.name for child in path.iterdir())
        notify("\n".join(names) if names else "This folder is empty.")
    elif action == "create_folder":
        path = (SAFE_FILES_DIR / args["path"]).resolve()
        try:
            path.relative_to(SAFE_FILES_DIR.resolve())
        except ValueError as exc:
            raise ValueError("New folders are limited to Aaru AI Files.") from exc
        if path.exists():
            raise FileExistsError("That folder already exists.")
        path.mkdir(parents=True)
        notify(f"Folder created locally: {path}")
    elif action == "move_file":
        source = (SAFE_FILES_DIR / args["source"]).resolve()
        destination_folder = (SAFE_FILES_DIR / args["destination_folder"]).resolve()
        for path in (source, destination_folder):
            try:
                path.relative_to(SAFE_FILES_DIR.resolve())
            except ValueError as exc:
                raise ValueError("File moves are limited to Aaru AI Files.") from exc
        if not source.is_file() or not destination_folder.is_dir():
            raise FileNotFoundError("The source file or destination folder was not found.")
        destination = destination_folder / source.name
        if destination.exists():
            raise FileExistsError("A file with that name already exists at the destination.")
        source.rename(destination)
        notify("File moved locally.")
    elif action == "cybersecurity_lesson":
        notify(get_lesson(args["topic"]))
    else:
        raise ValueError("Aaru does not implement this action.")
    return True
