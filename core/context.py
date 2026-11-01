
import json
from config.settings import config
from dataclasses import dataclass

LLM_CONFIG = config ["llm"]


@dataclass(frozen=True)
class ContextStats:
    estimated_tokens: int
    context_window: int
    usage_ratio: float
    compaction_threshold: int
    response_reserve: int
    available_tokens: int
    needs_compaction: bool


class ContextManager:

    def __init__(
        self,
        context_window=None,
        response_reserve_ratio=0.25,
        compaction_threshold=0.75
    ):

        if context_window is None:
            context_window = LLM_CONFIG["num_ctx"]

        if context_window <= 0:
            raise ValueError("Context window must be positive.")

        if not 0 < response_reserve_ratio < 1:
            raise ValueError(
                "Response reserve ratio must be between 0 and 1."
            )

        if not 0 < compaction_threshold < 1:
            raise ValueError(
                "Compaction threshold must be between 0 and 1."
            )

        self.context_window = context_window
        self.response_reserve_ratio = response_reserve_ratio
        self.compaction_threshold = compaction_threshold

        self.response_reserve = int(
            context_window * response_reserve_ratio
        )

        self.compaction_limit = int(
            context_window * compaction_threshold
        )

    # --------------------------------------------------
    # TOKEN ESTIMATION
    # --------------------------------------------------

    @staticmethod
    def estimate_text_tokens(text):
        """
        Rough estimate: approximately 4 characters per token.
        This is not an exact tokenizer.
        """

        if not text:
            return 0

        return max(1, (len(text) + 3) // 4)

    def estimate_message_tokens(self, message):

        if isinstance(message, dict):
            role = message.get("role", "")
            content = message.get("content", "")
            tool_calls = message.get("tool_calls")

        else:
            role = getattr(message, "role", "")
            content = getattr(message, "content", "")

            metadata = getattr(message, "metadata", {}) or {}
            tool_calls = metadata.get("tool_calls")

        tokens = self.estimate_text_tokens(str(content))

        # Account for role and message formatting overhead.
        tokens += 8

        if tool_calls:
            serialized = json.dumps(
                tool_calls,
                ensure_ascii=False,
                default=str
            )

            tokens += self.estimate_text_tokens(serialized)

        if role == "tool":
            tokens += 4

        return tokens

    def estimate_messages_tokens(self, messages):

        return sum(
            self.estimate_message_tokens(message)
            for message in messages
        )

    # --------------------------------------------------
    # CONTEXT STATUS
    # --------------------------------------------------

    def get_stats(self, messages, additional_tokens=0):

        estimated_tokens = (
            self.estimate_messages_tokens(messages)
            + max(0, additional_tokens)
        )

        usage_ratio = (
            estimated_tokens / self.context_window
        )

        available_tokens = max(
            0,
            self.context_window
            - estimated_tokens
            - self.response_reserve
        )

        return ContextStats(
            estimated_tokens=estimated_tokens,
            context_window=self.context_window,
            usage_ratio=usage_ratio,
            compaction_threshold=self.compaction_limit,
            response_reserve=self.response_reserve,
            available_tokens=available_tokens,
            needs_compaction=(
                estimated_tokens >= self.compaction_limit
            )
        )

    def needs_compaction(self, messages, additional_tokens=0):

        stats = self.get_stats(
            messages,
            additional_tokens
        )

        return stats.needs_compaction

    # --------------------------------------------------
    # REPORTING
    # --------------------------------------------------

    def format_stats(self, messages):

        stats = self.get_stats(messages)

        percentage = stats.usage_ratio * 100

        return (
            f"Context usage: {percentage:.1f}%\n"
            f"Estimated tokens: {stats.estimated_tokens:,}\n"
            f"Context window: {stats.context_window:,}\n"
            f"Compaction threshold: "
            f"{stats.compaction_threshold:,}\n"
            f"Response reserve: {stats.response_reserve:,}\n"
            f"Available tokens: {stats.available_tokens:,}\n"
            f"Compaction needed: {stats.needs_compaction}"
        )


context_manager = ContextManager()
