from ollama import chat

MODEL = "beam:cloud"


# def chat_with_model(
#     messages,
#     tools=None,
#     reasoning=False,
#     effort=None ):

#     if not reasoning:
#         think = False
#     else:
#         think = effort or True

#     response = chat(
#         model=MODEL,
#         messages=messages,
#         tools=tools or [],
#         think=think,
#         options={
#             "num_ctx": 8192
#         }
#     )

#     return response


def stream_with_model(
    messages,
    tools=None,
    reasoning=False,
    effort=None ):

    if not reasoning:
        think = False
    else:
        think = effort or True

    stream = chat(
        model=MODEL,
        messages=messages,
        tools=tools or [],
        think=think,
        options={
            "num_ctx": 8192
        },
        stream=True
    )

    return stream