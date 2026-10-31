from core.command import Command
from utils.time_parser import parse_delay
from core.scheduler import register_action




def reminder_message(message):

    print(f"\n🔔 Reminder: {' '.join(message)}\n> ", end="", flush=True)



register_action(
    "Reminder",
    reminder_message
)


def remind(delay, message):
    try:
        delay_seconds = parse_delay(delay)
    except ValueError:
        return "Invalid delay. Use formats like '10s', '5m', '2h', or '1d'."

    from core.scheduler import scheduler

    scheduler.add_job(
        delay_seconds,
        reminder_message,
        "Reminder",
        message
    )

    return f"Reminder set for {delay_seconds} seconds."


COMMANDS = [

    Command(
        name="remind",
        function=remind,
        description="Set a reminder after a specified amount of time.",
        toolset="Productivity",
        parameters={
            "type": "object",
            "properties": {
                "delay": {
                    "type": "string",
                    "description": "Amount of time before the reminder, such as '10s', '5m', '2h', or '1d'."
                },
                "message": {
                    "type": "string",
                    "description": "Message to display when the reminder triggers."
                }
            },
            "required": ["delay", "message"]
        }
    )

]