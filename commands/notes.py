from core.command import Command
from config.settings import config
notes_file=config["notes_file"]


def add_note(note):

    if not note or not note.strip():
        return "Write something to save."

    try:
        with open(notes_file, "a", encoding="utf-8") as file:
            file.write(note.strip() + "\n")

        return "Note saved."

    except OSError as e:
        return f"Error saving note: {e}"


def show_notes():

    try:
        with open(notes_file, "r", encoding="utf-8") as file:

            notes = [
                line.strip()
                for line in file
                if line.strip()
            ]

        if not notes:
            return "No notes yet."

        lines = ["------ Notes ------"]
        lines.extend(
            f"{index}. {note}"
            for index, note in enumerate(notes, start=1)
        )

        return "\n".join(lines)

    except FileNotFoundError:
        return "No notes yet."

    except OSError as e:
        return f"Error reading notes: {e}"


COMMANDS = [

    Command(
        name="note",
        function=add_note,
        description="Save a new note.",
        parameters={
            "type": "object",
            "properties": {
                "note": {
                    "type": "string",
                    "description": "The text that should be saved as a note."
                }
            },
            "required": ["note"]
        }
    ),

    Command(
        name="notes",
        function=show_notes,
        description="Show all saved notes.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    )

]