from pathlib import Path

import sounddevice as sd
from piper import PiperVoice


class TTS:

    def __init__(self):
        self.model_path = (
            Path(__file__).resolve().parent.parent
            / "models"
            / "tts"
            / "en_US-lessac-medium.onnx"
        )

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Piper voice model not found:\n{self.model_path}"
            )

        print("[TTS] Loading voice...")

        self.voice = PiperVoice.load(
            str(self.model_path)
        )

        self.sample_rate = self.voice.config.sample_rate

        print("[TTS] Voice loaded.")

    def speak(self, text):

        if not text or not text.strip():
            return

        import time

        text = text.strip()

        start = time.perf_counter()
        first_chunk_time = None

        with sd.RawOutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=0,
        ) as stream:

            for chunk in self.voice.synthesize(text):

                if first_chunk_time is None:
                    first_chunk_time = time.perf_counter()

                    print(
                        f"[TTS] First audio: "
                        f"{first_chunk_time - start:.3f}s"
                    )

                stream.write(chunk.audio_int16_bytes)

        total = time.perf_counter() - start

        print(f"[TTS] Total: {total:.3f}s")


tts = TTS()


def speak(text):
    tts.speak(text)