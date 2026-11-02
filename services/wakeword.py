
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
from openwakeword.model import Model

from config.settings import config


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class WakeWord:
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1280  # 80 ms, expected by openWakeWord

    def __init__(
        self,
        model_path=None,
        threshold=None,
        cooldown=None,
    ):
        wake_config = config.get("wakeword", {})

        self.debug = bool(wake_config.get("debug", False))
        self._last_score_log = 0.0

        configured_path = model_path or wake_config.get(
            "model_path",
            "models/hey_cj7.onnx",
        )

        self.model_path = Path(configured_path)
        if not self.model_path.is_absolute():
            self.model_path = PROJECT_ROOT / self.model_path

        self.threshold = (
            threshold
            if threshold is not None
            else float(wake_config.get("threshold", 0.5))
        )
        self.cooldown = (
            cooldown
            if cooldown is not None
            else float(wake_config.get("cooldown", 2.0))
        )

        if not 0.0 < self.threshold <= 1.0:
            raise ValueError("Wake-word threshold must be between 0 and 1.")

        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"Wake-word model not found: {self.model_path}"
            )

        print(f"[WAKE] Loading model: {self.model_path}")

        self.model = Model(
            wakeword_models=[str(self.model_path)],
            inference_framework="onnx",
        )

        model_keys = list(self.model.models.keys())

        if len(model_keys) != 1:
            raise RuntimeError(
                "Expected exactly one wake-word model, "
                f"loaded keys: {model_keys}"
            )

        # Use the actual prediction key exposed by openWakeWord.
        self.model_key = model_keys[0]

        self.stream = None
        self.running = False
        self.detected = threading.Event()
        self.last_detection = 0.0
        self.last_score = 0.0

        if self.debug and now - self._last_score_log >= 1.0:
            print(
                f"[WAKE] Listening score: {score:.3f} "
                f"(threshold={self.threshold:.2f})"
            )
            self._last_score_log = now

        self._lock = threading.Lock()

        print(
            f"[WAKE] Model ready: {self.model_key} "
            f"| threshold={self.threshold:.2f}"
        )

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(f"[WAKE] Audio status: {status}")

        if self.detected.is_set():
            return

        try:
            audio = np.clip(
                indata[:, 0] * 32767.0,
                -32768,
                32767,
            ).astype(np.int16)

            prediction = self.model.predict(audio)
            score = float(prediction.get(self.model_key, 0.0))

            self.last_score = score

            now = time.monotonic()

            if (
                score >= self.threshold
                and now - self.last_detection >= self.cooldown
            ):
                self.last_detection = now

                print(
                    f"\n[WAKE] Detected {self.model_key} "
                    f"(score={score:.3f})"
                )

                self.detected.set()

        except Exception as error:
            # Do not let an inference exception silently kill
            # the microphone callback.
            print(f"[WAKE] Prediction error: {error}")

    def start(self):
        with self._lock:
            if self.running:
                return

            self.detected.clear()
            self.last_score = 0.0

            try:
                device = sd.query_devices(kind="input")
                print(
                    f"[WAKE] Input device: {device['name']} "
                    f"| {device['default_samplerate']} Hz"
                )

                self.model.reset()

                self.stream = sd.InputStream(
                    samplerate=self.SAMPLE_RATE,
                    channels=1,
                    dtype="float32",
                    blocksize=self.CHUNK_SIZE,
                    callback=self._callback,
                )

                self.stream.start()
                self.running = True

                print("[WAKE] Listener active.")

            except Exception as error:
                if self.stream is not None:
                    try:
                        self.stream.close()
                    except Exception:
                        pass

                self.stream = None
                self.running = False

                raise RuntimeError(
                    f"Could not start wake-word microphone: {error}"
                ) from error

    def stop(self):
        with self._lock:
            if not self.running:
                return

            self.running = False

            stream = self.stream
            self.stream = None

            if stream is not None:
                try:
                    stream.stop()
                finally:
                    stream.close()

            self.detected.clear()

    def is_detected(self):
        return self.detected.is_set()
