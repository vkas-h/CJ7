import sounddevice as sd
import numpy as np

print("Default devices:", sd.default.device)
print("\nAvailable input devices:")

for i, device in enumerate(sd.query_devices()):
    if device["max_input_channels"] > 0:
        print(
            f"{i}: {device['name']} | "
            f"Channels: {device['max_input_channels']} | "
            f"Rate: {device['default_samplerate']}"
        )

device_id = sd.default.device[0]
device_info = sd.query_devices(device_id, "input")

print(f"\nTesting: {device_info['name']}")

for rate in [int(device_info["default_samplerate"]), 16000]:
    print(f"\nRecording at {rate} Hz for 5 seconds...")
    audio = sd.rec(
        int(5 * rate),
        samplerate=rate,
        channels=1,
        dtype="float32",
        device=device_id,
    )
    sd.wait()

    rms = float(np.sqrt(np.mean(audio ** 2)))
    peak = float(np.max(np.abs(audio)))

    print(f"RMS: {rms:.6f}")
    print(f"Peak: {peak:.6f}")