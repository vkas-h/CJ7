from ollama import chat
from config.settings import config


def stream_with_model(
    messages,
    tools=None,
    reasoning=False,
    effort=None
):

    llm_config = config["llm"]

    if not reasoning:
        think = False
    else:
        supported_efforts = {"low", "medium", "high"}

        if effort in supported_efforts:
            think = effort
        else:
            think = True

    return chat(
        model=llm_config["model"],
        messages=messages,
        tools=tools or [],
        think=think,
        options={
            "num_ctx": llm_config["num_ctx"]
        },
        stream=True
    )