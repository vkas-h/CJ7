import subprocess

import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities

from core.command import Command


def volume(action, value=None):
    """Get or change system volume."""
    action = action.strip().lower()
    try:
        endpoint = AudioUtilities.GetSpeakers().EndpointVolume
        if action == "get":
            current = round(endpoint.GetMasterVolumeLevelScalar() * 100)
            muted = bool(endpoint.GetMute())
            return f"Volume is {current}%. " + ("Muted." if muted else "Not muted.")
        if action == "set":
            if value is None:
                return "The 'set' action requires value (0-100)."
            try:
                value = int(value)
            except (ValueError, TypeError):
                return "Volume must be a number."
            if not 0 <= value <= 100:
                return "Volume must be between 0 and 100."
            endpoint.SetMasterVolumeLevelScalar(value / 100, None)
            return f"Volume set to {value}%."
        if action in {"up", "down"}:
            current = endpoint.GetMasterVolumeLevelScalar()
            delta = 0.10 if action == "up" else -0.10
            new = max(0.0, min(1.0, current + delta))
            endpoint.SetMasterVolumeLevelScalar(new, None)
            return f"Volume set to {round(new * 100)}%."
        if action == "mute":
            muted = not bool(endpoint.GetMute())
            endpoint.SetMute(muted, None)
            return "Muted." if muted else "Unmuted."
        return "Unknown volume action. Use get, set, up, down, or mute."
    except Exception as e:
        return f"Failed to control volume: {e}"


def _get_brightness():
    values = sbc.get_brightness()
    if isinstance(values, list):
        if not values:
            raise RuntimeError("No brightness values were returned.")
        values = values[0]
    if values is None:
        raise RuntimeError("Could not determine the current brightness.")
    return int(values)


def brightness(action, value=None):
    """Get or change screen brightness."""
    action = action.strip().lower()
    try:
        if action == "get":
            return f"Brightness is {_get_brightness()}%."
        if action == "set":
            if value is None:
                return "The 'set' action requires value (0-100)."
            try:
                value = int(value)
            except (ValueError, TypeError):
                return "Brightness must be a number."
            if not 0 <= value <= 100:
                return "Brightness must be between 0 and 100."
            sbc.set_brightness(value)
            return f"Brightness set to {value}%."
        if action in {"up", "down"}:
            current = _get_brightness()
            delta = 10 if action == "up" else -10
            new = max(0, min(100, current + delta))
            sbc.set_brightness(new)
            return f"Brightness set to {new}%."
        return "Unknown brightness action. Use get, set, up, or down."
    except Exception as e:
        return f"Failed to control brightness: {e}"


def power(action):
    """Perform a power action; confirmation is required for this whole tool."""
    action = action.strip().lower()
    commands = {
        "lock": (["rundll32.exe", "user32.dll,LockWorkStation"], "Computer lock command executed."),
        "sleep": (["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"], "Sleep command executed."),
        "restart": (["shutdown", "/r", "/t", "0"], "Restart command executed."),
        "shutdown": (["shutdown", "/s", "/t", "0"], "Shutdown command executed."),
    }
    if action not in commands:
        return "Unknown power action. Use lock, sleep, restart, or shutdown."
    command, message = commands[action]
    try:
        subprocess.run(command, check=True)
        return message
    except Exception as e:
        return f"Failed to perform power action '{action}': {e}"


def _schema(actions, description):
    return {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": actions, "description": description},
            "value": {
                "type": ["integer", "null"],
                "minimum": 0,
                "maximum": 100,
                "description": "Required for set; ignored for other actions.",
            },
        },
        "required": ["action"],
        "additionalProperties": False,
    }


COMMANDS = [
    Command(
        name="volume",
        function=volume,
        description="Get or change system volume. Actions: get, set, up, down, mute.",
        parameters=_schema(["get", "set", "up", "down", "mute"], "Volume action."),
        toolset="system",
    ),
    Command(
        name="brightness",
        function=brightness,
        description="Get or change screen brightness. Actions: get, set, up, down.",
        parameters=_schema(["get", "set", "up", "down"], "Brightness action."),
        toolset="system",
    ),
    Command(
        name="power",
        function=power,
        description="Lock, sleep, restart, or shut down the computer.",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["lock", "sleep", "restart", "shutdown"]}
            },
            "required": ["action"],
            "additionalProperties": False,
        },
        # Conservative: all power actions require approval, including lock.
        permission="confirm",
        toolset="system",
    ),
]
