"""Local wake-word and multilingual speech recognition."""

import json
import math
import os
import queue
import re
import threading
from collections import deque

from config import MODELS_DIR, MODEL_NAME, VOSK_MODEL_DIR


SAMPLE_RATE = 16_000
BLOCK_SIZE = 1_600
MAX_UTTERANCE_SECONDS = 20
SILENCE_BLOCKS = 5
SPEECH_THRESHOLD = 120
WAKE_WORDS = ("aaru", "aaroo", "aru", "arrow", "आरू", "आरु")
TRANSCRIPTION_PROMPT = (
    "Hindi, Hinglish, or English conversation. Common Hindi words: आरू, "
    "आराही, सुनो, बताओ, क्या, कैसे, तुम्हें, किसने, बनाया, देश, भारत, "
    "नहीं, मुझे, मेरा, खोलो, सुनाओ. Transcribe the words that were actually spoken."
)


class OfflineVoiceEngine:
    def __init__(self, on_command, on_status=lambda _status: None):
        self.on_command = on_command
        self.on_status = on_status
        self._audio_queue = queue.Queue(maxsize=32)
        self._stop_event = threading.Event()
        self._stream = None
        self._worker = None
        self._whisper = None
        self._whisper_lock = threading.Lock()
        self._generation = 0
        self._listening = False
        self._conversation_resume = threading.Event()
        self._transcribe_lock = threading.Lock()

    @property
    def listening(self):
        return self._listening

    def _audio_callback(self, indata, _frames, _time, status):
        if status:
            self.on_status(f"Microphone status: {status}")
        try:
            self._audio_queue.put_nowait(bytes(indata))
        except queue.Full:
            self.on_status("Audio buffer full; pausing recognition briefly.")

    def start(self):
        if self.listening:
            return
        while True:
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
        if not (VOSK_MODEL_DIR / "conf" / "model.conf").is_file():
            raise FileNotFoundError(
                "Offline wake-word model is missing. Run "
                "`python download_models.py --wake-word` first."
            )
        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer, Model
        except ImportError as exc:
            raise RuntimeError(
                "Voice dependencies are missing. Run `python -m pip install -r requirements.txt`."
            ) from exc

        model = Model(str(VOSK_MODEL_DIR))
        self._recognizer_factory = lambda: KaldiRecognizer(model, SAMPLE_RATE)
        self._recognizer = self._recognizer_factory()
        self._recognizer.SetWords(False)
        self._stop_event.clear()
        self._generation += 1
        self._listening = True
        self._worker = threading.Thread(target=self._listen_loop, daemon=True)
        self._stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        )
        try:
            self._stream.start()
            self._worker.start()
        except Exception:
            stream, self._stream = self._stream, None
            self._listening = False
            if stream is not None:
                stream.close()
            raise
        self.on_status("Wake word active; mic audio stays on this device until Aaru wakes.")

    def start_conversation(self):
        if self.listening:
            return
        self.on_status("Aaru ka Hindi/English voice model load ho raha hai...")
        self.prepare()
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError(
                "Voice dependencies are missing. Run `python -m pip install -r requirements.txt`."
            ) from exc

        while True:
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
        self._stop_event.clear()
        self._conversation_resume.clear()
        self._generation += 1
        self._listening = True
        self._stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        )
        try:
            self._stream.start()
            self._worker = threading.Thread(
                target=self._conversation_loop,
                name="AaruVoiceChat",
                daemon=True,
            )
            self._worker.start()
        except Exception:
            stream, self._stream = self._stream, None
            self._listening = False
            if stream is not None:
                stream.close()
            raise
        self.on_status("Voice chat active. Aaru sun rahi hai; bolna khatam karein to jawab degi.")

    def resume_conversation(self):
        if self._listening and not self._stop_event.is_set():
            self._conversation_resume.set()

    def stop(self):
        self._stop_event.set()
        self._conversation_resume.set()
        self._generation += 1
        self._listening = False
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
            except Exception as exc:
                self.on_status(f"Microphone stop error: {exc}")
            try:
                stream.close()
            except Exception as exc:
                self.on_status(f"Microphone close error: {exc}")
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=3)
        self._worker = None
        self.on_status("Voice chat off. Microphone is not being read.")

    @staticmethod
    def _find_wake_word(text):
        normalized = text.casefold()
        for wake_word in WAKE_WORDS:
            index = normalized.find(wake_word.casefold())
            if index >= 0:
                return index, index + len(wake_word)
        return None

    def _listen_loop(self):
        try:
            self._listen_loop_inner()
        except Exception as exc:
            self.on_status(f"Wake-word listener stopped after an audio error: {exc}")

    def _listen_loop_inner(self):
        frame_buffer = []
        waiting_for_command = False
        buffer_limit = (SAMPLE_RATE * 2) * MAX_UTTERANCE_SECONDS
        buffered_bytes = 0
        while not self._stop_event.is_set():
            try:
                data = self._audio_queue.get(timeout=0.25)
            except queue.Empty:
                continue
            frame_buffer.append(data)
            buffered_bytes += len(data)

            if buffered_bytes > buffer_limit:
                frame_buffer.clear()
                buffered_bytes = 0
                self._recognizer = self._recognizer_factory()
                waiting_for_command = False
                self.on_status("Speech was too long; waiting for the wake word again.")
                continue

            if not self._recognizer.AcceptWaveform(data):
                continue

            try:
                recognized = json.loads(self._recognizer.Result()).get("text", "").strip()
            except (json.JSONDecodeError, AttributeError):
                recognized = ""
            frames = b"".join(frame_buffer)
            frame_buffer.clear()
            buffered_bytes = 0
            self._recognizer = self._recognizer_factory()

            if waiting_for_command:
                waiting_for_command = False
                if recognized:
                    self._transcribe_async(frames)
                else:
                    self.on_status("No command heard. Say Aaru to try again.")
                continue

            wake = self._find_wake_word(recognized)
            if wake is None:
                continue
            tail = recognized[wake[1]:].strip(" ,.!?")
            if tail:
                self._transcribe_async(frames)
            else:
                waiting_for_command = True
                self.on_status("Aaru sun rahi hai. Ab apna command boliye.")

    @staticmethod
    def _audio_level(data):
        samples = memoryview(data).cast("h")
        if not samples:
            return 0.0
        return math.sqrt(sum(sample * sample for sample in samples) / len(samples))

    def _conversation_loop(self):
        try:
            self._conversation_loop_inner()
        except Exception as exc:
            if not self._stop_event.is_set():
                self.on_status(f"Voice chat stopped after an audio error: {exc}")
            self._stop_event.set()
        finally:
            stream, self._stream = self._stream, None
            if stream is not None:
                try:
                    stream.stop()
                except Exception as exc:
                    self.on_status(f"Microphone stop error: {exc}")
                try:
                    stream.close()
                except Exception as exc:
                    self.on_status(f"Microphone close error: {exc}")
            self._listening = False

    def _conversation_loop_inner(self):
        preroll = deque(maxlen=2)
        frames = []
        speech_started = False
        silence_blocks = 0
        max_blocks = int(MAX_UTTERANCE_SECONDS * SAMPLE_RATE / (BLOCK_SIZE))
        generation = self._generation

        while not self._stop_event.is_set():
            try:
                data = self._audio_queue.get(timeout=0.25)
            except queue.Empty:
                continue

            level = self._audio_level(data)
            if not speech_started:
                preroll.append(data)
                if level < SPEECH_THRESHOLD:
                    continue
                frames = list(preroll)
                speech_started = True
                silence_blocks = 0
                self.on_status("Aaru sun rahi hai...")
            else:
                frames.append(data)
                silence_blocks = silence_blocks + 1 if level < SPEECH_THRESHOLD else 0

            if len(frames) < max_blocks and silence_blocks < SILENCE_BLOCKS:
                continue

            self._pause_conversation_stream()
            pcm_frames = b"".join(frames)
            frames = []
            preroll.clear()
            speech_started = False
            silence_blocks = 0

            self.on_status("Aaru aapki baat samajh rahi hai...")
            transcript = self._transcribe_pcm(pcm_frames)
            transcript = self._remove_wake_word(transcript)
            if self._stop_event.is_set() or generation != self._generation:
                break
            if transcript:
                self._conversation_resume.clear()
                self.on_command(transcript)
                while (
                    not self._stop_event.is_set()
                    and not self._conversation_resume.wait(timeout=0.25)
                ):
                    pass
            else:
                self.on_status("Awaaz samajh nahi aayi. Dobara boliye.")

            if not self._stop_event.is_set():
                self._resume_conversation_stream()
                self.on_status("Aaru sun rahi hai. Aap bol sakte hain.")

    def _pause_conversation_stream(self):
        stream, self._stream = self._stream, None
        if stream is not None:
            stream.stop()
            stream.close()
        while True:
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

    def _resume_conversation_stream(self):
        import sounddevice as sd

        stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        )
        try:
            stream.start()
        except Exception:
            stream.close()
            raise
        self._stream = stream

    def _transcribe_async(self, pcm_frames):
        if not self._transcribe_lock.acquire(blocking=False):
            self.on_status("Aaru is still processing the previous voice command.")
            return
        generation = self._generation
        worker = threading.Thread(
            target=self._transcribe_and_deliver,
            args=(pcm_frames, generation),
            daemon=True,
        )
        try:
            worker.start()
        except RuntimeError:
            self._transcribe_lock.release()
            raise

    def _transcribe_and_deliver(self, pcm_frames, generation):
        try:
            transcript = self._transcribe_pcm(pcm_frames)
            transcript = self._remove_wake_word(transcript)
            if generation != self._generation:
                self.on_status("Stopped listening; the captured command was not run.")
            elif transcript:
                self.on_command(transcript)
            else:
                self.on_status("Command samajh nahi aaya. Dobara try karein.")
        except Exception as exc:
            self.on_status(f"Offline voice recognition error: {exc}")
        finally:
            self._transcribe_lock.release()

    @staticmethod
    def _remove_wake_word(text):
        cleaned = text.strip()
        for wake_word in WAKE_WORDS:
            cleaned = re.sub(
                rf"^\s*{re.escape(wake_word)}[\s,.:;!?-]*",
                "",
                cleaned,
                count=1,
                flags=re.IGNORECASE,
            )
        return cleaned.strip()

    def listen_once(self, seconds=12):
        import sounddevice as sd

        self.on_status(f"Bolna shuru karein ({seconds} seconds)...")
        recording = sd.rec(
            int(seconds * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        transcript = self._transcribe_pcm(recording.tobytes())
        self.on_status("Voice command complete.")
        return transcript.strip()

    def prepare(self):
        self._load_whisper()

    def _load_whisper(self):
        if self._whisper is not None:
            return self._whisper
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "Multilingual offline speech model is not installed. "
                "Run `python download_models.py --speech`."
            ) from exc

        with self._whisper_lock:
            if self._whisper is None:
                MODELS_DIR.mkdir(parents=True, exist_ok=True)
                self._whisper = WhisperModel(
                    MODEL_NAME,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=max(1, min(6, (os.cpu_count() or 2) - 1)),
                    download_root=str(MODELS_DIR),
                )
        return self._whisper

    def _transcribe_pcm(self, pcm_frames):
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError(
                "Multilingual offline speech model is not installed. "
                "Run `python download_models.py --speech`."
            ) from exc

        whisper = self._load_whisper()
        audio = np.frombuffer(pcm_frames, dtype=np.int16).astype(np.float32)
        if audio.size == 0:
            return ""
        audio /= 32_768.0
        segments, info = whisper.transcribe(
            audio,
            language=None,
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=TRANSCRIPTION_PROMPT,
        )
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
        likely_hinglish = bool(
            re.search(
                r"\b(kya|hai|hain|ho|tum|aap|main|mujhe|mera|nahi|nahin|"
                r"kar|karo|kaise|kyun|raha|rahi|rahe|riyo|bolo|kholo|"
                r"suno|chahiye)\b",
                transcript.casefold(),
            )
        )
        has_devanagari = any("\u0900" <= char <= "\u097f" for char in transcript)
        if info.language != "hi" and (
            info.language != "en"
            or info.language_probability < 0.75
            or likely_hinglish
            or has_devanagari
        ):
            segments, retry_info = whisper.transcribe(
                audio,
                language="hi",
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
                initial_prompt=TRANSCRIPTION_PROMPT,
            )
            hindi_transcript = " ".join(
                segment.text.strip() for segment in segments
            ).strip()
            if retry_info.language == "hi" and any(
                "\u0900" <= char <= "\u097f" for char in hindi_transcript
            ):
                transcript = hindi_transcript
        return transcript
