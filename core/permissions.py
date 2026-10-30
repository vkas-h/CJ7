def request_permission(command, arguments, ctx=None):
    """
    Decide whether an AI-requested command may execute.

    safe      -> execute automatically
    confirm   -> require explicit user approval
    dangerous -> never execute through the AI
    """

    permission = command.permission

    if permission == "safe":
        return True

    if permission == "dangerous":
        message = (
            f"[BLOCKED] AI is not allowed to execute "
            f"'{command.name}' automatically."
        )

        if ctx is not None:
            ctx.say(message)
        else:
            print(message)

        return False

    if permission == "confirm":
        if ctx is None:
            print(
                f"[BLOCKED] Cannot confirm '{command.name}': "
                "ToolContext is unavailable."
            )
            return False

        prompt = (
            f"Allow command '{command.name}'?\n"
            f"Arguments: {arguments}"
        )

        return ctx.confirm(prompt, timeout=30)

    print(
        f"[BLOCKED] Unknown permission level "
        f"'{permission}' for '{command.name}'."
    )
    return False