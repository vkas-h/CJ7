from core.command import Command
from utils.logger import log_command
import sys
from utils.plugin_loader import load_plugins
from core.scheduler import scheduler
from services import app_manager
# from threading import Thread
# from pathlib import Path
from config.settings import show_banner
from core.action import Action
# from core.dispatcher import dispatch
from core.event_bus import event_bus
from utils.logger import logger
# from core.session import Session
from core.message import Message
from core.session_manager import session_manager
from core.agent import Agent
# from services.tts import speak
from services.wakeword import WakeWord
from core.input_manager import InputManager
from core.tool_context import ToolContext




show_banner()
commands = load_plugins()
scheduler.initialize()
app_manager.initialize()
# SEARCH_PATHS = [Path.home(), Path("D:/")]
session_manager.create()

#---------------exit and help command --------------------

def log_event(event):
    logger.info(
        f"[EVENT] {event.type} | {event.data}"
    )

# event_bus.subscribe("action_started", log_event)
# event_bus.subscribe("action_completed", log_event)
event_bus.subscribe("action_failed", log_event)


def exit_program():
    print("Goodbye master ")
    sys.exit()

def help_command():
    
    lines = ["Available Commands:", ""]

    for cmd in commands.values():
        lines.append(f"{cmd.name} - {cmd.description}")

    return "\n".join(lines)



#-----------------------------------

EXIT = Command(
    name="exit",
    function=exit_program,
    description="Exit CJ7.",
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
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
)

commands[HELP.name] = HELP
commands[EXIT.name] = EXIT

wakeword = WakeWord()
input_manager = InputManager(wakeword)

tool_context = ToolContext(input_manager)
agent = Agent(
    commands,
    tool_context=tool_context
)

input_manager.start()


#-----------------------------------------------

print("Lets fucking go we r building it brick by brick")

while True:

    input_type, user_resp = input_manager.get_input()

    if user_resp is None:
        break

    # -----------------------------------------
    # VOICE MODE TIMED OUT
    # -----------------------------------------

    if input_type == "voice_timeout":
        continue

    words = user_resp.split()

    if not words:
        continue

    print(f"[INPUT] {input_type}: {user_resp}")

    session_manager.current_session.add_message(
        Message(
            role="user",
            content=user_resp
        )
    )

    log_command(user_resp)

    messages = session_manager.current_session.get_messages()

    content = agent.run(messages)

    session_manager.current_session.add_message(
        Message(
            role="assistant",
            content=content
        )
    )

    session_manager.current_session.save()

    # -----------------------------------------
    # KEYBOARD COMMAND FINISHED
    # -----------------------------------------

    if input_type == "keyboard":
        input_manager.resume_normal_mode()