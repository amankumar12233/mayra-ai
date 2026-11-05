"""Read-only local system information."""

from datetime import datetime
import platform

import psutil


def date_time_text():
    return datetime.now().astimezone().strftime("%A, %d %B %Y, %I:%M %p %Z")


def battery_text():
    battery = psutil.sensors_battery()
    if battery is None:
        return "Battery information is not available on this device."
    charging = "charging" if battery.power_plugged else "not charging"
    return f"Battery: {battery.percent:.0f}% ({charging})."


def system_text():
    memory = psutil.virtual_memory()
    return (
        f"System: {platform.system()} {platform.release()} ({platform.machine()})\n"
        f"Processor: {platform.processor() or 'Not reported'}\n"
        f"Memory: {memory.total // (1024 ** 3)} GB total, "
        f"{memory.available // (1024 ** 3)} GB available."
    )
