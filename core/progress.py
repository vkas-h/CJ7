
class Progress:
    def __init__(self):
        self.steps = []
        self.current = None

    def create_plan(self, steps):
        if not isinstance(steps, list):
            raise ValueError("Plan steps must be a list.")

        if not 2 <= len(steps) <= 5:
            raise ValueError("A plan must contain between 2 and 5 steps.")

        validated = []

        for step in steps:
            if not isinstance(step, dict):
                raise ValueError("Each plan step must be an object.")

            step_type = step.get("type")
            description = step.get("description")

            if step_type not in {"tool", "analysis", "response"}:
                raise ValueError(f"Invalid plan step type: {step_type}")

            if not isinstance(description, str) or not description.strip():
                raise ValueError("Every plan step needs a description.")

            validated.append({
                "type": step_type,
                "description": description.strip(),
                "status": "pending",
            })

        self.steps = validated
        self.current = None

        print("\n[PLAN]")

        for index, step in enumerate(self.steps, start=1):
            print(f"{index}. {step['description']}")

        print()

    def start_tool_step(self, tool_name):
        if not self.steps:
            return

        for index, step in enumerate(self.steps):
            if step["type"] == "tool" and step["status"] == "pending":
                step["status"] = "in_progress"
                self.current = index

                print(
                    f"[{index + 1}/{len(self.steps)}] "
                    f"{step['description']}..."
                )
                return

        print(f"[PROGRESS] Running tool: {tool_name}")

    def complete_tool_step(self, success=True):
        if self.current is None:
            return

        step = self.steps[self.current]
        step["status"] = "completed" if success else "failed"
        self.current = None

    def finish(self):
        self.steps = []
        self.current = None
