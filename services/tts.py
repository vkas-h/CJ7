
import time
from pathlib import Path

import sounddevice as sd
import onnxruntime as ort
from piper import PiperVoice

from config.settings import config


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TTS:
    def __init__(self):
        tts_config = config.get("tts", {})

        configured_path = tts_config.get(
            "model_path",
            "models/tts/en_US-lessac-medium.onnx",
        )

        self.model_path = Path(configured_path)

        if not self.model_path.is_absolute():
            self.model_path = PROJECT_ROOT / self.model_path

        self.requested_device = tts_config.get("device", "auto").lower()

        if self.requested_device not in ("auto", "cuda", "cpu"):
            raise ValueError(
                "TTS device must be auto, cuda, or cpu."
            )

        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"Piper voice model not found: {self.model_path}"
            )

        self.voice = None
        self.sample_rate = None
        self.device = None

        self._load_voice()

    def _load_voice(self):
        providers = ort.get_available_providers()

        cuda_available = "CUDAExecutionProvider" in providers

        if self.requested_device == "cpu":
            candidates = [False]
        elif cuda_available:
            candidates = [True, False]
        else:
            candidates = [False]

        for use_cuda in candidates:
            target = "CUDA" if use_cuda else "CPU"

            try:
                print(f"[TTS] Loading Piper on {target}...")

                voice = PiperVoice.load(
                    str(self.model_path),
                    use_cuda=use_cuda,
                )

                self.voice = voice
                self.sample_rate = voice.config.sample_rate
                self.device = target

                print(f"[TTS] Piper loaded on {target}.")
                return

            except Exception as error:
                print(
                    f"[TTS] {target} initialisation failed: {error}"
                )

                if use_cuda:
                    print("[TTS] Falling back to CPU.")

        raise RuntimeError(
            "Could not load Piper on either CUDA or CPU."
        )

    def speak(self, text):
        if not text or not text.strip():
            return

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

        print(
            f"[TTS] Total: {total:.3f}s | Device: {self.device}"
        )


tts = TTS()


def speak(text):
    tts.speak(text)
