
from pathlib import Path

from config.settings import config


class STT:
    def __init__(self):
        stt_config = config.get("stt", {})

        self.engine = stt_config.get("engine", "phonon").lower()
        self.model_name = stt_config.get("model", "phonon-2")
        self.hotwords = stt_config.get("hotwords", ["CJ7"])

        if len(self.hotwords) > 25:
            raise ValueError("Phonon supports at most 25 hotwords.")

        self._phonon = None
        self._whisper = None

        if self.engine not in ("phonon", "whisper"):
            raise ValueError(
                f"Unsupported STT engine: {self.engine}"
            )

        print(f"[STT] Selected engine: {self.engine}")

    def _load_phonon(self):
        if self._phonon is not None:
            return

        try:
            import fermion

            print(
                f"[STT] Loading {self.model_name} "
                "(CPU, first load may take some time)..."
            )

            self._phonon = fermion.load_speech(self.model_name)

            print("[STT] Phonon model loaded.")

        except Exception as error:
            raise RuntimeError(
                f"Could not load Phonon: {error}"
            ) from error

    def _load_whisper(self):
        if self._whisper is not None:
            return

        import os
        import sys

        # Preserve the existing Windows CUDA DLL setup for
        # the optional Whisper comparison engine.
        site_packages = Path(sys.prefix) / "Lib" / "site-packages"
        nvidia_dir = site_packages / "nvidia"

        for folder in ("cublas", "cudnn", "cuda_nvrtc"):
            bin_path = nvidia_dir / folder / "bin"

            if bin_path.exists():
                os.environ["PATH"] = (
                    str(bin_path) + os.pathsep + os.environ["PATH"]
                )

        from faster_whisper import WhisperModel

        stt_config = config.get("stt", {})

        device = stt_config.get("whisper_device", "cuda")
        compute_type = stt_config.get(
            "whisper_compute_type",
            "int8_float16",
        )

        print(f"[STT] Loading Whisper on {device}...")

        try:
            self._whisper = WhisperModel(
                "models/faster-whisper-small",
                device=device,
                compute_type=compute_type,
            )
        except Exception:
            if device != "cuda":
                raise

            print("[STT] Whisper CUDA unavailable. Falling back to CPU.")

            self._whisper = WhisperModel(
                "models/faster-whisper-small",
                device="cpu",
                compute_type="int8",
            )

        print("[STT] Whisper loaded.")

    def transcribe(self, audio_path):
        audio_path = Path(audio_path)

        if not audio_path.is_file():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        if self.engine == "phonon":
            self._load_phonon()

            try:
                text, decode_time, audio_time = self._phonon.transcribe(
                    str(audio_path),
                    hotwords=self.hotwords,
                )

                print(
                    f"[STT] Phonon: {decode_time:.3f}s decode "
                    f"/ {audio_time:.3f}s audio"
                )

                return text.strip()

            except Exception as error:
                raise RuntimeError(
                    f"Phonon transcription failed: {error}"
                ) from error

        self._load_whisper()

        segments, info = self._whisper.transcribe(
            str(audio_path),
            beam_size=5,
            language="en",
            vad_filter=True,
        )

        return " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()


# Keep the existing import interface:
# from services.stt import stt
stt = STT()
