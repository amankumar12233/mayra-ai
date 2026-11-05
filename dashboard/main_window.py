"""Aarohi AI (Aaru) desktop dashboard and explicit microphone controls."""

import math
import queue
import sys
import threading
import time
import tkinter as tk
from collections import deque
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

import psutil
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageTk

from assistant.conversation import ConversationService
from assistant.speech_output import SpeechOutput
from assistant.voice_engine import OfflineVoiceEngine
from config import APP_DIR, APP_NAME, load_settings, save_settings
from system.actions import execute_plan
from system.apps import register_custom_app


PALETTES = {
    "dark": {
        "background": "#020408", "panel": "#041322", "foreground": "#ddfaff",
        "muted": "#4facfe", "accent": "#00f2fe", "input": "#030b13",
        "border": "#0a5364", "accent_soft": "#082534", "green": "#62d9ec",
    },
    "light": {
        "background": "#eaf3f8", "panel": "#f8fcff", "foreground": "#102638",
        "muted": "#567184", "accent": "#008eae", "input": "#ffffff",
        "border": "#c5dce8", "accent_soft": "#d9f1f8", "green": "#138b6a",
    },
}
WALLPAPER_ANIMATION_INTERVAL_MS = 20


def _render_animated_wallpaper(image, elapsed):
    width, height = image.size
    scale = max(width / 1920, height / 1080)
    center_x, center_y = width / 2, height / 2
    outer_radius = 222 * 1.08 * scale
    glow_radius = max(1, 3 * scale)
    padding = math.ceil(glow_radius * 3 + 3 * scale)
    local_center = outer_radius + padding
    overlay_size = math.ceil(local_center * 2)
    left = round(center_x - local_center)
    top = round(center_y - local_center)
    overlay = Image.new("RGBA", (overlay_size, overlay_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    outer_box = (
        local_center - outer_radius,
        local_center - outer_radius,
        local_center + outer_radius,
        local_center + outer_radius,
    )
    outer_angle = (elapsed * 18) % 360
    for offset in range(0, 360, 90):
        start = outer_angle + offset
        draw.arc(
            outer_box,
            start,
            start + 30,
            fill=(0, 242, 254, 220),
            width=max(1, round(2.5 * scale)),
        )

    inner_radius = 212 * 1.08 * scale
    inner_box = (
        local_center - inner_radius,
        local_center - inner_radius,
        local_center + inner_radius,
        local_center + inner_radius,
    )
    inner_angle = (-elapsed * 30) % 360
    for offset in range(0, 360, 45):
        start = inner_angle + offset
        draw.arc(
            inner_box,
            start,
            start + 13,
            fill=(79, 172, 254, 210),
            width=max(1, round(2 * scale)),
        )

    glow = overlay.filter(ImageFilter.GaussianBlur(glow_radius))
    frame = image.convert("RGBA")
    ring_region = frame.crop(
        (left, top, left + overlay_size, top + overlay_size)
    )
    ring_region.alpha_composite(glow)
    ring_region.alpha_composite(overlay)
    frame.paste(ring_region, (left, top))
    return frame.convert("RGB")


class AaruDashboard:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.service = ConversationService(self.settings)
        self.speech_output = SpeechOutput()
        self.events = queue.Queue()
        self.history = []
        self.stat_history = {
            "cpu": deque([0] * 24, maxlen=24),
            "memory": deque([0] * 24, maxlen=24),
            "battery": deque([0] * 24, maxlen=24),
        }
        self.telemetry_panels = []
        self.telemetry_labels = {}
        self.wallpaper_source = None
        self.wallpaper_photo = None
        self.wallpaper_base_image = None
        self.wallpaper_base_size = None
        self.wallpaper_animated = False
        self.wallpaper_animation_start = time.monotonic()
        self.wallpaper_animation_job = None
        self.avatar_photo = None
        self.wallpaper_resize_job = None
        self.busy = False
        self.ptt_active = False
        self.voice_chat_active = False
        self.voice_state = "idle"
        self.voice_orb_phase = 0.0
        self.voice_chat_turn = None
        self.voice_engine = OfflineVoiceEngine(
            on_command=lambda text: self.events.put(("voice_command", text)),
            on_status=lambda text: self.events.put(("status", text)),
        )
        self.palette = PALETTES.get(self.settings["theme"], PALETTES["dark"])
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self._process_events)
        self.root.after(1000, self._update_clock)
        self.root.after(600, self._update_telemetry)
        self.root.after(100, self._animate_voice_orb)

    def _build_ui(self):
        self.root.title(f"{APP_NAME} | Aaru")
        window_icon_path = APP_DIR / "aaru.ico"
        if sys.platform == "win32" and window_icon_path.is_file():
            self.root.iconbitmap(str(window_icon_path))
        self.root.geometry("1280x720")
        self.root.minsize(1000, 600)
        if sys.platform == "win32":
            self.root.state("zoomed")
        self.root.configure(bg=self.palette["background"])
        self.wallpaper_label = tk.Label(
            self.root, bd=0, highlightthickness=0, bg=self.palette["background"]
        )
        self.root.bind("<Configure>", self._schedule_wallpaper_resize)
        wallpaper_path = self.settings.get("wallpaper_path") or str(
            APP_DIR / "aaru_wallpaper.png"
        )
        if wallpaper_path:
            try:
                self._load_wallpaper(wallpaper_path)
            except (OSError, ValueError) as exc:
                messagebox.showwarning(
                    "Wallpaper unavailable",
                    f"Could not load the saved wallpaper:\n{exc}",
                    parent=self.root,
                )
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self._apply_theme()

        self.chat_screen = tk.Frame(self.root, bg=self.palette["background"])
        self.chat_wallpaper_label = tk.Label(
            self.chat_screen,
            bd=0,
            highlightthickness=0,
            bg=self.palette["background"],
        )
        self.chat_wallpaper_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.chat_wallpaper_label.lower()
        shell = self.chat_screen
        self.shell = shell
        header = ttk.Frame(shell, style="Panel.TFrame", padding=(18, 12))
        header.pack(fill="x", padx=12, pady=(12, 7))
        icon_path = APP_DIR / "aaru-preview.png"
        self.icon_image = None
        if icon_path.is_file():
            try:
                self.icon_image = tk.PhotoImage(file=str(icon_path))
                self.icon_image = self.icon_image.subsample(4, 4)
                ttk.Label(header, image=self.icon_image, style="Panel.TLabel").pack(
                    side="left", padx=(0, 14)
                )
                self.root.iconphoto(True, self.icon_image)
            except tk.TclError:
                self.icon_image = None
        title_box = ttk.Frame(header, style="Panel.TFrame")
        title_box.pack(side="left", fill="x", expand=True)
        ttk.Label(
            title_box,
            text="AARU CORE  /  PERSONAL INTELLIGENCE",
            style="Eyebrow.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            title_box, text="Aarohi AI", style="Title.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            title_box,
            text="HUD CHAT  •  HINDI / ENGLISH  •  PRIVACY-FIRST",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 0))
        ttk.Label(
            title_box,
            text="CREATED BY KRISHNA KANT  •  MADE IN INDIA",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(3, 0))
        self.avatar_label = ttk.Label(header, style="Panel.TLabel")
        self.avatar_label.pack(side="right", padx=(8, 0))
        avatar_path = self.settings.get("assistant_icon_path", "")
        if avatar_path:
            try:
                self._load_avatar(avatar_path)
            except (OSError, ValueError) as exc:
                messagebox.showwarning(
                    "Assistant icon unavailable",
                    f"Could not load the saved assistant icon:\n{exc}",
                    parent=self.root,
                )
        self.header_clock = tk.StringVar(value="SYSTEM CLOCK")
        ttk.Label(header, textvariable=self.header_clock, style="Clock.TLabel").pack(
            side="right", padx=(8, 14)
        )
        self.mic_status = ttk.Label(
            header,
            text="●  MIC OFF",
            style="MicOff.TLabel",
            padding=(10, 6),
        )
        self.mic_status.pack(side="right", padx=(8, 0))

        telemetry = ttk.Frame(shell, style="TFrame")
        telemetry.pack(fill="x", padx=12, pady=(0, 7))
        self.telemetry_cards = {}
        self.telemetry_charts = {}
        for column, (key, title, unit) in enumerate(
            (("cpu", "PROCESSOR", "%"), ("memory", "MEMORY", "%"), ("battery", "BATTERY", "%"))
        ):
            card = tk.Frame(
                telemetry, bg=self.palette["panel"], highlightthickness=1,
                highlightbackground=self.palette["border"],
            )
            card.grid(row=0, column=column, sticky="nsew", padx=4)
            self.telemetry_panels.append(card)
            telemetry.columnconfigure(column, weight=1)
            title_label = tk.Label(
                card, text=title, bg=self.palette["panel"], fg=self.palette["muted"],
                font=("Consolas", 9, "bold"), anchor="w",
            )
            title_label.pack(fill="x", padx=12, pady=(9, 0))
            value = tk.StringVar(value="--")
            value_label = tk.Label(
                card, textvariable=value, bg=self.palette["panel"],
                fg=self.palette["accent"], font=("Consolas", 18, "bold"), anchor="w",
            )
            value_label.pack(fill="x", padx=12)
            self.telemetry_cards[key] = (value, unit)
            self.telemetry_labels[key] = (title_label, value_label)
            chart = tk.Canvas(
                card, height=30, bg=self.palette["panel"], highlightthickness=0,
            )
            chart.pack(fill="x", padx=10, pady=(0, 7))
            self.telemetry_charts[key] = chart

        toolbar = ttk.Frame(shell, style="Panel.TFrame", padding=(9, 8))
        toolbar.pack(fill="x", padx=12, pady=4)
        self.start_button = ttk.Button(
            toolbar,
            text="▶  START VOICE CHAT",
            command=self.start_voice_chat,
            style="Voice.TButton",
        )
        self.start_button.pack(side="left", padx=4)
        self.stop_button = ttk.Button(
            toolbar, text="■  STOP", command=self.stop_wake_word, state="disabled"
        )
        self.stop_button.pack(side="left", padx=4)
        self.speak_button = ttk.Button(
            toolbar, text="◉  SPEAK ONCE", command=self.listen_once
        )
        self.speak_button.pack(side="left", padx=4)
        ttk.Label(toolbar, text="AI CORE", style="Eyebrow.TLabel").pack(
            side="left", padx=(14, 6)
        )
        self.provider_var = tk.StringVar(value=self.settings["provider"])
        provider = ttk.Combobox(
            toolbar,
            textvariable=self.provider_var,
            values=("offline", "ollama", "openai", "openrouter"),
            state="readonly",
            width=11,
        )
        provider.pack(side="left")
        provider.bind("<<ComboboxSelected>>", self._change_provider)
        ttk.Label(toolbar, text="Model:", style="Panel.TLabel").pack(
            side="left", padx=(10, 4)
        )
        self.model_var = tk.StringVar(value=self._configured_model())
        model = ttk.Entry(toolbar, textvariable=self.model_var, width=17)
        model.pack(side="left")
        model.bind("<FocusOut>", self._change_model)
        model.bind("<Return>", self._change_model)
        self.voice_enabled = tk.BooleanVar(value=self.settings["voice_enabled"])
        ttk.Checkbutton(
            toolbar,
            text="Speak answers",
            variable=self.voice_enabled,
            command=self._change_voice,
        ).pack(side="left", padx=(10, 0))
        ttk.Button(toolbar, text="ADD APP", command=self.add_custom_app).pack(
            side="right", padx=4
        )
        ttk.Button(toolbar, text="CLEAR LOG", command=self.clear_chat).pack(
            side="right", padx=4
        )
        ttk.Button(toolbar, text="LIGHT / DARK", command=self.toggle_theme).pack(
            side="right", padx=4
        )
        appearance_menu = tk.Menu(self.root, tearoff=False)
        appearance_menu.add_command(
            label="Choose wallpaper…", command=self.choose_wallpaper
        )
        appearance_menu.add_command(
            label="Choose assistant icon…", command=self.choose_assistant_icon
        )
        appearance_menu.add_command(
            label="Reset wallpaper", command=self.reset_wallpaper
        )
        appearance_menu.add_command(
            label="Reset assistant icon", command=self.reset_assistant_icon
        )
        appearance_button = ttk.Menubutton(
            toolbar, text="APPEARANCE", menu=appearance_menu
        )
        appearance_button.pack(side="right", padx=4)
        ttk.Button(
            toolbar,
            text="⌂ HOME",
            command=self.show_home_screen,
        ).pack(side="right", padx=4)

        status_panel = ttk.Frame(shell, style="Panel.TFrame", padding=(12, 7))
        status_panel.pack(fill="x", padx=12, pady=4)
        self.status_var = tk.StringVar(value="SYSTEM READY  /  MIC DISABLED")
        self.voice_orb = tk.Canvas(
            status_panel,
            width=42,
            height=30,
            bg=self.palette["panel"],
            highlightthickness=0,
        )
        self.voice_orb.pack(side="left", padx=(0, 8))
        self._draw_voice_orb()
        ttk.Label(status_panel, textvariable=self.status_var, style="Status.TLabel").pack(
            side="left", fill="x", expand=True
        )
        self.clock_var = tk.StringVar(value="")
        ttk.Label(status_panel, textvariable=self.clock_var, style="Clock.TLabel").pack(
            side="right"
        )

        self.chat_console = tk.Frame(
            shell,
            bg=self.palette["panel"],
            highlightthickness=1,
            highlightbackground=self.palette["accent"],
        )
        self.chat_console.configure(width=620)
        self.chat_console.pack_propagate(False)
        self.chat_console.pack(
            side="right", fill="both", padx=(4, 12), pady=(4, 10)
        )
        tk.Label(
            self.chat_console,
            text="COMMUNICATION LINK  //  LIVE CHAT",
            bg=self.palette["panel"],
            fg=self.palette["accent"],
            font=("Consolas", 10, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(11, 6))
        self.chat = ScrolledText(
            self.chat_console,
            wrap="word",
            state="disabled",
            height=8,
            relief="solid",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self.palette["border"],
            highlightcolor=self.palette["accent"],
            padx=14,
            pady=12,
            font=("Segoe UI", 10),
            insertbackground=self.palette["foreground"],
        )
        self.chat.pack(fill="both", expand=True, padx=(10, 4), pady=(0, 6))
        self._style_chat()
        self.chat.vbar.configure(
            bg=self.palette["panel"],
            troughcolor=self.palette["input"],
            activebackground=self.palette["accent"],
            highlightthickness=0,
            relief="flat",
            bd=0,
        )
        self._append_message(
            "Aarohi",
            "SYSTEM ONLINE  //  Aapka message yahan se start hoga. "
            "Neeche type karein ya voice controls use karein.",
            add_history=False,
        )
        self._append_message(
            "SECURITY",
            "Voice chat mein mic active rahega jab tak aap Stop na dabayein. "
            "Audio aur speech recognition device par process hote hain; cloud AI "
            "chunne par pehchana hua text us provider ko bheja jaata hai. "
            "Jawab bolne ke liye Google ki online speech service use hoti hai. "
            "Voice authentication nahi hai; lock, shutdown, restart, sleep aur "
            "file changes ke liye typed confirmation zaroori hai.",
            add_history=False,
        )

        input_panel = ttk.Frame(self.chat_console, style="Panel.TFrame", padding=(8, 8))
        input_panel.pack(fill="x", padx=8, pady=(0, 8))
        self.entry = ttk.Entry(input_panel, font=("Consolas", 11))
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.entry.bind("<Return>", self.send_text)
        self.entry.bind("<Control-Return>", self.send_text)
        self.send_button = ttk.Button(
            input_panel, text="TRANSMIT  ➤", command=self.send_text
        )
        self.send_button.pack(side="right", padx=4)

        self.open_button = ttk.Button(
            self.root,
            text="OPEN AARU  →",
            command=self.show_conversation_screen,
            style="Voice.TButton",
        )
        self.open_button.place(relx=0.5, rely=0.87, anchor="center")
        self.open_button.lift()
        self.screen = "home"
        self._resize_wallpaper()

    def show_conversation_screen(self):
        if self.screen == "chat":
            return
        self.open_button.place_forget()
        self.chat_screen.pack(fill="both", expand=True)
        self.screen = "chat"
        self._resize_wallpaper()
        self.entry.focus_set()

    def show_home_screen(self):
        if self.voice_chat_active or self.voice_engine.listening:
            self.stop_wake_word()
        self.chat_screen.pack_forget()
        self.open_button.place(relx=0.5, rely=0.87, anchor="center")
        self.open_button.lift()
        self.screen = "home"

    def _apply_theme(self):
        p = self.palette
        self.root.configure(bg=p["background"])
        if hasattr(self, "shell"):
            self.shell.configure(
                bg=p["background"], highlightbackground=p["border"]
            )
        if hasattr(self, "chat_screen"):
            self.chat_screen.configure(bg=p["background"])
        self.style.configure("TFrame", background=p["background"])
        self.style.configure(
            "Panel.TFrame",
            background=p["panel"],
            bordercolor=p["border"],
            lightcolor=p["accent"],
            darkcolor=p["border"],
            borderwidth=1,
            relief="solid",
        )
        self.style.configure(
            "TLabel", background=p["background"], foreground=p["foreground"]
        )
        self.style.configure(
            "Panel.TLabel", background=p["panel"], foreground=p["foreground"]
        )
        self.style.configure(
            "Title.TLabel",
            background=p["panel"],
            foreground=p["accent"],
            font=("Consolas", 20, "bold"),
        )
        self.style.configure(
            "Eyebrow.TLabel",
            background=p["panel"],
            foreground=p["muted"],
            font=("Consolas", 9, "bold"),
        )
        self.style.configure(
            "Clock.TLabel",
            background=p["panel"],
            foreground=p["green"],
            font=("Consolas", 10, "bold"),
        )
        self.style.configure(
            "Muted.TLabel", background=p["panel"], foreground=p["muted"]
        )
        self.style.configure(
            "Status.TLabel",
            background=p["panel"],
            foreground=p["accent"],
            font=("Consolas", 10, "bold"),
        )
        self.style.configure(
            "MicOff.TLabel",
            background=p["panel"],
            foreground=p["muted"],
            font=("Consolas", 9, "bold"),
        )
        self.style.configure(
            "MicOn.TLabel",
            background=p["panel"],
            foreground=p["green"],
            font=("Consolas", 9, "bold"),
        )
        self.style.configure(
            "TButton", background=p["accent_soft"], foreground=p["accent"],
            padding=(9, 6), borderwidth=1, relief="solid",
            bordercolor=p["border"], font=("Consolas", 9, "bold"),
        )
        self.style.map(
            "TButton",
            background=[
                ("disabled", p["panel"]), ("active", p["accent"]),
                ("pressed", p["accent"]),
            ],
            foreground=[("disabled", p["muted"]), ("active", p["background"])],
        )
        self.style.configure(
            "Voice.TButton",
            background=p["accent"],
            foreground="#07111d" if self.settings["theme"] == "dark" else "#ffffff",
            padding=(11, 7),
            font=("Consolas", 10, "bold"),
            borderwidth=1,
            bordercolor=p["accent"],
            relief="solid",
        )
        self.style.map(
            "Voice.TButton",
            background=[
                ("disabled", p["accent_soft"]),
                ("active", p["green"]),
                ("pressed", p["green"]),
            ],
            foreground=[("disabled", p["muted"])],
        )
        self.style.configure(
            "TEntry",
            fieldbackground=p["input"],
            foreground=p["foreground"],
            insertcolor=p["foreground"],
            bordercolor=p["border"],
            lightcolor=p["border"],
            darkcolor=p["border"],
            borderwidth=1,
            padding=(8, 6),
        )
        self.style.configure(
            "TCheckbutton", background=p["panel"], foreground=p["accent"],
            font=("Consolas", 9),
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=p["input"],
            foreground=p["foreground"],
            background=p["panel"],
            arrowcolor=p["accent"],
            bordercolor=p["border"],
            lightcolor=p["accent"],
            darkcolor=p["border"],
            font=("Consolas", 9),
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", p["input"])],
            foreground=[("readonly", p["accent"])],
            selectbackground=[("readonly", p["input"])],
            selectforeground=[("readonly", p["accent"])],
        )
        self.style.configure(
            "TMenubutton",
            background=p["accent_soft"],
            foreground=p["accent"],
            padding=(8, 6),
            bordercolor=p["border"],
            lightcolor=p["accent"],
            darkcolor=p["border"],
            borderwidth=1,
            relief="solid",
            font=("Consolas", 9, "bold"),
        )
        self.style.map(
            "TMenubutton",
            background=[("active", p["accent"]), ("pressed", p["accent"])],
            foreground=[("active", p["background"]), ("pressed", p["background"])],
        )
        if hasattr(self, "chat"):
            self._style_chat()
        if hasattr(self, "chat_console"):
            self.chat_console.configure(
                bg=p["panel"], highlightbackground=p["accent"]
            )
            self.chat.vbar.configure(
                bg=p["panel"],
                troughcolor=p["input"],
                activebackground=p["accent"],
            )
        for panel in getattr(self, "telemetry_panels", ()):
            panel.configure(bg=p["panel"], highlightbackground=p["border"])
            for child in panel.winfo_children():
                if isinstance(child, tk.Canvas):
                    child.configure(bg=p["panel"])
        for title_label, value_label in getattr(self, "telemetry_labels", {}).values():
            title_label.configure(bg=p["panel"], fg=p["muted"])
            value_label.configure(bg=p["panel"], fg=p["accent"])
        for key in getattr(self, "telemetry_charts", {}):
            self._draw_sparkline(key)
        if hasattr(self, "voice_orb"):
            self.voice_orb.configure(bg=p["panel"])
            self._draw_voice_orb()

    def _draw_voice_orb(self):
        if not hasattr(self, "voice_orb"):
            return
        canvas = self.voice_orb
        canvas.delete("all")
        center_x, center_y = 21, 15
        active = self.voice_state in {"listening", "thinking", "starting"}
        color = self.palette["green"] if active else self.palette["muted"]
        if self.voice_state == "thinking":
            color = self.palette["accent"]
        pulse = math.sin(self.voice_orb_phase) if self.voice_state == "listening" else 0
        radius = 6 + max(0, pulse) * 2.5 if active else 5
        canvas.create_oval(
            center_x - 12, center_y - 12, center_x + 12, center_y + 12,
            outline=self.palette["border"], width=1,
        )
        canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill=color, outline="",
        )
        canvas.create_oval(
            center_x - 2, center_y - 2, center_x + 2, center_y + 2,
            fill=self.palette["panel"], outline="",
        )

    def _animate_voice_orb(self):
        if self.voice_state == "listening":
            self.voice_orb_phase += 0.45
            self._draw_voice_orb()
        self.root.after(120 if self.voice_state == "listening" else 350, self._animate_voice_orb)

    def _style_chat(self):
        self.chat.configure(
            bg=self.palette["input"],
            fg=self.palette["foreground"],
            insertbackground=self.palette["foreground"],
            selectbackground=self.palette["accent"],
            highlightbackground=self.palette["border"],
            highlightcolor=self.palette["accent"],
            font=("Consolas", 11),
            relief="flat",
        )
        self.chat.tag_configure(
            "speaker",
            foreground=self.palette["accent"],
            font=("Consolas", 10, "bold"),
            spacing1=5,
        )
        self.chat.tag_configure(
            "body", foreground=self.palette["foreground"], spacing3=8
        )
        self.chat.tag_configure(
            "user",
            foreground=self.palette["green"],
            font=("Consolas", 10, "bold"),
            spacing1=5,
        )

    def _schedule_wallpaper_resize(self, event):
        if event.widget is not self.root or self.wallpaper_source is None:
            return
        if self.wallpaper_resize_job is not None:
            self.root.after_cancel(self.wallpaper_resize_job)
        self.wallpaper_resize_job = self.root.after(90, self._resize_wallpaper)

    def _resize_wallpaper(self):
        self.wallpaper_resize_job = None
        if self.wallpaper_source is None:
            return
        width, height = self.root.winfo_width(), self.root.winfo_height()
        if width < 1 or height < 1:
            return
        size = (width, height)
        if self.wallpaper_base_size != size:
            self.wallpaper_base_image = ImageOps.fit(
                self.wallpaper_source,
                size,
                method=Image.Resampling.LANCZOS,
            )
            self.wallpaper_base_size = size
        image = self.wallpaper_base_image
        if self.wallpaper_animated:
            image = _render_animated_wallpaper(
                image, time.monotonic() - self.wallpaper_animation_start
            )
        self.wallpaper_photo = ImageTk.PhotoImage(image)
        for label in (
            self.wallpaper_label,
            getattr(self, "chat_wallpaper_label", None),
        ):
            if label is not None:
                label.configure(image=self.wallpaper_photo)
                label.place(x=0, y=0, relwidth=1, relheight=1)
                label.lower()

    def _load_wallpaper(self, path):
        image = self._read_custom_image(path)
        self.wallpaper_source = image.convert("RGB")
        self.wallpaper_base_image = None
        self.wallpaper_base_size = None
        self.wallpaper_animated = (
            Path(path).resolve() == (APP_DIR / "aaru_wallpaper.png").resolve()
        )
        self.wallpaper_animation_start = time.monotonic()
        if self.wallpaper_animation_job is not None:
            self.root.after_cancel(self.wallpaper_animation_job)
            self.wallpaper_animation_job = None
        if self.wallpaper_animated:
            self.wallpaper_animation_job = self.root.after(
                WALLPAPER_ANIMATION_INTERVAL_MS, self._animate_wallpaper_rings
            )
        self._resize_wallpaper()

    def _animate_wallpaper_rings(self):
        self.wallpaper_animation_job = None
        if not self.wallpaper_animated:
            return
        self._resize_wallpaper()
        self.wallpaper_animation_job = self.root.after(
            WALLPAPER_ANIMATION_INTERVAL_MS, self._animate_wallpaper_rings
        )

    def _load_avatar(self, path):
        image = ImageOps.fit(
            self._read_custom_image(path).convert("RGBA"),
            (48, 48),
            method=Image.Resampling.LANCZOS,
        )
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 47, 47), fill=255)
        image.putalpha(mask)
        self.avatar_photo = ImageTk.PhotoImage(image)
        self.avatar_label.configure(image=self.avatar_photo)
        self.root.iconphoto(True, self.avatar_photo)

    @staticmethod
    def _read_custom_image(path):
        image_path = Path(path).expanduser()
        try:
            with Image.open(image_path) as image:
                if image.width * image.height > 40_000_000:
                    raise ValueError("Choose an image smaller than 40 megapixels.")
                image.load()
                return image.copy()
        except Image.DecompressionBombError as exc:
            raise ValueError("The selected image is too large to load safely.") from exc

    def choose_wallpaper(self):
        path = filedialog.askopenfilename(
            title="Choose a dashboard wallpaper",
            filetypes=(("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"),),
            parent=self.root,
        )
        if not path:
            return
        try:
            self._load_wallpaper(path)
            self.settings["wallpaper_path"] = str(Path(path).resolve())
            self._save_settings()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not set wallpaper", str(exc), parent=self.root)

    def choose_assistant_icon(self):
        path = filedialog.askopenfilename(
            title="Choose an assistant icon",
            filetypes=(("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.ico"),),
            parent=self.root,
        )
        if not path:
            return
        try:
            self._load_avatar(path)
            self.settings["assistant_icon_path"] = str(Path(path).resolve())
            self._save_settings()
        except (OSError, ValueError) as exc:
            messagebox.showerror(
                "Could not set assistant icon", str(exc), parent=self.root
            )

    def reset_wallpaper(self):
        self._load_wallpaper(APP_DIR / "aaru_wallpaper.png")
        self.settings["wallpaper_path"] = ""
        self._save_settings()

    def reset_assistant_icon(self):
        self.avatar_photo = None
        self.avatar_label.configure(image="")
        self.settings["assistant_icon_path"] = ""
        if self.icon_image is not None:
            self.root.iconphoto(True, self.icon_image)
        self._save_settings()

    def _append_message(self, speaker, text, *, add_history=True):
        self.chat.configure(state="normal")
        if speaker == "You":
            tag, label = "user", "YOU  //  "
        elif speaker in {"Aaru", "Aarohi", "Aarohi (Aaru)"}:
            tag, label = "speaker", "AARU  //  "
        else:
            tag, label = "speaker", f"{speaker.upper()}  //  "
        self.chat.insert("end", label, tag)
        self.chat.insert("end", f"{text}\n\n", "body")
        self.chat.see("end")
        self.chat.configure(state="disabled")
        if add_history and speaker in {"You", "Aaru", "Aarohi", "Aarohi (Aaru)"}:
            role = "user" if speaker == "You" else "assistant"
            self.history.append({"role": role, "content": str(text)[:4_000]})
            self.history = self.history[-16:]

    def _process_events(self):
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "status":
                self.status_var.set(value)
                normalized = value.casefold()
                if "bolna shuru" in normalized:
                    self.ptt_active = True
                    self.voice_state = "listening"
                    self.mic_status.configure(text="LISTENING • ONE SHOT", style="MicOn.TLabel")
                elif "voice chat active" in normalized:
                    self.voice_state = "listening"
                    self.mic_status.configure(text="VOICE CHAT • LISTENING", style="MicOn.TLabel")
                    self.voice_chat_active = True
                elif self.voice_chat_active and (
                    "samajh rahi" in normalized or "responding" in normalized
                ):
                    self.voice_state = "thinking"
                    self.mic_status.configure(text="VOICE CHAT • RESPONDING", style="MicOn.TLabel")
                elif self.voice_chat_active and "sun rahi" in normalized:
                    self.voice_state = "listening"
                    self.mic_status.configure(text="VOICE CHAT • LISTENING", style="MicOn.TLabel")
                elif self.ptt_active and (
                    "voice command complete" in normalized
                    or "offline voice recognition error" in normalized
                ):
                    self.ptt_active = False
                    self.voice_state = "idle"
                    if not self.voice_engine.listening:
                        self.mic_status.configure(text="MIC OFF", style="MicOff.TLabel")
                elif "wake word active" in normalized or "sunn rahi" in normalized:
                    self.voice_state = "listening"
                    self.mic_status.configure(text="LISTENING • WAKE WORD", style="MicOn.TLabel")
                elif "voice chat off" in normalized:
                    self.voice_chat_active = False
                    self.voice_chat_turn = None
                    self.voice_state = "idle"
                    self.mic_status.configure(text="MIC OFF", style="MicOff.TLabel")
                elif "voice chat stopped" in normalized:
                    self.voice_chat_active = False
                    self.voice_chat_turn = None
                    self.voice_state = "idle"
                    self.start_button.configure(
                        state="normal", text="▶  START VOICE CHAT"
                    )
                    self.stop_button.configure(state="disabled")
                    self.mic_status.configure(text="MIC OFF", style="MicOff.TLabel")
                elif "wake word off" in normalized or "mic is off" in normalized:
                    self.voice_state = "idle"
                    self.mic_status.configure(text="MIC OFF", style="MicOff.TLabel")
                self._draw_voice_orb()
            elif kind == "voice_command":
                self._begin_command(value)
            elif kind == "conversation_command":
                self._begin_command(value, conversation=True)
            elif kind == "ptt_command":
                self.busy = False
                self.send_button.configure(state="normal")
                self.speak_button.configure(state="normal")
                self.entry.configure(state="normal")
                self._begin_command(value)
            elif kind == "ptt_done":
                self.ptt_active = False
                if not self.voice_engine.listening:
                    self.mic_status.configure(text="MIC OFF", style="MicOff.TLabel")
            elif kind == "listener":
                active = value
                self.voice_state = "listening" if active else "idle"
                self._draw_voice_orb()
                self.start_button.configure(
                    state="disabled" if active else "normal",
                    text="▶  VOICE CHAT ACTIVE" if active else "▶  START VOICE CHAT",
                )
                self.stop_button.configure(state="normal" if active else "disabled")
            elif kind == "message":
                speaker, text = value[:2]
                turn = value[2] if len(value) > 2 else None
                if turn is not None:
                    turn["has_response"] = True
                self._append_message(speaker, text)
                if speaker in {"Aaru", "Aarohi", "Aarohi (Aaru)"} and self.voice_enabled.get():
                    threading.Thread(
                        target=self._speak_response, args=(text, turn), daemon=True
                    ).start()
                elif turn is not None:
                    turn["speech_done"] = True
                    self._maybe_resume_voice_chat(turn)
            elif kind == "conversation_command_done":
                turn = value
                if turn is self.voice_chat_turn:
                    turn["command_done"] = True
                    if not turn["has_response"]:
                        turn["speech_done"] = True
                    self._maybe_resume_voice_chat(turn)
            elif kind == "conversation_speech_done":
                turn = value
                if turn is self.voice_chat_turn:
                    turn["speech_done"] = True
                    self._maybe_resume_voice_chat(turn)
            elif kind == "confirmation":
                description, phrase, result = value
                answer = simpledialog.askstring(
                    "Aaru confirmation",
                    f"{description}\n\nType exactly: {phrase}",
                    parent=self.root,
                )
                result[1] = answer == phrase
                result[0].set()
            elif kind == "error":
                self._append_message("Aaru", f"Error: {value}")
                messagebox.showerror("Aaru", str(value), parent=self.root)
            elif kind == "busy":
                self.busy = value
                state = "disabled" if value else "normal"
                self.send_button.configure(state=state)
                self.speak_button.configure(state=state)
                self.entry.configure(state=state)
                if not value:
                    self.entry.focus_set()
        self.root.after(100, self._process_events)

    def _speak_response(self, text, turn=None):
        try:
            self.speech_output.speak(text)
        except Exception as exc:
            self.events.put(("status", f"Text answer ready; offline voice unavailable: {exc}"))
        finally:
            if turn is not None:
                self.events.put(("conversation_speech_done", turn))

    def _confirm_action(self, description, phrase):
        result = [threading.Event(), False]
        self.events.put(("confirmation", (description, phrase, result)))
        result[0].wait()
        return result[1]

    def _begin_command(self, command, *, conversation=False):
        if self.busy:
            self.events.put(
                ("status", "Pichhla command abhi chal raha hai. Thoda intezar karein.")
            )
            if conversation:
                self.voice_engine.resume_conversation()
            return
        self.busy = True
        turn = None
        if conversation:
            turn = {
                "command_done": False,
                "has_response": False,
                "speech_done": False,
            }
            self.voice_chat_turn = turn
        self.events.put(("busy", True))
        self._append_message("You", command)
        history = list(self.history[:-1])
        threading.Thread(
            target=self._run_command,
            args=(command, history, turn),
            daemon=True,
        ).start()

    def _run_command(self, command, history, turn=None):
        try:
            self.events.put(("status", "Aaru request samajh rahi hai..."))
            plan = self.service.plan(command, history)
            execute_plan(
                self.service,
                plan,
                confirm_action=self._confirm_action,
                output=lambda text: self.events.put(
                    ("message", ("Aarohi (Aaru)", text, turn))
                ),
            )
        except Exception as exc:
            self.events.put(("error", exc))
        finally:
            self.events.put(("status", "Ready. Microphone runs only when enabled."))
            self.events.put(("busy", False))
            if turn is not None:
                self.events.put(("conversation_command_done", turn))

    def send_text(self, _event=None):
        command = self.entry.get().strip()
        if not command:
            return "break"
        self.entry.delete(0, "end")
        self._begin_command(command)
        return "break"

    def start_voice_chat(self):
        if self.busy:
            return
        self.start_button.configure(state="disabled")
        self.voice_state = "starting"
        self._draw_voice_orb()
        self.status_var.set("Starting hands-free voice chat...")
        threading.Thread(target=self._start_conversation, daemon=True).start()

    def _start_conversation(self):
        try:
            self.voice_engine.start_conversation()
            self.events.put(("listener", True))
        except Exception as exc:
            self.events.put(("error", exc))
            self.events.put(("listener", False))

    def start_wake_word(self):
        if self.busy:
            return
        self.start_button.configure(state="disabled")
        self.status_var.set("Loading local wake-word model...")
        threading.Thread(target=self._start_listener, daemon=True).start()

    def _start_listener(self):
        try:
            self.voice_engine.start()
            self.events.put(("listener", True))
        except Exception as exc:
            self.events.put(("error", exc))
            self.events.put(("listener", False))

    def stop_wake_word(self):
        self.stop_button.configure(state="disabled")
        threading.Thread(target=self._stop_listener, daemon=True).start()

    def _stop_listener(self):
        try:
            self.voice_engine.stop()
        finally:
            self.events.put(("listener", False))

    def _maybe_resume_voice_chat(self, turn):
        if (
            turn is not self.voice_chat_turn
            or not turn["command_done"]
            or not turn["speech_done"]
        ):
            return
        self.voice_chat_turn = None
        if self.voice_chat_active and self.voice_engine.listening:
            self.voice_engine.resume_conversation()

    def listen_once(self):
        if self.busy:
            return
        if self.voice_engine.listening:
            messagebox.showinfo(
                "Aarohi AI",
                "Pehle Stop listening dabayein; ek waqt par ek hi mic session chalega.",
                parent=self.root,
            )
            return
        self.busy = True
        self.send_button.configure(state="disabled")
        self.speak_button.configure(state="disabled")
        self.entry.configure(state="disabled")
        self.events.put(("busy", True))
        self.speak_button.configure(state="disabled")
        threading.Thread(target=self._listen_once_worker, daemon=True).start()

    def _listen_once_worker(self):
        queued_command = False
        try:
            transcript = self.voice_engine.listen_once()
            if transcript:
                self.events.put(("ptt_command", transcript))
                queued_command = True
            else:
                self.events.put(("status", "No speech detected."))
        except Exception as exc:
            self.events.put(("error", exc))
        finally:
            self.events.put(("ptt_done", None))
            if not queued_command:
                self.events.put(("busy", False))

    def _change_provider(self, _event=None):
        self.settings["provider"] = self.provider_var.get()
        self.model_var.set(self._configured_model())
        self._save_settings()
        if self.settings["provider"] == "ollama":
            self.status_var.set(
                "Ollama selected; install/start Ollama and pull the model shown."
            )
        elif self.settings["provider"] == "openai":
            self.status_var.set(
                "OpenAI selected; API use may incur charges. Keep your key private in .env."
            )
        elif self.settings["provider"] == "openrouter":
            self.status_var.set(
                "OpenRouter selected; API use may incur charges. Keep your key private in .env."
            )

    def _change_model(self, _event=None):
        model = self.model_var.get().strip()
        if model:
            key = {
                "openai": "openai_model",
                "openrouter": "openrouter_model",
            }.get(self.settings["provider"], "ollama_model")
            self.settings[key] = model
            self._save_settings()

    def _configured_model(self):
        key = {
            "openai": "openai_model",
            "openrouter": "openrouter_model",
        }.get(self.settings["provider"], "ollama_model")
        return self.settings[key]

    def _change_voice(self):
        self.settings["voice_enabled"] = bool(self.voice_enabled.get())
        self._save_settings()

    def _save_settings(self):
        save_settings(self.settings)
        self.service.update_settings(self.settings)

    def toggle_theme(self):
        theme = "light" if self.settings["theme"] == "dark" else "dark"
        self.settings["theme"] = theme
        self.palette = PALETTES[theme]
        self._apply_theme()
        self._save_settings()

    def clear_chat(self):
        if not messagebox.askyesno(
            "Clear chat", "In-memory conversation history clear karein?", parent=self.root
        ):
            return
        self.history.clear()
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")

    def add_custom_app(self):
        if sys.platform == "darwin":
            path = filedialog.askdirectory(
                title="Choose an installed .app", parent=self.root
            )
        else:
            path = filedialog.askopenfilename(
                title="Choose an installed application",
                filetypes=(
                    (".exe application", "*.exe"),
                    ("All files", "*"),
                ) if sys.platform == "win32" else (("Applications", "*"),),
                parent=self.root,
            )
        if not path:
            return
        alias = simpledialog.askstring(
            "Add approved app",
            "Voice alias for this app (for example, Music Player):",
            parent=self.root,
        )
        if not alias:
            return
        try:
            saved_alias = register_custom_app(alias, path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not add app", str(exc), parent=self.root)
            return
        self._append_message(
            "Aaru",
            f"'{saved_alias}' approved app alias save ho gaya. "
            "Aaru ab isi saved app ko khol sakti hai.",
        )

    def _update_clock(self):
        from system.information import battery_text, date_time_text

        try:
            self.clock_var.set(f"{date_time_text()}   •   {battery_text()}")
        except Exception as exc:
            self.clock_var.set(f"System status unavailable: {exc}")
        self.header_clock.set(datetime.now().astimezone().strftime("%H:%M:%S %Z"))
        self.root.after(30_000, self._update_clock)

    def _update_telemetry(self):
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        battery_percent = battery.percent if battery else None
        values = {
            "cpu": cpu,
            "memory": memory,
            "battery": battery_percent,
        }
        for key, value in values.items():
            variable, unit = self.telemetry_cards[key]
            if value is None:
                variable.set("N/A")
            else:
                variable.set(f"{value:.0f}{unit}")
                self.stat_history[key].append(value)
            self._draw_sparkline(key)
        self.root.after(2500, self._update_telemetry)

    def _draw_sparkline(self, key):
        canvas = self.telemetry_charts[key]
        canvas.delete("all")
        width = max(canvas.winfo_width(), 80)
        height = max(canvas.winfo_height(), 32)
        values = list(self.stat_history[key])
        accent = self.palette["accent"]
        grid = self.palette["border"]
        midline = height - 8
        canvas.create_line(0, midline, width, midline, fill=grid, width=1)
        if len(values) < 2:
            return
        points = []
        step = width / (len(values) - 1)
        graph_height = height - 14
        for index, value in enumerate(values):
            x = index * step
            y = height - 5 - (max(0, min(100, value)) / 100) * graph_height
            points.extend((x, y))
        canvas.create_line(*points, fill=accent, width=2, smooth=True)
        canvas.create_oval(
            points[-2] - 3, points[-1] - 3, points[-2] + 3, points[-1] + 3,
            fill=accent, outline="",
        )

    def close(self):
        if self.wallpaper_animation_job is not None:
            self.root.after_cancel(self.wallpaper_animation_job)
            self.wallpaper_animation_job = None
        try:
            self.voice_engine.stop()
        except (OSError, RuntimeError) as exc:
            messagebox.showwarning(
                "Aarohi AI",
                f"Microphone could not close cleanly: {exc}",
                parent=self.root,
            )
        self.root.destroy()
