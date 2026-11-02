
import unittest

from core.execution_guard import ExecutionGuard


class ExecutionGuardTests(unittest.TestCase):
    def setUp(self):
        self.guard = ExecutionGuard()

    
    def test_repeating_two_call_cycle_is_detected(self):
        calls = [
            ("readfile", {"path": "a.txt"}, {"success": False, "error": "A"}),
            ("search", {"query": "something"}, {"success": False, "error": "B"}),
        ]

        diagnostic = None
        for _ in range(3):
            for name, args, result in calls:
                diagnostic = self.guard.record_outcome(
                    name, args, result
                )

        self.assertIsNotNone(diagnostic)
        self.assertIn("Repeating tool-cycle guard", diagnostic)

    def test_different_outcome_breaks_cycle(self):
        calls = [
            ("readfile", {"path": "a.txt"}, {"success": False, "error": "A"}),
            ("search", {"query": "something"}, {"success": False, "error": "B"}),
        ]

        for _ in range(2):
            for name, args, result in calls:
                self.guard.record_outcome(name, args, result)

        # Change one outcome before the third repetition.
        self.guard.record_outcome(
            "readfile",
            {"path": "a.txt"},
            {"success": True, "output": "Changed"},
        )
        self.guard.record_outcome(
            "search",
            {"query": "something"},
            {"success": False, "error": "B"},
        )

        self.assertFalse(self.guard._cycle_reported)

    def test_three_call_cycle_is_detected(self):
        calls = [
            ("readfile", {"path": "a.txt"}, {"success": True, "output": "A"}),
            ("search", {"query": "x"}, {"success": True, "output": "B"}),
            ("open", {"path": "page"}, {"success": False, "error": "C"}),
        ]

        diagnostic = None
        for _ in range(3):
            for name, args, result in calls:
                diagnostic = self.guard.record_outcome(
                    name, args, result
                )

        self.assertIsNotNone(diagnostic)
        self.assertIn("Repeating tool-cycle guard", diagnostic)

    def test_reset_clears_cycle_history(self):
        calls = [
            ("readfile", {"path": "a.txt"}, {"success": False, "error": "A"}),
            ("search", {"query": "x"}, {"success": False, "error": "B"}),
        ]

        for _ in range(3):
            for name, args, result in calls:
                self.guard.record_outcome(name, args, result)

        self.guard.reset()

        self.assertFalse(self.guard._cycle_reported)
        self.assertEqual(len(self.guard._history), 0)


    def test_different_outcomes_do_not_trigger_block(self):
        args = {"path": "notes.txt"}

        self.guard.record_outcome(
            "readfile", args, {"success": True, "output": "A"}
        )
        self.guard.record_outcome(
            "readfile", args, {"success": True, "output": "B"}
        )

        self.assertIsNone(
            self.guard.should_block("readfile", args)
        )

    def test_three_identical_outcomes_block_next_call(self):
        args = {"path": "notes.txt"}
        result = {
            "success": False,
            "output": None,
            "error": "File not found",
        }

        for _ in range(3):
            self.guard.record_outcome("readfile", args, result)

        self.assertIsNotNone(
            self.guard.should_block("readfile", args)
        )

    def test_different_arguments_have_separate_streaks(self):
        result = {"success": False, "error": "Not found"}

        for _ in range(3):
            self.guard.record_outcome(
                "readfile", {"path": "a.txt"}, result
            )

        self.assertIsNone(
            self.guard.should_block(
                "readfile", {"path": "b.txt"}
            )
        )

    def test_plan_tool_is_not_guarded(self):
        for _ in range(5):
            self.guard.record_outcome(
                "create_plan",
                {"steps": []},
                {"success": True},
            )

        self.assertIsNone(
            self.guard.should_block(
                "create_plan", {"steps": []}
            )
        )

    def test_reset_clears_guard_state(self):
        args = {"path": "notes.txt"}
        result = {"success": False, "error": "Not found"}

        for _ in range(3):
            self.guard.record_outcome("readfile", args, result)

        self.guard.reset()

        self.assertIsNone(
            self.guard.should_block("readfile", args)
        )


if __name__ == "__main__":
    unittest.main()
