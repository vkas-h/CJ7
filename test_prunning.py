
from core.context import ContextManager
from core.message import Message

# Use a small temporary context window to trigger pruning.
manager = ContextManager(
    context_window=1000,
    response_reserve_ratio=0.25,
    compaction_threshold=0.75
)

transcript = [
    Message(role="user", content="Read these files")
]

calls = [
    {
        "function": {
            "name": "readfile",
            "arguments": {}
        }
    }
]

# Create five completed tool-call batches.
for i in range(5):
    transcript.append(
        Message(
            role="assistant",
            content="",
            metadata={"tool_calls": calls}
        )
    )

    transcript.append(
        Message(
            role="tool",
            content=f"Tool output {i}: " + ("X" * 2000),
            metadata={"tool_name": "readfile"}
        )
    )

# Preserve a copy to verify the original is untouched.
before = [
    (message.role, message.content, message.metadata.copy())
    for message in transcript
]

# Run the actual context preparation pipeline.
projected = manager.prepare_messages(
    transcript=transcript,
    system_prompt="You are CJ7, a desktop assistant.",
    tools=[],
    session_id=None
)

# Count retained and pruned tool results.
tool_messages = [
    message for message in projected
    if message["role"] == "tool"
]

full_results = sum(
    "X" * 100 in message["content"]
    for message in tool_messages
)

pruned_results = sum(
    "omitted from model context" in message["content"]
    for message in tool_messages
)

original_unchanged = before == [
    (message.role, message.content, message.metadata.copy())
    for message in transcript
]

print("Context triggered:", manager.last_stats.needs_compaction)
print("Original unchanged:", original_unchanged)
print("Full results:", full_results)
print("Pruned results:", pruned_results)
print("Total projected tool results:", len(tool_messages))
print("Estimated tokens:", manager.last_stats.total_tokens)
