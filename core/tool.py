from core.command import Command

def command_to_tool(command: Command) -> dict:
    return {
        "type": "function",
        "function": {
            "name": command.name,
            "description": command.description,
            "parameters": command.parameters,
        },
    }


def commands_to_tools(
    commands: dict[str, Command],
    toolsets: set[str] | None = None,
    ) -> list[dict]:


    # """Return enabled model tools, optionally restricted to selected toolsets."""
    return [
        command_to_tool(command)
        for command in commands.values()
        if command.enabled
        and (toolsets is None or command.toolset in toolsets)
    ]
