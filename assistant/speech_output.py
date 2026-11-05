"""Online Hindi text-to-speech using Google Translate speech."""

import io
import queue
import threading


class SpeechOutput:
    SAMPLE_RATE = 24_000

    def __init__(self):
        self._requests = queue.Queue()
        self._worker = None
        self._worker_lock = threading.Lock()

    def speak(self, text):
        self._start_worker()
        completed = threading.Event()
        result = []
        self._requests.put((text, completed, result))
        completed.wait()
        if result:
            raise result[0]

    def _start_worker(self):
        with self._worker_lock:
            if self._worker is None or not self._worker.is_alive():
                self._worker = threading.Thread(
                    target=self._speech_loop,
                    name="AaruSpeechOutput",
                    daemon=True,
                )
                self._worker.start()

    def _speech_loop(self):
        while True:
            text, completed, result = self._requests.get()
            try:
                audio = self._synthesize(text)
                self._play(audio)
            except Exception as exc:
                result.append(exc)
            finally:
                completed.set()
                self._requests.task_done()

    @classmethod
    def _synthesize(cls, text):
        try:
            from gtts import gTTS
        except ImportError as exc:
            raise RuntimeError(
                "Online Hindi voice dependency is missing. "
                "Run `python -m pip install -r requirements.txt`."
            ) from exc

        audio = io.BytesIO()
        language = (
            "hi"
            if any("\u0900" <= character <= "\u097f" for character in text)
            else "en"
        )
        try:
            gTTS(
                text=text,
                lang=language,
                slow=False,
                timeout=(5, 15),
            ).write_to_fp(audio)
        except Exception as exc:
            raise RuntimeError(f"Google speech request failed: {exc}") from exc
        if not audio.getbuffer().nbytes:
            raise RuntimeError("Google speech returned no audio.")
        return audio.getvalue()

    @classmethod
    def _play(cls, audio):
        try:
            import av
            import numpy as np
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError(
                "Audio playback dependencies are missing. "
                "Run `python -m pip install -r requirements.txt`."
            ) from exc

        frames = []
        with av.open(io.BytesIO(audio), format="mp3") as media:
            stream = media.streams.audio[0]
            resampler = av.AudioResampler(
                format="s16",
                layout="mono",
                rate=cls.SAMPLE_RATE,
            )
            for decoded in media.decode(stream):
                frames.extend(resampler.resample(decoded))
            frames.extend(resampler.resample(None))
        samples = [frame.to_ndarray().reshape(-1) for frame in frames]
        if not samples:
            raise RuntimeError("The Hindi speech audio could not be decoded.")
        sd.play(np.concatenate(samples), cls.SAMPLE_RATE, blocking=True)
