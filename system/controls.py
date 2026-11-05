"""Fixed, narrow controls for volume, brightness, media, and screenshots."""

import ctypes
import os
import shutil
import subprocess
import sys
from typing import NamedTuple
from pathlib import Path

import pyautogui
import psutil

from config import SAFE_FILES_DIR, ensure_user_directories
from system.apps import windows_process_names


class WindowTarget(NamedTuple):
    handle: int
    title: str
    process_id: int
    process_name: str


def _fixed_command(name, *arguments):
    executable = shutil.which(name)
    if not executable:
        raise NotImplementedError(f"{name} is not installed on this device.")
    subprocess.run([executable, *map(str, arguments)], check=True, shell=False)


def set_volume(percent):
    if isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 100:
        raise ValueError("Volume must be an integer from 0 to 100.")
    if sys.platform == "win32":
        from pycaw.pycaw import AudioUtilities

        AudioUtilities.GetSpeakers().EndpointVolume.SetMasterVolumeLevelScalar(
            percent / 100, None
        )
    elif sys.platform == "darwin":
        _fixed_command("osascript", "-e", f"set volume output volume {percent}")
    else:
        _fixed_command("pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{percent}%")


def adjust_volume(delta):
    if isinstance(delta, bool) or not isinstance(delta, int) or not -100 <= delta <= 100:
        raise ValueError("Volume adjustment must be an integer from -100 to 100.")
    if sys.platform == "win32":
        from pycaw.pycaw import AudioUtilities

        endpoint = AudioUtilities.GetSpeakers().EndpointVolume
        current = endpoint.GetMasterVolumeLevelScalar()
        endpoint.SetMasterVolumeLevelScalar(
            min(1.0, max(0.0, current + delta / 100)), None
        )
    elif sys.platform == "darwin":
        executable = shutil.which("osascript")
        if not executable:
            raise NotImplementedError("osascript is not installed on this device.")
        current = subprocess.run(
            [executable, "-e", "output volume of (get volume settings)"],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )
        percent = min(100, max(0, int(current.stdout.strip()) + delta))
        set_volume(percent)
    else:
        change = f"{'+' if delta >= 0 else '-'}{abs(delta)}%"
        _fixed_command("pactl", "set-sink-volume", "@DEFAULT_SINK@", change)


def toggle_mute():
    if sys.platform == "win32":
        from pycaw.pycaw import AudioUtilities

        endpoint = AudioUtilities.GetSpeakers().EndpointVolume
        endpoint.SetMute(not endpoint.GetMute(), None)
    elif sys.platform == "darwin":
        _fixed_command(
            "osascript",
            "-e",
            "set volume output muted not (output muted of (get volume settings))",
        )
    else:
        _fixed_command("pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle")


def set_brightness(percent):
    if isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 100:
        raise ValueError("Brightness must be an integer from 0 to 100.")
    try:
        import screen_brightness_control

        screen_brightness_control.set_brightness(percent)
    except Exception as exc:
        raise RuntimeError(
            "Brightness control is unsupported by this display or permission setup."
        ) from exc


def media_control(control):
    keys = {"play_pause": "playpause", "next": "nexttrack", "previous": "prevtrack"}
    key = keys.get(control)
    if key is None:
        raise ValueError("This media key is not available.")
    pyautogui.press(key)


def switch_window():
    if sys.platform == "darwin":
        pyautogui.hotkey("command", "tab")
    else:
        pyautogui.hotkey("alt", "tab")


def open_windows_security():
    if sys.platform != "win32" or not hasattr(os, "startfile"):
        raise NotImplementedError("Windows Security is available only on Windows.")
    os.startfile("windowsdefender://threat")


def find_app_windows(app):
    if sys.platform != "win32":
        raise NotImplementedError("Closing an app window is currently supported only on Windows.")
    process_names = set(windows_process_names(app))
    if not process_names:
        raise NotImplementedError(
            "Aaru cannot safely identify windows for this app. "
            "Try a supported desktop app such as Chrome, Notepad, or VS Code."
        )

    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    enum_windows = user32.EnumWindows
    enum_windows.argtypes = (
        ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM),
        wintypes.LPARAM,
    )
    enum_windows.restype = wintypes.BOOL
    is_window_visible = user32.IsWindowVisible
    is_window_visible.argtypes = (wintypes.HWND,)
    is_window_visible.restype = wintypes.BOOL
    get_window_text_length = user32.GetWindowTextLengthW
    get_window_text_length.argtypes = (wintypes.HWND,)
    get_window_text_length.restype = ctypes.c_int
    get_window_text = user32.GetWindowTextW
    get_window_text.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    get_window_text.restype = ctypes.c_int
    get_window_thread_process_id = user32.GetWindowThreadProcessId
    get_window_thread_process_id.argtypes = (
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    )
    get_window_thread_process_id.restype = wintypes.DWORD

    windows = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def collect_window(handle, _parameter):
        if not is_window_visible(handle):
            return True
        length = get_window_text_length(handle)
        if length <= 0:
            return True
        title_buffer = ctypes.create_unicode_buffer(length + 1)
        get_window_text(handle, title_buffer, len(title_buffer))
        title = title_buffer.value.strip()
        if not title:
            return True
        process_id = wintypes.DWORD()
        get_window_thread_process_id(handle, ctypes.byref(process_id))
        if not process_id.value or process_id.value == os.getpid():
            return True
        try:
            process_name = psutil.Process(process_id.value).name().casefold()
        except (psutil.Error, OSError):
            return True
        if process_name in process_names:
            windows.append(
                WindowTarget(
                    int(handle),
                    title[:200],
                    process_id.value,
                    process_name,
                )
            )
        return True

    if not enum_windows(collect_window, 0):
        error = ctypes.get_last_error()
        if error:
            raise OSError(error, "Windows could not enumerate open app windows.")
    return windows


def request_window_close(windows):
    if sys.platform != "win32":
        raise NotImplementedError("Closing an app window is currently supported only on Windows.")

    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    is_window = user32.IsWindow
    is_window.argtypes = (wintypes.HWND,)
    is_window.restype = wintypes.BOOL
    post_message = user32.PostMessageW
    post_message.argtypes = (
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    )
    post_message.restype = wintypes.BOOL
    closed = 0
    for window in windows:
        if not is_window(window.handle):
            continue
        try:
            current_name = psutil.Process(window.process_id).name().casefold()
        except (psutil.Error, OSError):
            continue
        if current_name != window.process_name:
            continue
        if not post_message(window.handle, 0x0010, 0, 0):
            error = ctypes.get_last_error()
            raise OSError(error, f"Windows could not request closing {window.title!r}.")
        closed += 1
    if closed == 0:
        raise RuntimeError("The selected app window closed or changed before Aaru could reach it.")
    return closed


def take_screenshot():
    ensure_user_directories()
    folder = SAFE_FILES_DIR / "Screenshots"
    folder.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    from PIL import ImageGrab

    path = folder / f"screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.png"
    ImageGrab.grab().save(path)
    return path


def system_action(action):
    if sys.platform != "win32":
        raise NotImplementedError(
            f"{action} is not implemented for this operating system. "
            "No terminal command was run."
        )

    if action == "lock":
        if not ctypes.windll.user32.LockWorkStation():
            raise OSError("Windows could not lock this computer.")
    elif action in {"shutdown", "restart"}:
        command = (
            Path(os.environ.get("SystemRoot", r"C:\Windows"))
            / "System32"
            / "shutdown.exe"
        )
        if not command.is_file():
            raise FileNotFoundError(f"Windows power utility was not found: {command}")
        mode = "/s" if action == "shutdown" else "/r"
        subprocess.run([command, mode, "/t", "60"], check=True, shell=False)
    elif action == "sleep":
        result = ctypes.windll.powrprof.SetSuspendState(False, True, False)
        if result == 0:
            raise OSError("Windows could not put this computer to sleep.")
    else:
        raise ValueError("This system action is not available.")
