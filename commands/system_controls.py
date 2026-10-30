# import ctypes
import subprocess

import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities

from core.command import Command

# ============================================================
# VOLUME
# ============================================================

def get_volume_device():
    return AudioUtilities.GetSpeakers()


def set_volume(value):
    if value is None:
        return "Usage: volume <0-100>"

    try:
        value = int(value)
    except (ValueError, TypeError):
        return "Volume must be a number."

    if not 0 <= value <= 100:
        return "Volume must be between 0 and 100."

    try:
        device = get_volume_device()
        device.EndpointVolume.SetMasterVolumeLevelScalar(
            value / 100,
            None
        )
        return f"Volume set to {value}%."

    except Exception as e:
        return f"Failed to change volume: {e}"


def volume_up():
    try:
        device = get_volume_device()
        current = device.EndpointVolume.GetMasterVolumeLevelScalar()
        new_value = min(1.0, current + 0.10)

        device.EndpointVolume.SetMasterVolumeLevelScalar(
            new_value,
            None
        )

        return f"Volume set to {round(new_value * 100)}%."

    except Exception as e:
        return f"Failed to increase volume: {e}"


def volume_down():
    try:
        device = get_volume_device()
        current = device.EndpointVolume.GetMasterVolumeLevelScalar()
        new_value = max(0.0, current - 0.10)

        device.EndpointVolume.SetMasterVolumeLevelScalar(
            new_value,
            None
        )

        return f"Volume set to {round(new_value * 100)}%."

    except Exception as e:
        return f"Failed to decrease volume: {e}"


def mute():
    try:
        device = get_volume_device()
        endpoint = device.EndpointVolume

        current = endpoint.GetMute()
        new_mute_state = not bool(current)

        endpoint.SetMute(new_mute_state, None)

        return "Muted." if new_mute_state else "Unmuted."

    except Exception as e:
        return f"Failed to toggle mute: {e}"


# ============================================================
# BRIGHTNESS
# ============================================================

def set_brightness(value):
    if value is None:
        return "Usage: brightness <0-100>"

    try:
        value = int(value)
    except (ValueError, TypeError):
        return "Brightness must be a number."

    if not 0 <= value <= 100:
        return "Brightness must be between 0 and 100."

    try:
        sbc.set_brightness(value)
        return f"Brightness set to {value}%."

    except Exception as e:
        return f"Failed to change brightness: {e}"


def get_brightness():
    values = sbc.get_brightness()

    if isinstance(values, list):
        if not values:
            raise RuntimeError("No brightness values were returned.")

        values = values[0]

    if values is None:
        raise RuntimeError("Could not determine the current brightness.")

    return int(values)


def brightness_up():
    try:
        current = get_brightness()
        new_value = min(100, current + 10)

        sbc.set_brightness(new_value)

        return f"Brightness set to {new_value}%."

    except Exception as e:
        return f"Failed to increase brightness: {e}"


def brightness_down():
    try:
        current = get_brightness()
        new_value = max(0, current - 10)

        sbc.set_brightness(new_value)

        return f"Brightness set to {new_value}%."

    except Exception as e:
        return f"Failed to decrease brightness: {e}"


# ============================================================
# POWER
# ============================================================

def lock_pc():
    try:
        subprocess.run(
            [
                "rundll32.exe",
                "user32.dll,LockWorkStation"
            ],
            check=True
        )

        return "Computer lock command executed."

    except Exception as e:
        return f"Failed to lock PC: {e}"


def sleep_pc():
    try:
        subprocess.run(
            [
                "rundll32.exe",
                "powrprof.dll,SetSuspendState",
                "0",
                "1",
                "0"
            ],
            check=True
        )

        return "Sleep command executed."

    except Exception as e:
        return f"Failed to put PC to sleep: {e}"


def restart_pc():
    try:
        subprocess.run(
            [
                "shutdown",
                "/r",
                "/t",
                "0"
            ],
            check=True
        )

        return "Restart command executed."

    except Exception as e:
        return f"Failed to restart PC: {e}"


def shutdown_pc():
    try:
        subprocess.run(
            [
                "shutdown",
                "/s",
                "/t",
                "0"
            ],
            check=True
        )

        return "Shutdown command executed."

    except Exception as e:
        return f"Failed to shut down PC: {e}"

    
# ============================================================
# COMMAND REGISTRATION
# ============================================================

COMMANDS = [

    Command(
        name="volume",
        function=set_volume,
        description="Set system volume from 0 to 100.",
        parameters={
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "description": "Volume percentage from 0 to 100."
                }
            },
            "required": ["value"]
        }
    ),

    Command(
        name="volumeup",
        function=volume_up,
        description="Increase system volume by 10%.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),

    Command(
        name="volumedown",
        function=volume_down,
        description="Decrease system volume by 10%.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),

    Command(
        name="mute",
        function=mute,
        description="Toggle system mute on or off.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),

    Command(
        name="brightness",
        function=set_brightness,
        description="Set screen brightness from 0 to 100.",
        parameters={
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "description": "Screen brightness percentage from 0 to 100."
                }
            },
            "required": ["value"]
        }
    ),

    Command(
        name="brightnessup",
        function=brightness_up,
        description="Increase screen brightness by 10%.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),

    Command(
        name="brightnessdown",
        function=brightness_down,
        description="Decrease screen brightness by 10%.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),

    Command(
        name="lock",
        function=lock_pc,
        description="Lock the computer.",
        permission="safe",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),

    Command(
        name="sleep",
        function=sleep_pc,
        description="Put the computer to sleep.",
        permission="confirm",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),

    Command(
        name="restart",
        function=restart_pc,
        description="Restart the computer.",
        permission="confirm",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),

    Command(
        name="shutdown",
        function=shutdown_pc,
        description="Shut down the computer.",
        permission="confirm",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    )

]