from services.microphone import microphone
from services.stt import stt


audio_file = microphone.record_until_silence()

if audio_file is None:

    print("[RESULT] No speech detected.")

else:

    print("[STT] Transcribing...")

    text = stt.transcribe(audio_file)

    print(f"[RESULT] {text}")

    audio_file.unlink(missing_ok=True)