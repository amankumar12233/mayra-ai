import os
import sys
import tempfile
import threading
import unittest
import zipfile
from array import array
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from assistant.conversation import ConversationService
from assistant.models import normalize_plan
from assistant.offline import interpret_offline
from assistant.speech_output import SpeechOutput
from assistant.voice_engine import (
    BLOCK_SIZE,
    MODEL_NAME,
    SAMPLE_RATE,
    SILENCE_BLOCKS,
    SPEECH_THRESHOLD,
    OfflineVoiceEngine,
)
from dashboard.main_window import _render_animated_wallpaper
from download_models import _safe_extract
from security.cybersecurity import get_lesson
from system import actions
from system.apps import SITES, canonical_app, open_app


class DashboardArtworkTests(unittest.TestCase):
    def test_default_wallpaper_ring_frames_animate_without_covering_center(self):
        from PIL import Image

        background = Image.new("RGB", (640, 360), "#020408")
        first_frame = _render_animated_wallpaper(background, 0)
        later_frame = _render_animated_wallpaper(background, 2)

        self.assertEqual(first_frame.size, background.size)
        self.assertNotEqual(first_frame, later_frame)
        self.assertEqual(first_frame.getpixel((320, 180)), background.getpixel((320, 180)))


class PlanValidationTests(unittest.TestCase):
    def test_only_allowlisted_apps_are_accepted(self):
        plan = normalize_plan(
            {"action": "open_app", "args": {"app": "Microsoft Word"}}
        )
        self.assertEqual(plan["args"]["app"], "word")
        with self.assertRaises(ValueError):
            normalize_plan({"action": "open_app", "args": {"app": "arbitrary.exe"}})

    def test_unsafe_url_schemes_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize_plan({"action": "open_url", "args": {"url": "javascript:alert(1)"}})
        with self.assertRaises(ValueError):
            normalize_plan({"action": "open_url", "args": {"url": "file:///secret.txt"}})

    def test_unexpected_arguments_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize_plan(
                {"action": "open_site", "args": {"site": "youtube", "command": "shutdown"}}
            )

    def test_user_paths_cannot_escape_workspace(self):
        with self.assertRaises(ValueError):
            normalize_plan({"action": "summarize_file", "args": {"path": "../secret.txt"}})
        with self.assertRaises(ValueError):
            normalize_plan(
                {
                    "action": "move_file",
                    "args": {"source": "notes.txt", "destination_folder": "../../"},
                }
            )

    def test_invalid_percent_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_plan({"action": "set_volume", "args": {"percent": 101}})

    def test_only_http_and_https_urls_are_normalized(self):
        plan = normalize_plan({"action": "open_url", "args": {"url": "example.com/path"}})
        self.assertEqual(plan["args"]["url"], "https://example.com/path")


class OfflineUnderstandingTests(unittest.TestCase):
    def test_casual_hinglish_song_request_routes_to_youtube_search(self):
        plan = interpret_offline(
            "Aree Aaru YouTube khol ke Salman Khan ka gana suna"
        )
        self.assertEqual(plan["action"], "youtube_search")
        self.assertIn("salman", plan["args"]["query"])

    def test_open_youtube_without_topic_does_not_invent_search(self):
        plan = interpret_offline("Aaru, YouTube kholo")
        self.assertEqual(plan["action"], "open_site")

    def test_open_google_and_search_routes_to_results(self):
        plan = interpret_offline("Open Google and search weather in Delhi")
        self.assertEqual(plan["action"], "web_search")
        self.assertIn("weather", plan["args"]["query"])

    def test_youtube_account_and_channel_controls_open_official_pages(self):
        account = interpret_offline("YouTube account settings kholo")
        self.assertEqual(account["action"], "open_site")
        self.assertEqual(account["args"]["site"], "youtube account")
        self.assertEqual(
            SITES[account["args"]["site"]],
            "https://www.youtube.com/account",
        )

        studio = interpret_offline("YouTube channel kholo")
        self.assertEqual(studio["action"], "open_site")
        self.assertEqual(studio["args"]["site"], "youtube channel")
        self.assertEqual(
            SITES[studio["args"]["site"]],
            "https://studio.youtube.com/",
        )

    def test_gmail_opens_in_the_browser_without_account_credentials(self):
        plan = interpret_offline("Gmail kholo")
        self.assertEqual(plan["action"], "open_site")
        self.assertEqual(plan["args"]["site"], "gmail")
        self.assertEqual(
            SITES[plan["args"]["site"]],
            "https://mail.google.com",
        )

    def test_negated_lock_does_not_lock(self):
        plan = interpret_offline("Aaru, please do not lock my laptop")
        self.assertEqual(plan["action"], "reply")

    def test_basic_spoken_math_is_evaluated_without_eval(self):
        plan = interpret_offline("Aaru, what is 2 plus 2?")
        self.assertEqual(plan["args"]["text"], "Answer: 4")

    def test_lock_requires_a_separate_typed_confirmation(self):
        plan = interpret_offline("Aaru, lock my laptop")
        self.assertEqual(plan["action"], "system_action")
        self.assertEqual(plan["args"]["action"], "lock")
        with patch("system.actions.controls.system_action") as system_action:
            executed = actions.execute_plan(None, plan, confirm_action=None)
        self.assertFalse(executed)
        system_action.assert_not_called()

    def test_system_action_requires_exact_confirmation_token(self):
        plan = {"action": "system_action", "args": {"action": "shutdown"}}
        with patch("system.actions.controls.system_action") as system_action:
            executed = actions.execute_plan(
                None,
                plan,
                confirm_action=lambda _description, phrase: phrase == "SHUT DOWN MY COMPUTER",
            )
        self.assertTrue(executed)
        system_action.assert_called_once_with("shutdown")

    def test_offline_general_question_does_not_claim_ai_answer(self):
        service = ConversationService({"provider": "offline"})
        plan = service.plan("Who discovered a new planet yesterday?")
        self.assertEqual(plan["action"], "reply")
        self.assertIn("offline mode", plan["args"]["text"])

    def test_common_roman_hindi_conversation_is_answered_without_slow_model(self):
        language = interpret_offline("kya tum hindi me baat kr sata ho")
        self.assertEqual(language["action"], "reply")
        self.assertIn("Haan", language["args"]["text"])
        capabilities = interpret_offline("tum kya kya ker sakta ho")
        self.assertEqual(capabilities["action"], "reply")
        self.assertIn("apps aur websites", capabilities["args"]["text"])
        personal = interpret_offline("me kuch nhi ker sakta tum apna batao")
        self.assertIn("Aarohi AI hoon", personal["args"]["text"])
        small_talk = interpret_offline("bolo kya hua")
        self.assertIn("Kuch nahi hua", small_talk["args"]["text"])

    def test_creator_question_names_krishna_kant_in_all_languages(self):
        questions = {
            "tumhe kisna banaya hai": "Krishna Kant",
            "tumhe kisne banaya": "Krishna Kant",
            "तुमें किसने मनाया है": "कृष्णा कांत",
            "Who created you?": "Krishna Kant",
            "तुम्हें किसने बनाया?": "कृष्णा कांत",
        }
        for question, creator in questions.items():
            with self.subTest(question=question):
                reply = interpret_offline(question)
                self.assertEqual(reply["action"], "reply")
                self.assertIn(creator, reply["args"]["text"])
        self.assertEqual(
            interpret_offline("tumhe kisne banaya hai")["args"]["text"],
            "Mujhe Krishna Kant ne banaya hai.",
        )
        self.assertIn(
            "nickname Aman Kumar",
            interpret_offline("Krishna Kant kaun hain?")["args"]["text"],
        )

    def test_creator_and_country_questions_have_separate_short_answers(self):
        self.assertEqual(
            interpret_offline("tumhe kisne banaya hai")["args"]["text"],
            "Mujhe Krishna Kant ne banaya hai.",
        )
        self.assertEqual(
            interpret_offline("tum kis country me bani ho")["args"]["text"],
            "Main India mein bani hoon.",
        )
        self.assertEqual(
            interpret_offline("tumhe kis country ne banaya")["args"]["text"],
            "Main India mein bani hoon.",
        )
        self.assertEqual(
            interpret_offline("तुम्हें किस देश में बनाया")["args"]["text"],
            "मैं भारत में बनी हूँ।",
        )
        self.assertEqual(
            interpret_offline("Which country were you made in?")["args"]["text"],
            "I was made in India.",
        )

    def test_aarohi_and_crush_questions_give_the_requested_ai_identity(self):
        questions = {
            "Aarohi kaun hai?": "Aarohi Krishna Kant ki crush hai.",
            "Who is your crush?": "Aarohi is Krishna Kant's crush.",
            "आराही कौन है?": "आराही, कृष्णा कांत की क्रश है।",
        }
        for question, answer in questions.items():
            with self.subTest(question=question):
                reply = interpret_offline(question)
                self.assertEqual(reply["action"], "reply")
                self.assertEqual(answer, reply["args"]["text"])
        self.assertEqual(
            interpret_offline("tumhari crush kaun hai")["args"]["text"],
            "Aarohi Krishna Kant ki crush hai.",
        )

    def test_creator_question_is_answered_before_using_an_ai_provider(self):
        service = ConversationService({"provider": "ollama"})
        with patch.object(service, "_ollama_plan") as ollama_plan:
            reply = service.plan("tumhe kisne banaya hai")
        self.assertIn("Krishna Kant", reply["args"]["text"])
        ollama_plan.assert_not_called()

    def test_identity_question_says_aaru_is_an_ai_not_a_human(self):
        questions = {
            "tum ai ho ya insaan": "AI assistant hoon, asli insaan nahi",
            "are you a real person?": "AI assistant, not a real person",
            "क्या तुम इंसान हो?": "AI assistant हूँ, असली इंसान नहीं",
        }
        for question, answer in questions.items():
            with self.subTest(question=question):
                reply = interpret_offline(question)
                self.assertEqual(reply["action"], "reply")
                self.assertIn(answer, reply["args"]["text"])

    def test_defensive_security_lesson_is_local_and_non_executing(self):
        plan = interpret_offline("Explain Nmap")
        self.assertEqual(plan["action"], "cybersecurity_lesson")
        self.assertIn("written permission", get_lesson(plan["args"]["topic"]))

    def test_virus_scan_request_opens_windows_security_only(self):
        for request in ("Aaru, mera virus scan karo", "Windows Security kholo"):
            with self.subTest(request=request):
                plan = interpret_offline(request)
                self.assertEqual(plan["action"], "open_security")
        with patch("system.actions.controls.open_windows_security") as open_security:
            messages = []
            actions.execute_plan(
                None,
                {"action": "open_security", "args": {}},
                output=messages.append,
            )
        open_security.assert_called_once_with()
        self.assertIn("Quick scan", messages[0])

    def test_protection_off_request_never_turns_off_security(self):
        plan = interpret_offline("turn off Windows Defender")
        self.assertEqual(plan["action"], "cybersecurity_lesson")
        self.assertIn("Keep antivirus", get_lesson(plan["args"]["topic"]))

    def test_close_named_app_requires_confirmation_and_never_force_kills(self):
        plan = interpret_offline("Aaru, Chrome band karo")
        self.assertEqual(plan["action"], "close_app")
        self.assertEqual(plan["args"]["app"], "chrome")
        windows = [type("Window", (), {"title": "Browser - Example"})()]
        with patch("system.actions.controls.find_app_windows", return_value=windows):
            with patch("system.actions.controls.request_window_close") as close:
                executed = actions.execute_plan(
                    None,
                    plan,
                    confirm_action=lambda _description, phrase: phrase == "CLOSE APP",
                )
        self.assertTrue(executed)
        close.assert_called_once_with(windows)

    def test_close_app_without_confirmation_does_not_close_window(self):
        plan = {"action": "close_app", "args": {"app": "Chrome"}}
        windows = [type("Window", (), {"title": "Browser - Example"})()]
        with patch("system.actions.controls.find_app_windows", return_value=windows):
            with patch("system.actions.controls.request_window_close") as close:
                executed = actions.execute_plan(None, plan)
        self.assertFalse(executed)
        close.assert_not_called()

    def test_close_all_apps_request_only_offers_individual_confirmed_closing(self):
        plan = interpret_offline("close all apps")
        self.assertEqual(plan["action"], "reply")
        self.assertIn("typed confirmation", plan["args"]["text"])

    def test_kali_and_sudo_su_requests_get_safe_explanations(self):
        for request in ("Kali Linux commands batao", "Aaru, sudo su kya karta hai?"):
            with self.subTest(request=request):
                plan = interpret_offline(request)
                self.assertEqual(plan["action"], "cybersecurity_lesson")
                self.assertEqual(plan["args"]["topic"], "linux")
        lesson = get_lesson("linux")
        self.assertIn("root (administrator) shell", lesson)
        self.assertIn("`exit` type karke", lesson)
        self.assertIn("Aaru commands run nahi karti", lesson)

    def test_network_attack_request_is_redirected_to_education(self):
        plan = interpret_offline("hack my neighbor wifi")
        self.assertEqual(plan["action"], "cybersecurity_lesson")
        self.assertIn("permission", get_lesson(plan["args"]["topic"]))


class VoiceHelperTests(unittest.TestCase):
    def test_wake_word_and_prefix_cleanup(self):
        self.assertIsNotNone(OfflineVoiceEngine._find_wake_word("Aaru, open YouTube"))
        self.assertEqual(
            OfflineVoiceEngine._remove_wake_word("Aaru, open YouTube"),
            "open YouTube",
        )

    def test_audio_level_uses_pcm_signal(self):
        pcm = array("h", [1000, -1000, 1000, -1000]).tobytes()
        self.assertEqual(OfflineVoiceEngine._audio_level(pcm), 1000)
        self.assertEqual(OfflineVoiceEngine._audio_level(b""), 0)

    def test_continuous_voice_chat_transcribes_after_silence(self):
        class FakeStream:
            def __init__(self, **kwargs):
                self.closed = False

            def start(self):
                pass

            def stop(self):
                pass

            def close(self):
                self.closed = True

        fake_sounddevice = SimpleNamespace(RawInputStream=FakeStream)
        commands = []
        delivered = threading.Event()
        engine = OfflineVoiceEngine(
            on_command=lambda text: (
                commands.append(text),
                delivered.set(),
                engine.resume_conversation(),
            )
        )
        quiet = array("h", [0] * BLOCK_SIZE).tobytes()
        speech = array("h", [180] * BLOCK_SIZE).tobytes()

        with patch.dict("sys.modules", {"sounddevice": fake_sounddevice}):
            with patch.object(engine, "_transcribe_pcm", return_value="hello there"):
                with patch.object(engine, "prepare"):
                    engine.start_conversation()
                    try:
                        for frame in (
                            quiet,
                            quiet,
                            speech,
                            *(quiet for _ in range(SILENCE_BLOCKS)),
                        ):
                            engine._audio_queue.put(frame)
                        self.assertTrue(delivered.wait(timeout=3))
                        self.assertEqual(commands, ["hello there"])
                        self.assertTrue(engine.listening)
                    finally:
                        engine.stop()

    def test_voice_chat_prepares_speech_model_before_opening_microphone(self):
        calls = []

        class FakeStream:
            def __init__(self, **_kwargs):
                calls.append("microphone")

            def start(self):
                pass

            def stop(self):
                pass

            def close(self):
                pass

        engine = OfflineVoiceEngine(lambda _text: None)
        engine.prepare = lambda: calls.append("model")
        fake_sounddevice = SimpleNamespace(RawInputStream=FakeStream)
        with patch.dict("sys.modules", {"sounddevice": fake_sounddevice}):
            engine.start_conversation()
            engine.stop()

        self.assertEqual(calls[:2], ["model", "microphone"])

    def test_voice_chat_uses_more_sensitive_mic_and_shorter_turn_pause(self):
        self.assertEqual(SPEECH_THRESHOLD, 120)
        self.assertEqual(MODEL_NAME, "base")
        self.assertLessEqual(SILENCE_BLOCKS * BLOCK_SIZE / SAMPLE_RATE, 0.5)

    def test_voice_chat_preloads_whisper_model_only_once(self):
        created = []

        class FakeWhisperModel:
            def __init__(self, model_name, **kwargs):
                created.append((model_name, kwargs))

        engine = OfflineVoiceEngine(lambda _text: None)
        fake_module = SimpleNamespace(WhisperModel=FakeWhisperModel)
        with tempfile.TemporaryDirectory() as root:
            with patch("assistant.voice_engine.MODELS_DIR", Path(root)):
                with patch.dict("sys.modules", {"faster_whisper": fake_module}):
                    engine.prepare()
                    engine.prepare()

        self.assertEqual(len(created), 1)
        self.assertEqual(created[0][0], "base")
        self.assertEqual(created[0][1]["compute_type"], "int8")

    def test_speech_transcription_retries_misdetected_language_as_hindi(self):
        calls = []

        class FakeWhisper:
            def transcribe(self, _audio, **kwargs):
                calls.append(kwargs)
                language = kwargs["language"]
                if language is None:
                    return iter([SimpleNamespace(text="wrong language")]), SimpleNamespace(
                        language="en",
                        language_probability=0.1,
                    )
                return iter([SimpleNamespace(text="साफ हिंदी")]), SimpleNamespace(
                    language="hi",
                    language_probability=0.99,
                )

        engine = OfflineVoiceEngine(lambda _text: None)
        engine._whisper = FakeWhisper()
        pcm = np.array([1000, -1000], dtype=np.int16).tobytes()

        self.assertEqual(engine._transcribe_pcm(pcm), "साफ हिंदी")
        self.assertEqual([call["language"] for call in calls], [None, "hi"])
        self.assertTrue(all(call["beam_size"] == 1 for call in calls))
        self.assertTrue(all("Hinglish" in call["initial_prompt"] for call in calls))

    def test_speech_transcription_retries_english_detected_hinglish_as_hindi(self):
        calls = []

        class FakeWhisper:
            def transcribe(self, _audio, **kwargs):
                calls.append(kwargs)
                if kwargs["language"] is None:
                    return iter([SimpleNamespace(text="Kya tum riyo")]), SimpleNamespace(
                        language="en",
                        language_probability=0.98,
                    )
                return iter([SimpleNamespace(text="क्या तुम सुन रही हो")]), SimpleNamespace(
                    language="hi",
                    language_probability=0.99,
                )

        engine = OfflineVoiceEngine(lambda _text: None)
        engine._whisper = FakeWhisper()
        pcm = np.array([1000, -1000], dtype=np.int16).tobytes()

        self.assertEqual(engine._transcribe_pcm(pcm), "क्या तुम सुन रही हो")
        self.assertEqual([call["language"] for call in calls], [None, "hi"])

    def test_speech_transcription_retries_garbled_devanagari_detected_as_english(self):
        calls = []

        class FakeWhisper:
            def transcribe(self, _audio, **kwargs):
                calls.append(kwargs)
                if kwargs["language"] is None:
                    return iter([SimpleNamespace(text="ताना किस ने बनाया")]), SimpleNamespace(
                        language="en",
                        language_probability=0.99,
                    )
                return iter([SimpleNamespace(text="तुम्हें किसने बनाया")]), SimpleNamespace(
                    language="hi",
                    language_probability=0.99,
                )

        engine = OfflineVoiceEngine(lambda _text: None)
        engine._whisper = FakeWhisper()
        pcm = np.array([1000, -1000], dtype=np.int16).tobytes()

        self.assertEqual(engine._transcribe_pcm(pcm), "तुम्हें किसने बनाया")
        self.assertEqual([call["language"] for call in calls], [None, "hi"])

    def test_speech_output_serializes_requests_on_one_thread(self):
        calls = []
        output = SpeechOutput()
        output._synthesize = lambda text: calls.append(
            ("synthesize", text, threading.get_ident())
        )
        output._play = lambda _audio: calls.append(
            ("play", None, threading.get_ident())
        )

        with patch.object(output, "_synthesize", wraps=output._synthesize):
            output.speak("first")
            output.speak("second")

        thread_ids = {thread_id for _operation, _text, thread_id in calls}
        self.assertEqual(len(thread_ids), 1)
        self.assertEqual(
            [text for operation, text, _thread_id in calls if operation == "synthesize"],
            ["first", "second"],
        )

    def test_speech_output_uses_google_hindi_for_devanagari(self):
        requests = []

        class FakeGoogleTTS:
            def __init__(self, **kwargs):
                requests.append(kwargs)

            def write_to_fp(self, audio):
                audio.write(b"audio")

        fake_gtts = SimpleNamespace(gTTS=FakeGoogleTTS)
        with patch.dict("sys.modules", {"gtts": fake_gtts}):
            audio = SpeechOutput._synthesize("नमस्ते")

        self.assertEqual(audio, b"audio")
        self.assertEqual(requests[0]["text"], "नमस्ते")
        self.assertEqual(requests[0]["lang"], "hi")

    def test_speech_output_uses_english_for_latin_script(self):
        requests = []

        class FakeGoogleTTS:
            def __init__(self, **kwargs):
                requests.append(kwargs)

            def write_to_fp(self, audio):
                audio.write(b"audio")

        fake_gtts = SimpleNamespace(gTTS=FakeGoogleTTS)
        with patch.dict("sys.modules", {"gtts": fake_gtts}):
            SpeechOutput._synthesize("Hello, how are you?")

        self.assertEqual(requests[0]["lang"], "en")


class ModelArchiveTests(unittest.TestCase):
    def test_voice_model_archive_rejects_parent_directory_paths(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            archive = base / "unsafe.zip"
            destination = base / "extract"
            destination.mkdir()
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("../outside.txt", "unsafe")
            with self.assertRaises(ValueError):
                _safe_extract(archive, destination)
            self.assertFalse((base / "outside.txt").exists())

    def test_voice_model_archive_limits_total_extracted_size(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            archive = base / "large.zip"
            destination = base / "extract"
            destination.mkdir()
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("first", "1234")
                zipped.writestr("second", "5678")
            with patch("download_models.MAX_WAKE_MODEL_BYTES", 6):
                with self.assertRaises(ValueError):
                    _safe_extract(archive, destination)


class LocalModelPolicyTests(unittest.TestCase):
    def test_api_key_is_not_saved_in_settings(self):
        import config

        with tempfile.TemporaryDirectory() as root:
            data_dir = Path(root)
            settings_path = data_dir / "settings.json"
            with patch("config.DATA_DIR", data_dir), patch(
                "config.SETTINGS_PATH", settings_path
            ):
                config.save_settings(
                    {
                        **config.DEFAULT_SETTINGS,
                        "OPENAI_API_KEY": "test-key-not-real",
                    }
                )
            saved_settings = settings_path.read_text(encoding="utf-8")
            self.assertNotIn("OPENAI_API_KEY", saved_settings)
            self.assertNotIn("test-key-not-real", saved_settings)

    def test_ollama_endpoint_must_be_loopback_only(self):
        service = ConversationService(
            {
                "provider": "ollama",
                "ollama_url": "http://example.com:11434",
                "ollama_model": "qwen2.5:1.5b",
            }
        )
        with self.assertRaises(ValueError):
            service._ollama_url()

    def test_ollama_request_bounds_generation_and_history(self):
        import json

        service = ConversationService(
            {
                "provider": "ollama",
                "ollama_url": "http://127.0.0.1:11434",
                "ollama_model": "qwen2.5:1.5b",
            }
        )
        response_body = {
            "message": {
                "content": '{"action":"reply","args":{"text":"Main madad kar sakti hoon."},"message":""}'
            }
        }

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return json.dumps(response_body).encode("utf-8")

        history = [
            {"role": "user", "content": f"old question {index}"}
            for index in range(12)
        ]
        with patch(
            "assistant.conversation.urllib.request.build_opener"
        ) as build_opener:
            build_opener.return_value.open.return_value = FakeResponse()
            plan = service._ollama_plan("Aap kya kar sakti ho?", history)

        request = build_opener.return_value.open.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["options"]["num_predict"], 192)
        self.assertEqual(body["options"]["num_ctx"], 3072)
        self.assertEqual(body["options"]["num_thread"], 4)
        self.assertEqual(body["keep_alive"], "10m")
        self.assertEqual(len(body["messages"]), 8)
        self.assertEqual(plan["action"], "reply")

    def test_model_reply_with_nonstandard_args_is_salvaged_as_safe_text(self):
        response = ConversationService._normalize_model_response(
            '{"action":"reply","args":"Hindi mein jawab.","message":""}'
        )
        self.assertEqual(response["action"], "reply")
        self.assertEqual(response["args"]["text"], "Hindi mein jawab.")

    def test_invalid_non_reply_model_plan_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "safe action format"):
            ConversationService._normalize_model_response(
                '{"action":"open_app","args":null,"message":""}'
            )

    def test_openai_provider_requires_key_and_never_uses_fallback(self):
        service = ConversationService({"provider": "openai", "openai_model": "gpt-4o-mini"})
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with self.assertRaisesRegex(RuntimeError, r"OPENAI_API_KEY.*\.env"):
                service.plan("Explain gravity")

    def test_openai_provider_sends_key_and_returns_validated_plan(self):
        service = ConversationService({"provider": "openai", "openai_model": "gpt-4o-mini"})
        response_body = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"action":"reply","args":{"text":"Gravity pulls objects together."},'
                            '"message":""}'
                        )
                    }
                }
            ]
        }

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                import json

                return json.dumps(response_body).encode("utf-8")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-not-real"}):
            with patch("assistant.conversation.urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
                plan = service.plan("Explain gravity")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key-not-real")
        self.assertEqual(plan["action"], "reply")
        self.assertIn("Gravity", plan["args"]["text"])

    def test_openrouter_provider_uses_its_key_endpoint_and_model(self):
        import json

        service = ConversationService(
            {"provider": "openrouter", "openrouter_model": "openrouter/auto"}
        )
        response_body = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"action":"reply","args":{"text":"Namaste!"},"message":""}'
                        )
                    }
                }
            ]
        }

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return json.dumps(response_body).encode("utf-8")

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-not-real"}):
            with patch(
                "assistant.conversation.urllib.request.urlopen",
                return_value=FakeResponse(),
            ) as urlopen:
                plan = service.plan("Namaste")
        request = urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(
            request.full_url,
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key-not-real")
        self.assertEqual(body["model"], "openrouter/auto")
        self.assertEqual(plan["action"], "reply")
        self.assertEqual(plan["args"]["text"], "Namaste!")

    def test_openrouter_provider_requires_its_own_key(self):
        service = ConversationService(
            {"provider": "openrouter", "openrouter_model": "openrouter/auto"}
        )
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
            with self.assertRaisesRegex(RuntimeError, "OPENROUTER_API_KEY"):
                service.plan("Namaste")


class LocalAppTests(unittest.TestCase):
    def test_app_alias_normalization(self):
        self.assertEqual(canonical_app("VS Code"), "vscode")
        self.assertIsNone(canonical_app("powershell.exe"))

    def test_windows_excel_launch_uses_absolute_executable_not_office_protocol(self):
        import system.apps as app_registry

        with tempfile.TemporaryDirectory() as root:
            excel = Path(root) / "EXCEL.EXE"
            excel.touch()
            with (
                patch("system.apps.sys.platform", "win32"),
                patch.object(app_registry, "WINDOWS_PATHS", {"excel": (excel,)}),
                patch("system.apps.shutil.which", return_value=None),
                patch("system.apps.subprocess.Popen") as popen,
            ):
                self.assertEqual(open_app("Excel"), "excel")
            popen.assert_called_once_with([str(excel)], shell=False)

    def test_windows_notepad_launch_uses_absolute_system_executable(self):
        import system.apps as app_registry

        with tempfile.TemporaryDirectory() as root:
            system_root = Path(root)
            notepad = system_root / "System32" / "notepad.exe"
            notepad.parent.mkdir()
            notepad.touch()
            with (
                patch("system.apps.sys.platform", "win32"),
                patch.dict(os.environ, {"SystemRoot": str(system_root)}),
                patch("system.apps.shutil.which", return_value=None),
                patch("system.apps.subprocess.Popen") as popen,
            ):
                self.assertEqual(open_app("Notepad"), "notepad")
            popen.assert_called_once_with([str(notepad)], shell=False)

    def test_custom_app_must_be_added_by_the_user_before_voice_can_open_it(self):
        import system.apps as app_registry

        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            if sys.platform == "win32":
                target = base / "player.exe"
                target.touch()
            elif sys.platform == "darwin":
                target = base / "Player.app"
                target.mkdir()
            else:
                target = base / "player"
                target.touch()
                target.chmod(target.stat().st_mode | 0o111)
            registry_path = base / "custom_apps.json"
            with patch("system.apps.CUSTOM_APPS_PATH", registry_path):
                app_registry.custom_apps.cache_clear()
                app_registry.register_custom_app("My Player", target)
                self.assertEqual(canonical_app("my player"), "custom:my_player")
                plan = interpret_offline("Aaru, open My Player")
                self.assertEqual(plan["action"], "open_app")
                self.assertEqual(plan["args"]["app"], "custom:my_player")
                with patch("system.apps._launch") as launch:
                    actions.execute_plan(None, plan)
                    launch.assert_called_once()
            app_registry.custom_apps.cache_clear()

    def test_website_is_opened_without_running_a_command(self):
        with patch("system.actions.webbrowser.open") as open_browser:
            actions.execute_plan(
                None,
                {"action": "youtube_search", "args": {"query": "Salman Khan songs"}},
            )
        open_browser.assert_called_once()
        self.assertIn("youtube.com/results", open_browser.call_args.args[0])

    def test_text_file_cannot_escape_its_directory(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root) / "safe"
            base.mkdir()
            outside = Path(root) / "secret.txt"
            outside.write_text("secret", encoding="utf-8")
            with self.assertRaises(ValueError):
                from system.notes import safe_text_file

                safe_text_file("../secret.txt", base)

    def test_summarize_file_reads_validated_text_and_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root) / "safe"
            base.mkdir()
            (base / "notes.txt").write_text("A small UTF-8 note.", encoding="utf-8")
            client = type(
                "SummaryClient",
                (),
                {"answer_file_summary": lambda _self, text: f"Summary: {text}"},
            )()
            messages = []
            with patch("system.actions.SAFE_FILES_DIR", base):
                executed = actions.execute_plan(
                    client,
                    {"action": "summarize_file", "args": {"path": "notes.txt"}},
                    confirm_action=lambda _description, phrase: phrase == "SEND FILE",
                    output=messages.append,
                )
            self.assertTrue(executed)
            self.assertEqual(messages, ["Summary: A small UTF-8 note."])


if __name__ == "__main__":
    unittest.main()
