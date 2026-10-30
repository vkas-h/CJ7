import time
import threading
from pathlib import Path
import numpy as np
import sounddevice as sd
from openwakeword.model import Model


class WakeWord:

    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1280  # 80 ms

    def __init__(
        self,
        model_path: str = "models/hey_cj7.onnx",
        threshold: float = 0.80,
        cooldown: float = 2.0,
    ):
        self.model_path = Path(model_path)
        self.threshold = threshold
        self.cooldown = cooldown

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Wake-word model not found: {self.model_path}"
            )

        self.model = Model(
            wakeword_models=[str(self.model_path)],
            inference_framework="onnx",
        )

        self.stream = None
        self.running = False
        self.detected = threading.Event()
        self.last_detection = 0.0

    def _callback(self, indata, frames, time_info, status):

        if status:
            print(f"Audio status: {status}")

        if self.detected.is_set():
            return

        audio = (indata[:, 0] * 32767).astype(np.int16)

        prediction = self.model.predict(audio)

        score = prediction.get("hey_cj7", 0.0)

        now = time.monotonic()

        if (
            score >= self.threshold
            and now - self.last_detection >= self.cooldown
        ):
            self.last_detection = now

            print(
                f"\n[CJ7] Wake word detected "
                f"(score={score:.3f})"
            )

            self.detected.set()

    def start(self):

        if self.running:
            return

        self.detected.clear()
        self.running = True

        self.stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=self.CHUNK_SIZE,
            callback=self._callback,
        )

        self.stream.start()

        print("[CJ7] Wake-word listener active.")

    def stop(self):

        if not self.running:
            return

        self.running = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.detected.clear()

    def is_detected(self):

        return self.detected.is_set()
        self.stream.start()

        print("[CJ7] Wake-word listener active.")

    def stop(self):
        """Stop microphone wake-word monitoring."""

        if not self.running:
            return

        self.running = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.detected.clear()

    def is_detected(self):
        """Return True if the wake word was detected."""

        return self.detected.is_set()