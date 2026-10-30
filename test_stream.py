from services.llm import stream_with_model


messages = [
    {
        "role": "user",
        "content": "Explain what a DFA is in a simple way."
    }
]


print("\n[THINKING]\n")

stream = stream_with_model(
    messages=messages,
    reasoning=True,
    effort="low"
)

answer_started = False

for chunk in stream:

    message = chunk.message

    # -------------------------
    # THINKING
    # -------------------------

    thinking = getattr(message, "thinking", None)

    if thinking:
        print(thinking, end="", flush=True)

    # -------------------------
    # FINAL ANSWER
    # -------------------------

    content = getattr(message, "content", None)

    if content:

        if not answer_started:
            print("\n\n[ANSWER]\n")
            answer_started = True

        print(content, end="", flush=True)


print("\n")