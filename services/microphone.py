import queue
import tempfile
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

from faster_whisper.vad import get_vad_model


class Microphone:

    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = "float32"

    # Silero VAD
    VAD_THRESHOLD = 0.50
    VAD_NEG_THRESHOLD = 0.35

    # Endpointing
    MIN_SILENCE_DURATION = 1.2
    START_TIMEOUT = 2.5
    MAX_RECORDING_TIME = 15.0

    # Audio padding
    PRE_SPEECH_DURATION = 0.20
    POST_SPEECH_DURATION = 0.20

    # Silero expects 512 samples at 16 kHz
    CHUNK_SIZE = 512

    def __init__(self):

        print("[MIC] Loading Silero VAD...")

        self.vad_model = get_vad_model()

        self.h = np.zeros(
            (1, 1, 128),
            dtype=np.float32,
        )

        self.c = np.zeros(
            (1, 1, 128),
            dtype=np.float32,
        )

        self.context = np.zeros(
            (1, 64),
            dtype=np.float32,
        )

        print("[MIC] Silero VAD loaded.")

    def _reset_vad(self):

        self.h.fill(0)
        self.c.fill(0)
        self.context.fill(0)

    def _vad_probability(self, audio):

        audio = np.asarray(
            audio,
            dtype=np.float32,
        )

        if len(audio) != self.CHUNK_SIZE:
            raise ValueError(
                f"Expected {self.CHUNK_SIZE} samples, "
                f"got {len(audio)}"
            )

        # Silero VAD expects the previous 64 samples
        # as context before the current 512 samples.
        model_input = np.concatenate(
            [
                self.context[0],
                audio,
            ]
        ).reshape(1, -1)

        output, self.h, self.c = self.vad_model.session.run(
            None,
            {
                "input": model_input,
                "h": self.h,
                "c": self.c,
            },
        )

        # Save the end of this chunk as context
        # for the next chunk.
        self.context[0] = audio[-64:]

        return float(np.asarray(output).squeeze())

    def record_until_silence(self):

        print("[MIC] Waiting for speech...")

        self._reset_vad()

        audio_queue = queue.Queue()

        def callback(indata, frames, time_info, status):

            if status:
                print(f"[MIC] Audio status: {status}")

            audio = indata[:, 0].copy()

            audio_queue.put(audio)

        speech_started = False

        speech_start_time = None
        silence_start_time = None

        all_audio = []

        # Keep audio from immediately before speech starts.
        pre_speech_chunks = []

        pre_speech_samples = int(
            self.PRE_SPEECH_DURATION
            * self.SAMPLE_RATE
        )

        pre_speech_chunks_needed = max(
            1,
            pre_speech_samples // self.CHUNK_SIZE,
        )

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=self.DTYPE,
            blocksize=self.CHUNK_SIZE,
            callback=callback,
        ):

            recording_started_at = time.monotonic()
            print("[MIC] Listening for speech (2.5s timeout)...")

            
            while True:

                # --------------------------------
                # INITIAL SPEECH TIMEOUT
                # --------------------------------

                if (
                    not speech_started
                    and (
                        time.monotonic()
                        - recording_started_at
                        >= self.START_TIMEOUT
                    )
                ):

                    print("[MIC] No speech detected.")
                    return None

                # --------------------------------
                # GET AUDIO
                # --------------------------------

                try:

                    audio = audio_queue.get(
                        timeout=0.1
                    )

                except queue.Empty:
                    continue

                now = time.monotonic()
            

                # --------------------------------
                # VAD
                # --------------------------------

                speech_probability = (
                    self._vad_probability(audio)
                )

                # Keep a rolling pre-speech buffer.
                pre_speech_chunks.append(audio)

                if (
                    len(pre_speech_chunks)
                    > pre_speech_chunks_needed
                ):
                    pre_speech_chunks.pop(0)

                # --------------------------------
                # WAITING FOR SPEECH
                # --------------------------------

                if not speech_started:

                    if (
                        speech_probability
                        >= self.VAD_THRESHOLD
                    ):

                        speech_started = True

                        speech_start_time = now
                        last_speech_time = now

                        # Include the small amount of
                        # audio immediately before speech.
                        all_audio.extend(
                            pre_speech_chunks
                        )

                        print(
                            "[MIC] Speech detected "
                            f"(VAD={speech_probability:.2f})"
                        )

                    continue

                # --------------------------------
                # RECORDING
                # --------------------------------

                all_audio.append(audio)

                # --------------------------------
                # STRONG SPEECH
                # --------------------------------

                if speech_probability >= self.VAD_THRESHOLD:

                    # We are definitely hearing speech.
                    # Any previous silence is cancelled.
                    silence_start_time = None

                # --------------------------------
                # HYSTERESIS REGION
                # --------------------------------

                elif speech_probability >= self.VAD_NEG_THRESHOLD:

                    # Probability is weaker than normal speech,
                    # but it is still inside the hysteresis region.
                    #
                    # Do NOT start/end the utterance here.
                    silence_start_time = None

                # --------------------------------
                # ACTUAL SILENCE
                # --------------------------------

                else:

                    # Start the silence timer only when we
                    # actually enter the silence region.
                    if silence_start_time is None:

                        silence_start_time = now

                    silence_duration = (
                        now - silence_start_time
                    )

                    if (
                        silence_duration
                        >= self.MIN_SILENCE_DURATION
                    ):

                        print(
                            "[MIC] Silence detected "
                            f"(VAD={speech_probability:.2f})"
                        )

                        break

                # --------------------------------
                # MAXIMUM RECORDING TIME
                # --------------------------------

                if (
                    now - speech_start_time
                    >= self.MAX_RECORDING_TIME
                ):

                    print(
                        "[MIC] Maximum recording "
                        "time reached."
                    )

                    break

        if not all_audio:

            return None

        # --------------------------------
        # BUILD AUDIO
        # --------------------------------

        audio = np.concatenate(
            all_audio
        )

        # Keep a little audio after the detected
        # speech endpoint.
        post_speech_samples = int(
            self.POST_SPEECH_DURATION
            * self.SAMPLE_RATE
        )

        if len(audio) > post_speech_samples:

            audio = audio[
                :-post_speech_samples
            ]

        # --------------------------------
        # SAVE WAV
        # --------------------------------

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        )

        temp_path = Path(
            temp_file.name
        )

        temp_file.close()

        audio_int16 = (
            np.clip(audio, -1.0, 1.0)
            * 32767
        ).astype(np.int16)

        with wave.open(
            str(temp_path),
            "wb",
        ) as wav:

            wav.setnchannels(
                self.CHANNELS
            )

            wav.setsampwidth(2)

            wav.setframerate(
                self.SAMPLE_RATE
            )

            wav.writeframes(
                audio_int16.tobytes()
            )

        print(
            f"[MIC] Saved: {temp_path}"
        )

        return temp_path


microphone = Microphone()