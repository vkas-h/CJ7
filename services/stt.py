import os
import sys
from pathlib import Path

site_packages = Path(sys.prefix) / "Lib" / "site-packages"
nvidia_dir = site_packages / "nvidia"

cuda_bin_paths = [
    nvidia_dir / "cublas" / "bin",
    nvidia_dir / "cudnn" / "bin",
    nvidia_dir / "cuda_nvrtc" / "bin",
]

# Make CUDA DLLs available to native Windows/CTranslate2 loading.
for path in cuda_bin_paths:
    if path.exists():
        os.environ["PATH"] = str(path) + os.pathsep + os.environ["PATH"]

from faster_whisper import WhisperModel


class STT:
    def __init__(
        self,
        model_path="models/faster-whisper-small",
        device="cuda",
        compute_type="int8_float16",
    ):
        print("[STT] Loading speech recognition model...")

        self.model = WhisperModel(
            model_path,
            device=device,
            compute_type=compute_type,
        )

        print("[STT] Speech recognition model loaded.")

    def transcribe(self, audio_path):

        segments, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            language="en",
            vad_filter=True,
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        )

        return text.strip()


stt = STT()