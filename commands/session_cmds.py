from core.command import Command
from core.session_manager import session_manager


def session(action, session_number=None, new_title=None):
    """List, inspect, load, or rename saved sessions."""

    action = action.strip().lower()

    if action == "list":
        sessions = session_manager.list_sessions()

        if not sessions:
            return "No saved sessions found."

        lines = ["Saved Sessions", "-" * 45]

        for index, item in enumerate(sessions, start=1):
            created_at = item["created_at"].strftime(
                "%d %b %Y • %I:%M %p"
            )

            current = ""
            active = session_manager.current_session

            if active and item["id"] == active.id:
                current = " [CURRENT]"

            lines.append(f"{index}. {item['title']}{current}")
            lines.append(f"   {created_at}")
            lines.append("")

        return "\n".join(lines)

    if action == "latest":
        item = session_manager.get_latest_session()

        if item is None:
            return "No saved sessions found."

        return (
            "Latest Session\n"
            f"Title: {item.title}\n"
            f"Created: {item.created_at.strftime('%d %b %Y • %I:%M %p')}"
        )

    if action == "load":
        if session_number is None:
            return "Provide the session number to load."

        try:
            session_number = int(session_number)
        except (TypeError, ValueError):
            return "Session number must be a number."

        item = session_manager.load_by_index(session_number)

        if item is None:
            return "Session not found."

        return f"Loaded session: {item.title}"

    if action == "rename":
        if session_number is None:
            return "Provide the session number to rename."

        if not new_title or not new_title.strip():
            return "Provide a non-empty new title."

        try:
            session_number = int(session_number)
        except (TypeError, ValueError):
            return "Session number must be a number."

        item = session_manager.rename_session(
            session_number,
            new_title.strip()
        )

        if item is None:
            return "Session not found."

        return f"Session renamed to: {item.title}"

    return (
        f"Unknown session action: {action}. "
        "Use list, latest, load, or rename."
    )


COMMANDS = [
    Command(
        name="session",
        function=session,
        description=(
            "Manage saved conversations. Use action='list' to list sessions, "
            "'latest' to inspect the latest session, 'load' with a "
            "session_number to load one, or 'rename' with session_number "
            "and new_title to rename one."
        ),
        toolset="memory",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "latest", "load", "rename"],
                    "description": "Operation to perform."
                },
                "session_number": {
                    "type": "integer",
                    "description": (
                        "Session number, required for load and rename."
                    )
                },
                "new_title": {
                    "type": "string",
                    "description": "New title, required for rename."
                }
            },
            "required": ["action"]
        }
    )
]