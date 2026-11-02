import queue
import threading

from services.microphone import microphone
from services.stt import stt


class InputManager:

    def __init__(self, wakeword):
        self.wakeword = wakeword

        self.keyboard_queue = queue.Queue()

        self.running = False
        self.keyboard_thread = None

        self.voice_mode = False

        self._request_lock = threading.Lock()
        self._pending_request = None

    def _keyboard_listener(self):
        
        """The only thread that reads keyboard input."""

        while self.running:
            try:
                text = input("> ").strip()

                if not text:
                    continue

                with self._request_lock:
                    request = self._pending_request

                    if request is not None:
                        request["answer"] = text
                        request["event"].set()
                        continue

                self.keyboard_queue.put(text)

            except (EOFError, KeyboardInterrupt):
                self.running = False
                break

    def ask(self, prompt, timeout=30):
        """Request an answer through the existing keyboard listener."""

        request = {
            "event": threading.Event(),
            "answer": None,
        }

        with self._request_lock:
            if self._pending_request is not None:
                return None

            self._pending_request = request

        try:
            print(f"\n[INPUT REQUIRED] {prompt}", flush=True)

            if not request["event"].wait(timeout=timeout):
                return None

            return request["answer"]

        finally:
            with self._request_lock:
                if self._pending_request is request:
                    self._pending_request = None


    def start(self):
        """
        Start keyboard and wake-word monitoring.
        """

        if self.running:
            return

        self.running = True
        self.voice_mode = False

        self.keyboard_thread = threading.Thread(
            target=self._keyboard_listener,
            daemon=True,
        )

        self.keyboard_thread.start()

        self.wakeword.start()

    def stop(self):
        """
        Stop input monitoring.
        """

        self.running = False
        self.voice_mode = False

        self.wakeword.stop()

    def resume_normal_mode(self):
        """
        Return to normal keyboard + wake-word mode.
        """

        self.voice_mode = False

        if not self.running:
            return

        self.wakeword.start()

    def get_input(self):
        """
        Wait for input.

        Normal mode:
            ("keyboard", text)
            ("wakeword", "Hey C-J-seven")

        Voice mode:
            ("voice", text)
            ("voice_timeout", "")
        """

        while self.running:

            # -----------------------------------------
            # VOICE MODE
            # -----------------------------------------

            if self.voice_mode:

                audio_file = microphone.record_until_silence()

                # No speech within START_TIMEOUT
                if audio_file is None:

                    print("[VOICE] No speech detected.")
                    print("[VOICE] Returning to normal mode.")

                    self.voice_mode = False
                    self.wakeword.start()

                    return (
                        "voice_timeout",
                        "",
                    )

                print("[STT] Transcribing...")

                try:
                    text = stt.transcribe(audio_file)

                except Exception as error:
                    print(f"[VOICE] Transcription failed: {error}")

                    self.voice_mode = False

                    try:
                        self.wakeword.start()
                    except Exception as wake_error:
                        print(f"[WAKE] Could not resume listener: {wake_error}")

                    return (
                        "voice_error",
                        str(error),
                    )

                finally:
                    audio_file.unlink(missing_ok=True)

                if not text.strip():
                    print("[VOICE] Empty transcription.")
                    continue

                return (
                    "voice",
                    text,
                )

            # -----------------------------------------
            # WAKE WORD
            # -----------------------------------------

            if self.wakeword.is_detected():

                self.wakeword.stop()

                self.voice_mode = True

                return (
                    "wakeword",
                    "Hey C-J-seven",
                )

            # -----------------------------------------
            # KEYBOARD
            # -----------------------------------------

            try:

                text = self.keyboard_queue.get(
                    timeout=0.1
                )

                self.wakeword.stop()

                return (
                    "keyboard",
                    text,
                )

            except queue.Empty:
                continue

        return None, None