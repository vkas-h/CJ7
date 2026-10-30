from core.command import Command

def command_to_tool(command : Command) -> dict :
    return {
        "type": "function",
        "function": {
            "name": command.name,
            "description": command.description,
            "parameters": command.parameters,
        }
    }


def commands_to_tools(commands : dict[str, Command]) ->list[dict]:
    return[
        command_to_tool(command)
        for command in commands.values()
        if command.enabled
    ]