from core.command import Command
from core.session_manager import session_manager


def list_sessions():

    sessions = session_manager.list_sessions()

    if not sessions:
        return "No saved sessions found."

    lines = [
        "",
        "Saved Sessions",
        "-" * 45
    ]

    for index, session in enumerate(
        sessions,
        start=1
    ):

        created_at = session["created_at"].strftime(
            "%d %b %Y • %I:%M %p"
        )

        current = ""

        if (
            session_manager.current_session
            and session["id"]
            == session_manager.current_session.id
        ):
            current = " [CURRENT]"

        lines.append(
            f"{index}. {session['title']}{current}"
        )

        lines.append(
            f"   {created_at}"
        )

        lines.append("")

    return "\n".join(lines)


def latest_session():

    session = session_manager.get_latest_session()

    if session is None:
        return "No saved sessions found."

    return (
        "Latest Session\n"
        f"Title: {session.title}\n"
        f"Created: "
        f"{session.created_at.strftime('%d %b %Y • %I:%M %p')}"
    )


def load_session(session_number):

    if session_number is None:
        return "Usage: loadsession <session number>"

    try:
        session_number = int(session_number)

    except ValueError:
        return "Session number must be a number."

    session = session_manager.load_by_index(
        session_number
    )

    if session is None:
        return "Session not found."

    return (
        f"Loaded session: {session.title}"
    )


def rename_session(session_number , new_title):

    # if len(args) < 2:
    #     return (
    #         "Usage: renamesession "
    #         "<session number> <new title>"
    #     )

    try:
        session_number = int(session_number)

    except ValueError:
        return "Session number must be a number."


    session = session_manager.rename_session(
        session_number,
        new_title
    )

    if session is None:
        return "Session not found."

    return (
        f"Session renamed to: {session.title}"
    )


COMMANDS = [

    Command(
        name="sessions",
        function=list_sessions,
        description="List all saved sessions.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),

    Command(
        name="latestsession",
        function=latest_session,
        description="Show information about the most recently created session.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),

    Command(
        name="loadsession",
        function=load_session,
        description="Load a saved session using its session number.",
        parameters={
            "type": "object",
            "properties": {
                "session_number": {
                    "type": "integer",
                    "description": "Number of the saved session to load."
                }
            },
            "required": ["session_number"]
        }
    ),

    Command(
        name="renamesession",
        function=rename_session,
        description="Rename a saved session.",
        parameters={
            "type": "object",
            "properties": {
                "session_number": {
                    "type": "integer",
                    "description": "Number of the saved session to rename."
                },
                "new_title": {
                    "type": "string",
                    "description": "New title for the session."
                }
            },
            "required": ["session_number", "new_title"]
        }
    )

]