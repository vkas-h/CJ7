import os
import importlib

from core.command import Command

COMMAND_FOLDER = "commands"


def load_plugins():

    commands = {}

    for file in os.listdir(COMMAND_FOLDER):

        # Ignore folders and non-python files
        if not file.endswith(".py"):
            continue

        module_name = file[:-3]

        # Import the plugin
        try:
            module = importlib.import_module(
                f"{COMMAND_FOLDER}.{module_name}"
            )

        except Exception as e:
            print(f"[ERROR] Failed to import '{module_name}'")
            print(e)
            continue

        # Check if COMMANDS exists
        if not hasattr(module, "COMMANDS"):
            print(f"[WARNING] '{module_name}' has no COMMANDS list.")
            continue

        # COMMANDS must be a list
        if not isinstance(module.COMMANDS, list):
            print(f"[WARNING] '{module_name}.COMMANDS' must be a list.")
            continue

        # Register every command
        for command in module.COMMANDS:

            # Every item must be a Command object
            if not isinstance(command, Command):
                print(f"[WARNING] Invalid Command object in '{module_name}'.")
                continue

            # Prevent duplicate command names
            if command.name in commands:
                print(
                    f"[WARNING] Duplicate command '{command.name}' "
                    f"found in '{module_name}'. Skipping."
                )
                continue

            commands[command.name] = command

            print(f"[OK] Loaded '{command.name}'")

    print(f"\n[INFO] Loaded {len(commands)} commands.\n")

    return commands