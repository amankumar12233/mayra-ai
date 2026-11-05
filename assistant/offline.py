"""Small offline intent parser for common commands and basic calculations."""

import ast
import operator
import re

from assistant.models import normalize_plan
from system.apps import APPS, FOLDERS, SITES, canonical_app, custom_apps


_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _safe_arithmetic(node):
    if isinstance(node, ast.Expression):
        return _safe_arithmetic(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if abs(node.value) > 1_000_000_000:
            raise ValueError("Number is too large.")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left, right = _safe_arithmetic(node.left), _safe_arithmetic(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 8:
            raise ValueError("Power must be between -8 and 8.")
        result = _BINOPS[type(node.op)](left, right)
        if abs(result) > 1_000_000_000:
            raise ValueError("Result is too large.")
        return result
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_safe_arithmetic(node.operand))
    raise ValueError("Only basic arithmetic is supported offline.")


def calculate(text):
    normalized = text.casefold()
    word_operators = (
        (r"\bdivided by\b", "/"),
        (r"\bover\b", "/"),
        (r"\bmultiplied by\b", "*"),
        (r"\btimes\b", "*"),
        (r"\bplus\b", "+"),
        (r"\bminus\b", "-"),
    )
    for pattern, operator_symbol in word_operators:
        normalized = re.sub(pattern, operator_symbol, normalized)
    match = re.search(
        r"(?:calculate|what is|what's|solve|kitna hota hai|jod(?:o)?|add)\s*"
        r"([-+*/().\d\s%]+)",
        normalized,
    )
    if not match:
        return None
    expression = match.group(1).strip().rstrip("?. ")
    if not expression or len(expression) > 80:
        return None
    expression = expression.replace("%", "/100")
    try:
        result = _safe_arithmetic(ast.parse(expression, mode="eval"))
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
        return None
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return normalize_plan(
        {
            "action": "reply",
            "args": {"text": f"Answer: {result}"},
            "message": "",
        }
    )


def _has(text, *phrases):
    return any(phrase in text for phrase in phrases)


def creator_reply(command):
    text = command.casefold().strip()
    crush_question = _has(
        text,
        "aarohi kaun hai",
        "aarohi kon hai",
        "aarohi kaun ho",
        "who is aarohi",
        "who's aarohi",
        "who is aaru",
        "who's aaru",
        "who is your crush",
        "who's your crush",
        "aarohi ki crush",
        "aaru ki crush",
        "aarohi kiski crush",
        "aaru kiski crush",
        "tumhari crush kaun",
        "tumhara crush kaun",
        "tumhe kis par crush hai",
        "आराही कौन है",
        "आरोही कौन है",
        "आरू कौन है",
        "तुम्हारी क्रश कौन",
        "तुम्हारा क्रश कौन",
        "आराही किसकी क्रश",
        "आरोही किसकी क्रश",
    )
    creator_identity_question = _has(
        text,
        "who is krishna kant",
        "who's krishna kant",
        "krishna kant kaun",
        "krishna kant kon",
        "कृष्णा कांत कौन",
        "कृष्ण कांत कौन",
    )
    country_question = _has(
        text,
        "which country",
        "what country",
        "what country were you",
        "which country were you",
        "what country are you from",
        "where were you made",
        "where were you created",
        "kis country",
        "kis desh",
        "kaun se desh",
        "kis mulk",
        "भारत में बनी",
        "भारत में बने",
        "किस देश",
    )
    creator_question = _has(
        text,
        "tumhe kisne banaya",
        "tumhe kisna banaya",
        "tumhe kisne manaya",
        "tumko kisne banaya",
        "aapko kisne banaya",
        "kisne banaya tumhe",
        "kisne tumhe banaya",
        "tumhe kisne create kiya",
        "tumhe kisne banaya hai",
        "tumhe kisne design kiya",
        "तुम्हें किसने बनाया",
        "तुमें किसने बनाया",
        "तुम्हें किसने मनाया",
        "तुमें किसने मनाया",
        "तुमको किसने बनाया",
        "आपको किसने बनाया",
        "किसने तुम्हें बनाया",
        "who made you",
        "who created you",
        "who developed you",
        "who built you",
        "who is your creator",
    )
    identity_question = _has(
        text,
        "tum ai ho ya insaan",
        "tum ai ho ya insan",
        "tum ai ho ya real",
        "kya tum ai ho",
        "kya aap ai ho",
        "kya tum insaan ho",
        "kya tum insan ho",
        "kya aap insaan hain",
        "kya aap insan hain",
        "are you an ai",
        "are you ai",
        "are you human",
        "are you a real person",
        "are you a real human",
        "तुम एआई हो या इंसान",
        "क्या तुम एआई हो",
        "क्या आप एआई हो",
        "क्या तुम इंसान हो",
        "क्या आप इंसान हैं",
    )
    if not (
        crush_question
        or creator_identity_question
        or creator_question
        or country_question
        or identity_question
    ):
        return None
    is_hindi = bool(re.search(r"[\u0900-\u097f]", text))
    is_english = bool(re.search(r"\b(who|your|created|made|developer|are you)\b", text))
    if crush_question:
        if is_hindi:
            reply = "आराही, कृष्णा कांत की क्रश है।"
        elif is_english:
            reply = "Aarohi is Krishna Kant's crush."
        else:
            reply = "Aarohi Krishna Kant ki crush hai."
    elif creator_identity_question:
        if is_hindi:
            reply = (
                "कृष्णा कांत आरू के निर्माता हैं। उनका निकनेम अमन कुमार है।"
            )
        elif is_english:
            reply = (
                "Krishna Kant created Aaru. His nickname is Aman Kumar."
            )
        else:
            reply = (
                "Krishna Kant Aaru ke creator hain. Unka nickname Aman Kumar hai."
            )
    elif identity_question:
        if is_hindi:
            reply = "मैं आराही हूँ, आरू की AI assistant। मैं एक AI assistant हूँ, असली इंसान नहीं।"
        elif is_english:
            reply = "I'm Aarohi, Aaru's AI assistant. I'm an AI assistant, not a real person."
        else:
            reply = "Main Aarohi, Aaru ki AI assistant hoon. Main AI assistant hoon, asli insaan nahi."
    elif country_question:
        if is_hindi:
            reply = "मैं भारत में बनी हूँ।"
        elif is_english:
            reply = "I was made in India."
        else:
            reply = "Main India mein bani hoon."
    elif is_hindi:
        reply = "मुझे कृष्णा कांत ने बनाया है।"
    elif is_english:
        reply = "Krishna Kant created me."
    else:
        reply = "Mujhe Krishna Kant ne banaya hai."
    return normalize_plan({"action": "reply", "args": {"text": reply}})


def _clean_query(text, service):
    query = text.casefold()
    query = re.sub(r"\baaru\b|आरू|आरु", " ", query)
    for word in (
        "please", "can you", "could you", "open", "khol do",
        "kholo", "khol ke", "jao", "pe", "par", "on", "search", "find",
        "dhoondo", "dhundo", "karo", "kar do", "sunao", "suna", "chalao",
        "play", "gana", "gaana", "ganna", "song", "songs", "music",
        "youtube", "you tube", "google", "aaru", "for", "mujhe", "please",
        "ka", "ki", "ke", "and",
    ):
        query = re.sub(rf"\b{re.escape(word)}\b", " ", query)
    query = re.sub(r"[^\w\s'-]", " ", query)
    query = re.sub(r"\s+", " ", query).strip()
    if service == "youtube" and not query:
        return None
    return query or None


def interpret_offline(command):
    text = command.casefold().strip()
    if not text:
        return None

    creator = creator_reply(text)
    if creator:
        return creator

    if _has(
        text,
        "can you speak hindi",
        "can you talk in hindi",
        "hindi me baat",
        "hindi mein baat",
        "hindi me bol",
        "hindi mein bol",
        "hindi me baat kr",
        "hindi mein baat kr",
    ):
        reply = (
            "Haan, main Hindi, English aur Hinglish mein baat kar sakti hoon. "
            "Aap jis style mein likhenge, main usi style mein jawab dene ki koshish karungi."
            if re.search(r"\b(me|mein|kr|krr|sakta|sakti)\b", text)
            else "हाँ, मैं हिंदी, English और Hinglish में बात कर सकती हूँ। आप जिस भाषा में पूछेंगे, मैं उसी में जवाब दूँगी।"
        )
        return normalize_plan({"action": "reply", "args": {"text": reply}})

    if _has(
        text,
        "tum apna batao",
        "aap apna batao",
        "you tell me about yourself",
        "tell me about yourself",
        "me kuch nhi ker sakta tum apna batao",
        "main kuch nahi kar sakta tum apna batao",
        "kuch nhi tum batao",
        "kuch nahi tum batao",
    ):
        return normalize_plan(
            {
                "action": "reply",
                "args": {
                    "text": (
                        "Main Aarohi AI hoon, aap mujhe Aaru bula sakte hain. "
                        "Main aapke sawaalon, Hindi-English baat-cheet, apps aur "
                        "safe laptop controls mein madad karti hoon. Aap kis baare "
                        "mein baat karna chahenge?"
                    )
                },
            }
        )

    if text.strip(" .,!?") in {
        "kya hua",
        "bolo kya hua",
        "aaru kya hua",
        "aaru bolo kya hua",
        "what happened",
    }:
        return normalize_plan(
            {
                "action": "reply",
                "args": {
                    "text": (
                        "Kuch nahi hua—main yahin hoon aur aapse baat kar rahi hoon. "
                        "Aap batao, kis topic par baat karein?"
                    )
                },
            }
        )

    if _has(
        text,
        "what can you do",
        "what all can you do",
        "how can you help",
        "tum kya kya kar sakti",
        "tum kya kya ker sakti",
        "tum kya kya kar sakta",
        "tum kya kya ker sakta",
        "tum kya kar sakte",
        "tum kya ker sakti ho",
        "tum kya kar sakta ho",
        "tum kya kar sakte ho",
        "aap kya kya kar sakti",
        "aap kya kar sakte",
    ):
        reply = (
            "Main apps aur websites khol sakti hoon, Google/YouTube search, "
            "system info, volume/brightness, notes aur basic sawaalon mein madad "
            "kar sakti hoon. Commands ya shutdown jaise sensitive actions se "
            "pehle confirmation leti hoon."
            if re.search(r"\b(tum|ker|kr|sakta|sakti|hoon)\b", text)
            else "I can open supported apps and websites, search Google/YouTube, "
            "share system info, adjust volume/brightness, save notes, and answer "
            "general questions through the configured AI provider. Sensitive actions require confirmation."
        )
        return normalize_plan({"action": "reply", "args": {"text": reply}})

    if _has(
        text,
        "don't lock",
        "do not lock",
        "not lock",
        "lock mat",
        "lock na",
        "no lock",
        "nahi lock",
        "don't shut",
        "do not shut",
        "mat shutdown",
        "shutdown mat",
    ) or (
        _has(text, "don't", "do not", "mat ", "na kare", "not ")
        and _has(text, "lock", "sleep", "shutdown", "shut down", "restart")
    ):
        return normalize_plan(
            {
                "action": "reply",
                "args": {"text": "The computer will not be locked or shut down."},
            }
        )

    security_terms = {
        "nmap": ("nmap", "n map", "network scan"),
        "wireshark": ("wireshark", "packet capture"),
        "wifi": ("wifi", "wi-fi", "wireless security"),
        "cctv": ("cctv", "camera security"),
        "passwords": ("password", "passphrase", "mfa", "two factor"),
        "privacy": ("online privacy", "privacy"),
        "labs": (
            "ethical hacking",
            "cyber lab",
            "authorized lab",
            "hack into",
            "break into",
            "unauthorized access",
            "credential theft",
            "brute force",
            "ddos",
            "write malware",
            "make malware",
            "keylogger",
            "exploit a website",
        ),
        "linux": (
            "linux command",
            "linux basics",
            "kali",
            "sudo su",
            "sudo command",
        ),
        "networking": ("networking basics", "ip address", "dns", "network basics"),
        "fundamentals": (
            "cybersecurity",
            "cyber security",
            "ethical security",
            "disable antivirus",
            "turn off antivirus",
            "turn off defender",
            "turn off windows defender",
            "defender off",
            "disable defender",
            "disable firewall",
            "turn off firewall",
            "firewall off",
            "firewall disable",
            "login bypass",
            "bypass login",
            "password bypass",
        ),
    }
    for topic, phrases in security_terms.items():
        if _has(text, *phrases):
            return normalize_plan(
                {"action": "cybersecurity_lesson", "args": {"topic": topic}}
            )

    if _has(
        text,
        "virus scan",
        "scan for virus",
        "scan for viruses",
        "malware scan",
        "defender scan",
        "remove virus",
        "remove viruses",
        "virus hatao",
        "virus htao",
        "virus nikal",
        "windows security",
        "turn on protection",
        "enable defender",
        "defender on",
        "firewall on",
    ):
        return normalize_plan({"action": "open_security", "args": {}})

    if _has(
        text,
        "close all apps",
        "close all windows",
        "close everything",
        "all open apps",
        "sab apps band",
        "saari apps band",
        "sab kuch band",
        "jo bhi khula",
        "desktop band",
    ):
        return normalize_plan(
            {
                "action": "reply",
                "args": {
                    "text": (
                        "Main unsaved work bachane ke liye sab apps ek saath band "
                        "nahi karti. Kisi ek supported app ka naam boliye, jaise "
                        "'Chrome band karo'; main pehle typed confirmation lungi."
                    )
                },
            }
        )

    arithmetic = calculate(text)
    if arithmetic:
        return arithmetic

    if _has(text, "what time", "current time", "time kya", "kitne baje"):
        return normalize_plan(
            {"action": "date_time", "args": {}, "message": ""}
        )
    if _has(text, "what date", "today's date", "today date", "aaj ki date", "aaj kya din"):
        return normalize_plan(
            {"action": "date_time", "args": {}, "message": ""}
        )
    if _has(text, "battery", "charge kitna", "battery kitna"):
        return normalize_plan(
            {"action": "battery_info", "args": {}, "message": ""}
        )
    if _has(text, "system info", "computer information", "laptop specs", "system information"):
        return normalize_plan(
            {"action": "system_info", "args": {}, "message": ""}
        )
    if _has(text, "list files", "show files", "files dikhao"):
        match = re.search(r"(?:in|inside|mein|under)\s+(.+)$", text)
        folder = match.group(1).strip(" .") if match else "."
        return normalize_plan(
            {"action": "list_files", "args": {"folder": folder}}
        )
    if _has(text, "create folder", "new folder", "folder banao", "folder bana do"):
        name = re.sub(
            r"^(?:.*?)(?:create folder|new folder|folder banao|folder bana do)\s*",
            "",
            text,
        ).strip(" .")
        if name:
            return normalize_plan(
                {"action": "create_folder", "args": {"path": name}}
            )
    if _has(text, "summarize file", "summary of file", "file ka summary"):
        match = re.search(r"(?:file|of)\s+(.+)$", text)
        if match:
            return normalize_plan(
                {"action": "summarize_file", "args": {"path": match.group(1).strip()}}
            )
    if _has(text, "move file", "file move", "file ko move"):
        match = re.search(r"from\s+(.+?)\s+to\s+(.+)$", text)
        if match:
            return normalize_plan(
                {
                    "action": "move_file",
                    "args": {
                        "source": match.group(1).strip(),
                        "destination_folder": match.group(2).strip(),
                    },
                }
            )
    if _has(text, "save note", "make a note", "note likho", "note banao", "note this"):
        content = re.sub(
            r"^(?:.*?)(?:save note|make a note|note likho|note banao|note this)\s*",
            "",
            command,
            flags=re.IGNORECASE,
        ).strip()
        if content:
            title = " ".join(content.split()[:5]).strip(" .,:;")
            return normalize_plan(
                {"action": "save_note", "args": {"title": title, "text": content}}
            )

    if _has(text, "screenshot", "screen shot", "capture my screen"):
        return normalize_plan({"action": "screenshot", "args": {}})
    if _has(text, "next track", "next song", "next media"):
        return normalize_plan(
            {"action": "media_control", "args": {"control": "next"}}
        )
    if _has(text, "previous track", "previous song", "previous media", "last song"):
        return normalize_plan(
            {"action": "media_control", "args": {"control": "previous"}}
        )
    if _has(text, "pause music", "resume music", "play pause", "play or pause", "media pause"):
        return normalize_plan(
            {"action": "media_control", "args": {"control": "play_pause"}}
        )
    if _has(text, "switch window", "next window", "change window", "alt tab"):
        return normalize_plan({"action": "switch_window", "args": {}})

    if _has(text, "mute", "unmute", "sound band", "awaaz band"):
        return normalize_plan({"action": "toggle_mute", "args": {}})
    if _has(text, "volume"):
        if _has(text, "increase", "up", "badha", "tez"):
            return normalize_plan(
                {"action": "adjust_volume", "args": {"delta": 10}}
            )
        if _has(text, "decrease", "down", "kam", "low"):
            return normalize_plan(
                {"action": "adjust_volume", "args": {"delta": -10}}
            )
        match = re.search(r"\b(\d{1,3})\s*(?:percent|%)", text)
        if match:
            return normalize_plan(
                {"action": "set_volume", "args": {"percent": int(match.group(1))}}
            )

    if _has(text, "brightness", "screen light", "display light"):
        match = re.search(r"\b(\d{1,3})\s*(?:percent|%)", text)
        if match:
            return normalize_plan(
                {"action": "set_brightness", "args": {"percent": int(match.group(1))}}
            )
        if _has(text, "increase", "up", "badha", "tez"):
            return normalize_plan(
                {"action": "set_brightness", "args": {"percent": 70}}
            )
        if _has(text, "decrease", "down", "kam", "low"):
            return normalize_plan(
                {"action": "set_brightness", "args": {"percent": 30}}
            )

    for alias in sorted(FOLDERS, key=len, reverse=True):
        if _has(text, f"open {alias}", f"{alias} folder", f"{alias} kholo", f"{alias} khol"):
            return normalize_plan(
                {"action": "open_folder", "args": {"folder": alias}}
            )

    if _has(text, "lock", "lock my laptop", "laptop lock", "computer lock"):
        return normalize_plan(
            {"action": "system_action", "args": {"action": "lock"}}
        )
    if _has(text, "shutdown", "shut down", "turn off my laptop", "laptop band"):
        return normalize_plan(
            {"action": "system_action", "args": {"action": "shutdown"}}
        )
    if _has(text, "restart", "reboot"):
        return normalize_plan(
            {"action": "system_action", "args": {"action": "restart"}}
        )
    if _has(text, "sleep computer", "put computer to sleep", "laptop sleep"):
        return normalize_plan(
            {"action": "system_action", "args": {"action": "sleep"}}
        )

    requested_url = re.search(r"https?://[^\s]+", command, flags=re.IGNORECASE)
    if requested_url and _has(text, "open", "visit", "website", "khol", "kholo"):
        return normalize_plan(
            {"action": "open_url", "args": {"url": requested_url.group(0).rstrip(".,!?")}}
        )

    if "google maps" in text and _has(text, "open", "khol", "kholo", "visit"):
        return normalize_plan({"action": "open_site", "args": {"site": "maps"}})

    for name in sorted(SITES, key=len, reverse=True):
        if name == "google" and name in text and _has(
            text, "search", "find", "dhoondo", "dhundo", "search for"
        ):
            query = _clean_query(text, "google")
            if query:
                return normalize_plan(
                    {"action": "web_search", "args": {"query": query}}
                )
        if name in text and (
            _has(text, "open", "khol", "kholo", "launch", "go to", "visit")
            or name == "youtube" and _has(text, "gana", "gaana", "ganna", "song", "search", "suna", "play")
        ):
            if name == "youtube" and _has(text, "search", "gana", "gaana", "ganna", "song", "suna", "play"):
                query = _clean_query(text, "youtube")
                if query:
                    return normalize_plan(
                        {"action": "youtube_search", "args": {"query": query}}
                    )
            return normalize_plan(
                {"action": "open_site", "args": {"site": name}}
            )

    close_requested = _has(
        text, "close", "quit", "exit", "band karo", "band kar do", "band kar"
    )
    if close_requested:
        normalized_close_text = re.sub(r"[^\w\s.-]", " ", text)
        normalized_close_text = re.sub(r"[-_]", " ", normalized_close_text)
        normalized_close_text = re.sub(r"\s+", " ", normalized_close_text).strip()
        app_aliases = [
            (alias, app_id)
            for app_id, aliases in APPS.items()
            for alias in aliases + (app_id.replace("_", " "),)
        ]
        app_aliases.extend(
            (alias.replace("_", " "), f"custom:{alias}")
            for alias in custom_apps()
        )
        for alias, app_id in sorted(app_aliases, key=lambda item: len(item[0]), reverse=True):
            normalized_alias = re.sub(r"\s+", " ", alias.replace("-", " ").casefold()).strip()
            if normalized_alias and re.search(
                rf"(?<!\w){re.escape(normalized_alias)}(?!\w)",
                normalized_close_text,
            ):
                return normalize_plan(
                    {"action": "close_app", "args": {"app": app_id}}
                )

    for app_id, aliases in APPS.items():
        for alias in sorted(aliases + (app_id.replace("_", " "),), key=len, reverse=True):
            if alias in text and (
                _has(text, "open", "khol", "kholo", "launch", "start", "chalao")
                or text == alias
            ):
                return normalize_plan(
                    {"action": "open_app", "args": {"app": app_id}}
                )

    normalized_text = re.sub(r"[^\w\s.-]", " ", text)
    normalized_text = re.sub(r"[-_]", " ", normalized_text)
    normalized_text = re.sub(r"\s+", " ", normalized_text).strip()
    for app_alias in sorted(custom_apps(), key=len, reverse=True):
        alias = app_alias.replace("_", " ")
        if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized_text) and (
            _has(text, "open", "khol", "kholo", "launch", "start", "chalao")
            or normalized_text == alias
        ):
            return normalize_plan(
                {"action": "open_app", "args": {"app": app_alias}}
            )

    if _has(text, "google par", "google pe", "search on google", "google search"):
        query = _clean_query(text, "google")
        if query:
            return normalize_plan(
                {"action": "web_search", "args": {"query": query}}
            )
    if _has(text, "youtube par", "youtube pe", "youtube search", "youtube par search"):
        query = _clean_query(text, "youtube")
        if query:
            return normalize_plan(
                {"action": "youtube_search", "args": {"query": query}}
            )

    if _has(text, "hello", "hi aaru", "hey aaru", "namaste", "kaise ho", "how are you"):
        return normalize_plan(
            {
                "action": "reply",
                "args": {"text": "Namaste! Main theek hoon. Aap kya karna chahenge?"},
            }
        )
    if _has(text, "help", "what can you do", "kya kar sakti", "kya kar sakte"):
        return normalize_plan(
            {
                "action": "reply",
                "args": {
                    "text": (
                        "Main apps/websites khol sakti hoon, search, date/time, "
                        "battery/system info, volume/brightness, screenshots, "
                        "notes aur authorized cybersecurity lessons mein madad "
                        "kar sakti hoon. General AI chat ke liye local Ollama "
                        "model connect karein."
                    )
                },
            }
        )
    if _has(text, "cybersecurity", "cyber security", "ethical hacking", "nmap", "wireshark"):
        return normalize_plan(
            {"action": "cybersecurity_lesson", "args": {"topic": "fundamentals"}}
        )
    if text in {"quit", "exit", "close aaru"}:
        return normalize_plan(
            {"action": "reply", "args": {"text": "App band karne ke liye Exit button use karein."}}
        )
    return None


def offline_fallback(command):
    return normalize_plan(
        {
            "action": "reply",
            "args": {
                "text": (
                    "Main offline mode mein hoon aur is sawaal ka bharosemand "
                    "jawab abhi nahi de pa rahi. Basic commands chalti rahengi. "
                    "Natural conversation ke liye optional local Ollama model "
                    "connect karein; koi paid API key zaroori nahi."
                )
            },
        }
    )
