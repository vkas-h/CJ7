
from dataclasses import dataclass
from enum import Enum


class ReasoningLevel(Enum):
    NONE = "none"
    XHIGH = "xhigh"
    MAX = "max"


@dataclass
class ReasoningPolicy:
    level: ReasoningLevel
    think: bool | str
    effort: str | None


class ReasoningRouter:

    SIMPLE_MESSAGES = {
        "hi",
        "hello",
        "hey",
        "thanks",
        "thank you",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
    }

    COMPLEX_PATTERNS = (
        "debug this",
        "debug my code",
        "design an architecture",
        "system architecture",
        "complex reasoning",
        "deep analysis",
        "analyze this project",
        "refactor the entire",
    )

    def decide(self, messages):

        user_message = ""

        for message in reversed(messages):
            if message.get("role") == "user":
                user_message = message.get("content", "")
                break

        text = user_message.lower().strip().rstrip("!.?")

        if text in self.SIMPLE_MESSAGES:
            return ReasoningPolicy(
                level=ReasoningLevel.NONE,
                think=False,
                effort=None,
            )

        if any(pattern in text for pattern in self.COMPLEX_PATTERNS):
            return ReasoningPolicy(
                level=ReasoningLevel.MAX,
                think=True,
                effort="max",
            )

        return ReasoningPolicy(
            level=ReasoningLevel.XHIGH,
            think=True,
            effort="xhigh",
        )
