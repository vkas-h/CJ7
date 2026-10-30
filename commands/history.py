from core.command import Command
HISTORY_FILE = "data/history.txt"


def show_history():

    try:

        with open(HISTORY_FILE, "r") as file:

            history = file.read().strip()

        if not history :
            return "Command history is empty."

        return f"Command History: \n{history}"

        
    except FileNotFoundError:

        return "No history available."



COMMANDS = [

    Command(
        name="history",
        function=show_history,
        description="Show the command history.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    )

]