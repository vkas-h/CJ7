from pathlib import Path

from core.command import Command
from core.store import store
from config.settings import config


LEGACY_NOTES_FILE = Path(config["notes_file"])


def migrate_legacy_notes():
    """
    Import notes.txt into SQLite once.

    The source_ref marker makes migration idempotent. The original
    text file is deliberately retained as a backup.
    """
    if not LEGACY_NOTES_FILE.exists():
        return 0

    existing = store.list_notes(limit=100000)

    migrated_lines = {
        note["text"]
        for note in existing
        if note.get("source_ref") == "legacy_notes.txt"
    }

    imported = 0

    with LEGACY_NOTES_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            note_text = line.strip()

            if not note_text or note_text in migrated_lines:
                continue

            store.add_note(
                text=note_text,
                source_type="legacy",
                source_ref="legacy_notes.txt"
            )

            migrated_lines.add(note_text)
            imported += 1

    return imported


def notes(action, note=None, query=None):
    """Add, list, or search SQLite-backed notes."""

    action = action.strip().lower()

    try:
        migrated = migrate_legacy_notes()

        if action == "add":
            if not note or not note.strip():
                return "Write something to save."

            store.add_note(
                text=note.strip(),
                source_type="user"
            )

            return "Note saved to SQLite."

        if action == "list":
            saved_notes = store.list_notes(limit=100)

            if not saved_notes:
                return "No notes yet."

            lines = ["------ Saved Notes ------"]

            for index, item in enumerate(saved_notes, start=1):
                lines.append(f"{index}. {item['text']}")

            if migrated:
                lines.append(
                    f"\nImported {migrated} legacy note(s) from notes.txt."
                )

            return "\n".join(lines)

        if action == "search":
            if not query or not query.strip():
                return "Provide a search query."

            results = store.search(query.strip(), limit=20)

            # Only show notes, not historical conversation messages.
            results = [
                item for item in results
                if item["source"] == "note"
            ]

            if not results:
                return f"No notes found matching: {query}"

            lines = [f"------ Notes matching '{query}' ------"]

            for index, item in enumerate(results, start=1):
                lines.append(f"{index}. {item['text']}")

            return "\n".join(lines)

        return (
            f"Unknown notes action: {action}. "
            "Use add, list, or search."
        )

    except Exception as error:
        return f"Notes error: {error}"


COMMANDS = [
    Command(
        name="notes",
        function=notes,
        description=(
            "Manage saved notes. Use action='add' to save a note, "
            "action='list' to show saved notes, or action='search' "
            "to search notes."
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
                    "description": "Search query when action is search."
                }
            },
            "required": ["action"],
            "additionalProperties": False
        }
    )
]