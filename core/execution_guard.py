
import hashlib
import json
from collections import defaultdict, deque


class ExecutionGuard:
    """
    Detects repeated tool calls and repeating tool-call sequences.

    This is independent of the model and planner. It does not impose
    a maximum number of agent iterations.
    """

    IDENTICAL_OUTCOME_LIMIT = 3
    CYCLE_LENGTHS = (2, 3, 4)
    CYCLE_REPEAT_LIMIT = 3

    def __init__(self):
        self._last_outcome = {}
        self._outcome_streak = defaultdict(int)
        self._blocked = set()

        # Each entry is (tool+arguments identity, outcome fingerprint).
        self._history = deque(
            maxlen=max(self.CYCLE_LENGTHS) * self.CYCLE_REPEAT_LIMIT
        )
        self._cycle_reported = False

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
        """Return a diagnostic for a previously blocked exact call."""
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

    def _detect_repeating_cycle(self):
        if self._cycle_reported:
            return None

        history = list(self._history)

        for length in self.CYCLE_LENGTHS:
            required = length * self.CYCLE_REPEAT_LIMIT

            if len(history) < required:
                continue

            window = history[-required:]
            pattern = window[:length]

            # A single repeated call belongs to the individual-call
            # guard, not the sequence-cycle detector.
            identities = {entry[0] for entry in pattern}
            if len(identities) < 2:
                continue

            repeated = all(
                window[index:index + length] == pattern
                for index in range(0, required, length)
            )

            if repeated:
                self._cycle_reported = True
                return (
                    "Repeating tool-cycle guard: the same sequence "
                    f"of {length} tool calls has produced the same "
                    f"outcomes {self.CYCLE_REPEAT_LIMIT} times. "
                    "Stop repeating this sequence. Change the "
                    "approach or explain the limitation."
                )

        return None

    def record_outcome(self, tool_name, arguments, result):
        """
        Record a completed call.

        Returns a diagnostic if a repeating multi-call cycle is detected.
        Existing callers may safely ignore the return value.
        """
        if tool_name == "create_plan":
            return None

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

        self._history.append((identity, outcome))

        return self._detect_repeating_cycle()

    def reset(self):
        self._last_outcome.clear()
        self._outcome_streak.clear()
        self._blocked.clear()
        self._history.clear()
        self._cycle_reported = False
