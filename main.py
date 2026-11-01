
from core.command import Command
from utils.logger import log_command
import sys

from utils.plugin_loader import load_plugins
from core.scheduler import scheduler
from services import app_manager
from config.settings import show_banner
from core.action import Action
from core.event_bus import event_bus
from utils.logger import logger
from core.message import Message
from core.session_manager import session_manager
from core.agent import Agent
from services.wakeword import WakeWord
from core.input_manager import InputManager
from core.tool_context import ToolContext


show_banner()

commands = load_plugins()

scheduler.initialize()
app_manager.initialize()

# Always start a new session on application launch.
session_manager.create()


# --------------------------------------------------
# EVENTS
# --------------------------------------------------

def log_event(event):
    logger.info(
        f"[EVENT] {event.type} | {event.data}"
    )


event_bus.subscribe("action_failed", log_event)


# --------------------------------------------------
# CORE COMMANDS
# --------------------------------------------------

def exit_program():
    print("Goodbye master")
    sys.exit()


def help_command():

    lines = ["Available Commands:", ""]

    for cmd in commands.values():
        lines.append(f"{cmd.name} - {cmd.description}")

    return "\n".join(lines)


EXIT = Command(
    name="exit",
    function=exit_program,
    description="Exit CJ7.",
    toolset="core",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
)

HELP = Command(
    name="help",
    function=help_command,
    description="Shows available commands",
    toolset="core",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
)

commands[HELP.name] = HELP
commands[EXIT.name] = EXIT


# --------------------------------------------------
# INITIALIZE ASSISTANT
# --------------------------------------------------

wakeword = WakeWord()
input_manager = InputManager(wakeword)

tool_context = ToolContext(input_manager)

agent = Agent(
    commands,
    tool_context=tool_context
)

input_manager.start()


# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------

print("Lets fucking go we r building it brick by brick")


while True:

    input_type, user_resp = input_manager.get_input()

    if user_resp is None:
        break

    if input_type == "voice_timeout":
        continue

    words = user_resp.split()

    if not words:
        continue

    print(f"[INPUT] {input_type}: {user_resp}")

    session = session_manager.current_session

    # Save user message immediately.
    session.add_message(
        Message(
            role="user",
            content=user_resp,
            metadata={
                "provenance": {
                    "source_type": input_type,
                    "source_ref": "user_input"
                }
            }
        )
    )

    session.save()

    log_command(user_resp)

    # Run the agent using the current session transcript.
    messages = session.get_messages()

    content = agent.run(
        messages,
        on_update=session.save
        )

    # Save final assistant response.
    session.add_message(
        Message(
            role="assistant",
            content=content
        )
    )

    session.save()

    if input_type == "keyboard":
        input_manager.resume_normal_mode()