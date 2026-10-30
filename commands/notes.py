from core.command import Command
from config.settings import config

notes_file = config["notes_file"]


def notes(action, note=None, query=None):
    """Add, list, or search saved notes."""

    action = action.strip().lower()

    if action == "add":
        if not note or not note.strip():
            return "Write something to save."

        try:
            with open(notes_file, "a", encoding="utf-8") as file:
                file.write(note.strip() + "\n")

            return "Note saved."

        except OSError as e:
            return f"Error saving note: {e}"

    if action in {"list", "search"}:
        try:
            with open(notes_file, "r", encoding="utf-8") as file:
                saved_notes = [
                    line.strip()
                    for line in file
                    if line.strip()
                ]

        except FileNotFoundError:
            saved_notes = []

        except OSError as e:
            return f"Error reading notes: {e}"

        if action == "search":
            if not query or not query.strip():
                return "Provide a search query."

            search_query = query.strip().casefold()
            saved_notes = [
                item for item in saved_notes
                if search_query in item.casefold()
            ]

            if not saved_notes:
                return f"No notes found matching: {query}"

            heading = f"Notes matching '{query}'"

        else:
            if not saved_notes:
                return "No notes yet."

            heading = "Saved Notes"

        lines = [f"------ {heading} ------"]
        lines.extend(
            f"{index}. {item}"
            for index, item in enumerate(saved_notes, start=1)
        )
        return "\n".join(lines)

    return (
        f"Unknown notes action: {action}. "
        "Use add, list, or search."
    )


COMMANDS = [
    Command(
        name="notes",
        function=notes,
        description=(
            "Manage saved notes. Use action='add' to save a note, "
            "action='list' to show all notes, or action='search' "
            "to find notes containing a phrase."
        ),
        toolset="memory",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "list", "search"],
                    "description": "Operation to perform."
                },
                "note": {
                    "type": "string",
                    "description": "Text to save when action is add."
                },
                "query": {
                    "type": "string",
                    "description": "Phrase to find when action is search."
                }
            },
            "required": ["action"]
        }
    )
]