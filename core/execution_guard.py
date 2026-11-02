
import hashlib
import json
from collections import defaultdict


class ExecutionGuard:
    """
    Detects repeated tool calls that produce unchanged outcomes.

    This is deliberately independent of the model and planner.
    It does not impose a maximum number of agent iterations.
    """

    IDENTICAL_OUTCOME_LIMIT = 3

    def __init__(self):
        self._last_outcome = {}
        self._outcome_streak = defaultdict(int)
        self._blocked = set()

    @staticmethod
    def _fingerprint(value):
        encoded = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _identity(self, tool_name, arguments):
        return (
            tool_name,
            self._fingerprint(arguments or {}),
        )

    def should_block(self, tool_name, arguments):
        """
        Return a diagnostic if this exact tool+arguments combination
        has already produced the same outcome too many times.
        """
        if tool_name == "create_plan":
            return None

        identity = self._identity(tool_name, arguments)

        if identity in self._blocked:
            return (
                f"Repeated-call guard: '{tool_name}' with these "
                "arguments has repeatedly produced the same outcome. "
                "Do not repeat this action. Change your approach, "
                "use different arguments, or explain the limitation."
            )

        return None

    def record_outcome(self, tool_name, arguments, result):
        """
        Record a completed call. Three identical consecutive outcomes
        arm a block for the next identical call.
        """
        if tool_name == "create_plan":
            return

        identity = self._identity(tool_name, arguments)
        outcome = self._fingerprint(result)

        previous = self._last_outcome.get(identity)

        if previous == outcome:
            self._outcome_streak[identity] += 1
        else:
            self._outcome_streak[identity] = 1

        self._last_outcome[identity] = outcome

        if (
            self._outcome_streak[identity]
            >= self.IDENTICAL_OUTCOME_LIMIT
        ):
            self._blocked.add(identity)

    def reset(self):
        self._last_outcome.clear()
        self._outcome_streak.clear()
        self._blocked.clear()
