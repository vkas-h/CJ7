from core.action import Action
from core.results import Result
from .event import Event
from .event_bus import event_bus

def dispatch(action : Action , commands : dict) -> Result:

    command_name = action.type

    event_bus.publish(
        Event(
            type="action_started",
            data={
                "action_id":str(action.id),
                "action_type": command_name,
                "arguments": action.arguments
            }
        )
    )

    command = commands.get(command_name)

    if command is None:
        
        result = Result(
            success=False,
            error=f"unknown command : {command_name}"
        )

        event_bus.publish(
            Event(
                type="action_failed",
                data={
                    "action_id": str(action.id),
                    "action_type": command_name,
                    "error": result.error
                }
            )
        )

        return result

    try:
        output = command.function(**action.arguments)

        if output is None:
            output = (
                f"Command '{command_name}' completed "
                "but returned no output."
            )

        result = Result(
            success=True,
            output=str(output)
        )
    
        event_bus.publish(
            Event(
                type="action_completed",
                data={
                    "action_id": str(action.id),
                    "action_type": command_name,
                    "output": result.output
                }
            )
        )

        return result

    except Exception as e  :
        result = Result(
            success=False,
            error=str(e)
        )

        event_bus.publish(
            Event(
                type="action_failed",
                data={
                    "action_id": str(action.id),
                    "action_type": command_name,
                    "error": result.error
                }
            )
        )

        return result



    