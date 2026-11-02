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
        think = effort if effort in supported_efforts else True

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


def generate_with_model(
    messages,
    format=None,
    temperature=0.2,
    num_predict=1200
):
    """
    Non-streaming model call for internal tasks such as:
    - session summarization
    - durable memory extraction

    This does not expose internal output to the user.
    """
    llm_config = config["llm"]

    kwargs = {
        "model": llm_config["model"],
        "messages": messages,
        "options": {
            "num_ctx": llm_config["num_ctx"],
            "temperature": temperature,
            "num_predict": num_predict
        },
        "stream": False
    }

    if format is not None:
        kwargs["format"] = format

    return chat(**kwargs)