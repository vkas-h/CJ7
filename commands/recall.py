from core.command import Command
from core.store import store


def recall(query, limit=5):
    if not query or not query.strip():
        return "Provide something to search for."

    try:
        limit = max(1, min(int(limit), 10))

        results = store.search_context(
            query=query,
            limit=limit
        )

        if not results:
            return "No relevant historical records found."

        output = ["Historical Recall", ""]

        for index, item in enumerate(results, start=1):
            output.append(
                f"{index}. [{item['source']} | ref: {item['ref']}]"
            )
            output.append(item["text"])
            output.append("")

        return "\n".join(output)

    except Exception as error:
        return f"Recall failed: {error}"


COMMANDS = [
    Command(
        name="recall",
        function=recall,
        description=(
            "Search historical conversations and saved notes. "
            "Use a few distinctive keywords."
        ),
        toolset="memory",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords to search for."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results, from 1 to 10."
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    )
]