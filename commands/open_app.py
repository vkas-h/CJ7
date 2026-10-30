from core.command import Command
from services.app_manager import launch_app


def open_app(app_name):
    return launch_app(app_name)


COMMANDS = [
    Command(
        name="open",
        function=open_app,
        description="Open an installed application.",
        parameters={
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name of the application to open."
                }
            },
            "required": ["app_name"]
        }
    )
]