from dataclasses import dataclass
from enum import Enum


class ReasoningLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ReasoningPolicy:
    level: ReasoningLevel # ReasoningLevel is CJ7's internal classification and have nothing to do with ollama
    think: bool
    effort: str | None
    soft_budget: int


class ReasoningRouter:

    def decide(self, messages):

        user_message = ""

        for message in reversed(messages):
            if message.get("role") == "user":
                user_message = message.get("content", "")
                break

        text = user_message.lower().strip()

        # -------------------------------------------------
        # NONE
        # -------------------------------------------------

        simple_patterns = [
            "hello",
            "hi",
            "hey",
            "thanks",
            "thank you",
            "good morning",
            "good evening",
            "good night",
            "what time",
            "open ",
            "launch ",
            "start ",
            "close ",
            "mute",
            "volume",
            "brightness",
        ]

        if any(pattern in text for pattern in simple_patterns):
            return ReasoningPolicy(
                level=ReasoningLevel.NONE,
                think=False,
                effort=None,
                soft_budget=0,
            )

        # -------------------------------------------------
        # MEDIUM
        # -------------------------------------------------

        medium_patterns = [
            "explain",
            "compare",
            "why",
            "how does",
            "how do",
            "difference between",
            "summarize",
            "analyze",
        ]

        if any(pattern in text for pattern in medium_patterns):
            return ReasoningPolicy(
                level=ReasoningLevel.MEDIUM,
                think=True,
                effort="medium",
                soft_budget=1500,
            )

        # -------------------------------------------------
        # HIGH
        # -------------------------------------------------

        complex_patterns = [
            "debug",
            "design",
            "architect",
            "implement",
            "refactor",
            "optimize",
            "plan",
            "build",
            "analyze this project",
        ]

        if any(pattern in text for pattern in complex_patterns):
            return ReasoningPolicy(
                level=ReasoningLevel.HIGH,
                think=True,
                effort="high",
                soft_budget=4000,
            )

        # -------------------------------------------------
        # LOW DEFAULT
        # -------------------------------------------------

        return ReasoningPolicy(
            level=ReasoningLevel.LOW,
            think=True,
            effort="low",
            soft_budget=700,
        )