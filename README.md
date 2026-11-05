# Aarohi AI (Aaru)

Aarohi AI, nicknamed Aaru, is a small, offline-first desktop voice assistant. It is designed first
for Windows 11 laptops, with a limited set of safe controls also available on
macOS and Linux. It uses Python and Tkinter instead of a large Electron app.
Created by Krishna Kant in India.

The project intentionally does **not** contain 25,000-100,000 lines of
duplicated code. It keeps the implementation modular and testable.

## What works

- Text chat and a futuristic dark/neon desktop dashboard with light-theme
  option, live CPU/RAM/battery sparkline panels, system clock, microphone
  status, and in-memory conversation history. The assistant is **Aarohi AI**,
  nicknamed **Aaru**. The app opens to the full-bleed Aaru wallpaper with an
  **OPEN AARU** button; opening it reveals the chat, voice, and AI provider
  controls. Use **Appearance** in the dashboard to choose a
  Fill-scaled wallpaper and a custom assistant avatar; choices are saved
  locally in the user's Aaru AI settings. The dashboard identifies its creator
  as Krishna Kant and displays “Made in India”.
- The desktop window and Windows shortcut use `aaru.ico`; the dashboard mark
  uses `aaru-preview.png`. Both are generated from the complete `aaru.svg`
  source artwork. `aaru_wallpaper.svg` is rendered to the 1920 × 1080
  `aaru_wallpaper.png`; the dashboard scales it with Windows-style Fill
  cropping to avoid margins. With the default wallpaper, the portrait is
  slightly enlarged and its cyan HUD rings animate; custom wallpapers remain
  unchanged.
- Offline multilingual speech-to-text through the base Whisper model; continuous
  hands-free voice chat and single-command push-to-talk are available.
- Hindi text-to-speech using Google's online Translate speech service. Only
  Aaru's reply text is sent to the speech service; microphone audio stays local.
- Basic commands and common Hinglish phrases work without a language model.
- Optional natural conversation with a local Ollama model or the OpenAI API.
  Ollama works locally; OpenAI sends prompts to OpenAI and may incur API
  charges depending on the user's API plan/credits.
- Open the approved apps and websites listed below; search Google or YouTube;
  open common user folders; set volume and supported display brightness; take
  local screenshots; control media keys and switch windows.
- On Windows, open Windows Security for the user to start a Defender scan.
  Aaru does not run scans or disable security settings. A named, supported
  desktop app can receive a normal close request after a typed confirmation;
  apps are never force-terminated or all closed together.
- Battery and basic system information, local notes, and limited file listing,
  text summarizing, folder creation, and file moving within `Aaru AI Files`.
- Short, local educational cybersecurity lessons.

### Approved app names

Chrome, Edge, Notepad, Calculator, Paint, Word, Excel, PowerPoint, VS Code,
Task Manager/System Monitor, Settings, Control Panel, Snipping Tool, Camera,
and File Explorer. Aaru checks whether an app is available on the current OS
and reports when it is missing. To add another installed app, use **Add app…**
in the dashboard to choose its executable and give it a voice alias. On Windows,
only a manually selected `.exe` is saved; Aaru launches it without command-line
arguments. The alias and path are stored in the user's Aaru AI data folder.
App availability varies by OS and installation.

### Approved websites

Google, YouTube, Gmail, WhatsApp Web, Instagram, Facebook, ChatGPT, Claude,
Google Maps, Amazon India, Flipkart, and GitHub. Aaru can also open YouTube
account settings and YouTube Studio for account/channel management. These pages
open in the default browser; sign in with Google there. Aaru does not collect
or store Google credentials. A user-requested ordinary HTTP/HTTPS URL can also
be opened. Search opens browser results; Aaru does not store or rebroadcast
copyrighted music.

## What is deliberately not automatic

- The microphone is **off** until the user presses **Start voice chat** or
  **Speak once**. Voice chat listens until the user presses **Stop** and pauses
  while Aaru processes and speaks each reply. Audio recognition is local;
  recognized text is sent only to the selected AI provider.
- A voice is not identity verification. Wake-word detection can hear another
  nearby person, so it cannot approve risky actions.
- Lock, sleep, shutdown, restart, moving files, and sending a selected file to
  the local AI require a separate visible dialog and the user must type the
  requested confirmation phrase. Saying “yes” into the microphone does not
  confirm the dialog. Aaru never deletes files, disables Defender/firewalls,
  bypasses login, or runs arbitrary terminal/PowerShell commands.
  - Say “virus scan” or “Windows Security kholo” to open Microsoft's Virus &
    threat protection page; choose Quick scan or Full scan there. Microsoft
    Defender, not Aaru, handles any detected-threat quarantine/removal.
    Say “Chrome band karo” (or name another supported app) to request a normal
    close; Aaru displays the matching window titles and requires typing
    `CLOSE APP`. Save work first. “Close all apps” is intentionally not supported.
- Aaru's cybersecurity module is educational. It discusses authorization,
  defensive basics, and safe local labs. It does not scan networks, access
  accounts/devices, or execute Nmap/Wireshark or other terminal commands.
- Offline mode is not a general-purpose LLM: it handles basic commands,
  simple arithmetic, and curated lessons. For open-ended questions, install
  Ollama and select it in the dashboard. Small local models may make mistakes
  and can be slower on a low-memory laptop.

## Requirements

- Windows 11 64-bit, macOS, or a desktop Linux distribution.
- Python 3.11 or 3.12 recommended. Linux distributions need Tkinter and
  `espeak` for offline voice output; macOS/Linux may request microphone,
  accessibility, or screen-capture permissions for the respective features.
- A working microphone and speakers/headphones for voice.
- The setup downloads open-source voice components when requested:
  - Vosk small English model (about 40 MB) for the “Aaru” wake word.
  - Whisper base multilingual model for Hindi/English speech.
  These model files are stored under the current user's Aaru AI data folder,
  not in the source tree. The first download needs internet. Text and basic
  offline commands still work if you skip them.
- Optional: Ollama and a local model. On a constrained laptop, try a small
  multilingual model such as `qwen2.5:1.5b`. Ollama and the model use additional
  disk space/RAM; neither is bundled.

## Windows 11 setup

1. Install 64-bit Python 3.11 or 3.12 and enable the Python Launcher.
2. Open PowerShell in this project folder.
3. Run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\setup.ps1
   ```

4. Choose whether to download the local voice models. Skipping keeps basic text
   commands available; voice features explain how to install the models later.
5. Start Aaru with `.\run.ps1` or double-click `run.bat`.

The setup uses a project-local `.venv`, so it does not install these packages
into another Python project. It also creates/refreshes a desktop shortcut named
**Aarohi AI** with the included icon.

### Optional local AI chat

1. Install Ollama from its official website.
2. In a terminal, download a model, for example:

   ```text
   ollama pull qwen2.5:1.5b
   ```

3. Start Ollama and select **ollama** in Aaru's dashboard. The model field
   defaults to `qwen2.5:1.5b`; set it to the model you downloaded.

Ollama should listen locally at `127.0.0.1:11434`. Aaru rejects non-local
Ollama endpoints. Chat history stays in memory and is sent only to that local
Ollama service when the Ollama provider is selected.
For laptops with 8 GB RAM, the 1.5B model uses CPU and may take several
seconds on its first answer. Aaru keeps it loaded briefly, limits context and
answer length, and handles common Romanized-Hindi greetings/capability
questions locally. Small models can still misunderstand open-ended Hinglish;
try a short, direct question or use the optional OpenAI provider.

### Optional OpenAI API

1. Add your API key to the blank `.env` file in the project root:

   ```text
   OPENAI_API_KEY=your_api_key_here
   ```

2. Restart Aaru, select **openai** in the AI provider list, and leave the model
   as `gpt-4o-mini` or enter another model available to your API account.
3. API requests send your current prompt and recent conversation to OpenAI.
   API access/billing is separate from ChatGPT subscriptions; a one-year offer
   does not by itself guarantee unlimited API usage. Check API Platform usage
   and limits. Aaru does not fall back silently if the key is missing or the
   API rejects a request.

The project-root `.env` is ignored by Git. Never paste an API key in chat,
commit it, or put it in `config.py` or `settings.json`. If a key has already
been shared publicly or in an untrusted place, revoke it and create a new one.

### Optional OpenRouter API

1. Add your OpenRouter key to the project-root `.env` file:

   ```text
   OPENROUTER_API_KEY=your_openrouter_key_here
   ```

2. Restart Aarohi and select **openrouter** in **AI CORE**. The default model
   is `openrouter/auto`; you can enter another model ID supported by your
   OpenRouter account.
3. OpenRouter forwards the prompt to the selected model. Requests may use
   account credits or incur charges according to your OpenRouter account and
   chosen model. Check its current model availability and pricing first.

The OpenRouter key is read from `.env` and is never written to Aaru settings.
Do not paste the key into chat or commit it.

## Linux/macOS setup

Install Python 3, Tkinter, and any OS-specific audio prerequisites first, then
run:

```sh
sh ./setup.sh
sh ./run.sh
```

The dashboard, text chat, web search, local notes, offline models, and some
desktop controls are cross-platform. Window switching and global media keys
may require accessibility permission. Brightness and volume support depends
on installed OS services/drivers. Power controls are currently implemented
only for Windows; Aaru reports unsupported actions instead of running a
generic shell command. The primary target and full app list are Windows 11.

## Voice chat and speech

1. Complete setup and install the offline multilingual speech model.
2. Click **Start voice chat** and speak naturally in Hindi or English. Aaru
   loads its speech model before opening the mic, detects a 0.5-second pause,
   processes your turn, speaks its reply, and listens again. No wake word or
   fixed-length recording is needed. The mic listens for quieter speech, and
   the dashboard's voice indicator shows listening and processing states.
3. Click **Stop** to end the conversation and close microphone access.
   **Speak once** remains available for one short, 12-second command.
4. Use the text box at any time. Voice is never treated as proof of identity.

Speech recognition preloads the base multilingual Whisper model when voice chat
starts, then retries likely Hindi-English mixed speech as Hindi if automatic
language detection mistakes it for English. A short pause ends each turn. CPU
threads are selected for the available processor and a fast decoding beam keeps
transcription responsive. Accents, noise, song titles, and mixed-language speech
can still affect accuracy. Aaru does not synthesize or clone a person's voice.

## Privacy and security

- No microphone stream is opened until a listening button is used. Stop
  listening closes it.
- Speech audio is processed in memory by local models; Aaru does not save
  microphone recordings to the user's files.
- Offline mode and local Ollama keep voice transcripts and chat on the device.
  Selecting OpenAI or OpenRouter sends recognized text to that provider.
  Speaking a reply uses Google's online Hindi speech service and sends only
  the reply text to it.
  Internet searches open the selected browser and send the query to that
  website. Do not put passwords or secrets in a search.
- Reading/summarizing a file is limited to UTF-8 text files under
  `Documents\Aaru AI Files` (64 KB maximum) and requires typing **SEND FILE**.
  In Ollama mode the selected text is sent to the local Ollama service; in
  Offline mode Aaru returns a clearly labeled excerpt instead.
- Notes are plain UTF-8 files stored locally under the user's Aaru AI data
  folder. Do not store passwords or recovery codes in notes.
- Chat history is held in memory only and the **Clear chat** button removes it.
  No voice profile or biometric identification is stored.
- The assistant accepts plans only from a fixed action allowlist and validates
  all arguments before use. It never gives model output to a command shell.

## Ethical cybersecurity learning

Ask for fundamentals, Kali/Linux command explanations, networking, Nmap,
Wireshark, Wi-Fi/CCTV security, password safety, privacy, or authorized lab
guidance. For example, Aaru explains that `sudo su` may open a root
(administrator) shell, why commands in that shell are powerful, and why using
`sudo` for one needed command is generally safer. Lessons are informational
only: Aaru never runs terminal commands. Practice only in an isolated lab you
own or have explicit written permission to test. No network scans or
offensive commands are run.

## Project layout

```text
Aaru/
  main.py                    Desktop application entry point
  config.py                  Paths and non-secret settings
  assistant/
    conversation.py          Offline/optional Ollama conversation
    models.py                Strict model-output validation
    offline.py               Basic offline Hindi/English intents
    voice_engine.py          Local wake word and multilingual speech
    speech_output.py         Offline OS text-to-speech
  dashboard/
    main_window.py           Tkinter dashboard and explicit controls
  system/
    actions.py               Allowlisted action dispatcher
    apps.py                  App, website, and folder allowlists
    controls.py              Volume, brightness, media, screenshot, power
    information.py           Battery, date, and system status
    notes.py                 Local notes and safe text-file paths
  security/
    confirmations.py          Typed confirmation policy
    cybersecurity.py          Defensive learning cards
  tests/
    test_core.py              Safety and offline behavior tests
  download_models.py         Optional voice-model setup
  setup.ps1 / setup.sh        Environment setup
  run.ps1 / run.sh / run.bat  Launchers
  requirements.txt            Python dependencies
```

## Tests and development

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Or on macOS/Linux:

```sh
.venv/bin/python -m unittest discover -v
```

## Common issues

- **Python/venv not found:** install 64-bit Python 3.11/3.12, reopen the
  terminal, and run setup again.
- **Tkinter missing:** install the OS Python Tk package (`python3-tk` on
  Debian/Ubuntu); this package is supplied with standard Windows Python.
- **Wake-word model missing:** run
  `.\.venv\Scripts\python.exe .\download_models.py --wake-word`.
- **Speech model missing:** run
  `.\.venv\Scripts\python.exe .\download_models.py --speech`. This needs
  internet once; subsequent transcription is local.
- **No microphone/audio:** choose the correct OS input device and grant the
  app microphone permission. Stop any other app currently holding the device.
- **Hindi voice unavailable:** check the internet connection. Hindi voice
  replies use Google's online speech service.
- **Ollama error:** start Ollama, confirm the model is downloaded, and check
  that the dashboard model name exactly matches the local model.
- **Brightness/volume/media unavailable:** the laptop display, sound service,
  OS permissions, and installed drivers must support that control.
- **Application not found:** install the app or use the approved name. Aaru
  does not accept an arbitrary executable path from voice/model output.

## Optional Windows executable

After setup, a user can build a distributable with PyInstaller, but this is not
part of the standard install. The application still needs the speech models,
Tk/audio system libraries, and an appropriate licence review. A bundled EXE
does not make the models or general AI answers magically offline; keep the
limitations above in mind.

For an experimental Windows build, activate the project virtual environment,
install PyInstaller, and test the result on a clean Windows account:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\pyinstaller.exe --noconfirm --windowed --name AaruAI --icon .\aaru.ico --add-data ".\aaru-preview.png;." --collect-all faster_whisper --collect-all vosk .\main.py
```

This packaging command is a starting point, not a verified release build;
speech-model downloads remain separate and native audio/Tk libraries may need
platform-specific packaging work.
