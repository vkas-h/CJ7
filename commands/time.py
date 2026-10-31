from core.command import Command
import datetime as dt

def show_time():
    now = dt.datetime.now()
    current_time = now.strftime("%I:%M %p")
    
    return f"Current time is {current_time}."



COMMANDS = [
    
    Command(
    name="time",
    function=show_time,
    description="Get the current system time.",
    toolset="core",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
]
