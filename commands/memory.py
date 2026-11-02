from core.command import Command
from core.memory import read_life_memory


def memory(action="show"):
    action = (action or "show").strip().lower()

    if action not in {"show", "user", "projects"}:
        return "Use action='show', 'user', or 'projects'."

    try:
        saved = read_life_memory()

        if action == "user":
            content = saved["user"]
            heading = "User Memory"

        elif action == "projects":
            content = saved["general"]
            heading = "Project Memory"

        else:
            sections = []

            if saved["user"].strip():
                sections.append(
                    "USER MEMORY\n" + saved["user"]
                )

            if saved["general"].strip():
                sections.append(
                    "PROJECT MEMORY\n" + saved["general"]
                )

            content = "\n\n".join(sections)
            heading = "Persistent Memory"

        if not content.strip():
            return "No persistent memory has been saved yet."

        return f"------ {heading} ------\n\n{content}"

    except Exception as error:
        return f"Could not read persistent memory: {error}"


COMMANDS = [
    Command(
        name="memory",
        function=memory,
        description=(
            "View persistent memory. Use action='show' for all memory, "
            "'user' for user facts, or 'projects' for project memory."
        ),
        toolset="memory",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["show", "user", "projects"]
                }
            },
            "required": [],
            "additionalProperties": False
        }
    )
]