class Progress:
    def __init__(self):
        self.steps = []
        self.current = 0

    def create_plan(self, steps):
        self.steps = steps
        self.current = 0

        if not steps:
            return

        print("\n[PLAN]")

        for index, step in enumerate(steps, start=1):
            print(f"{index}. {step['description']}")

        print()

    def start_step(self, description=None):
        if self.current >= len(self.steps):
            return

        step = self.steps[self.current]

        if description is None:
            description = step["description"]

        self.current += 1

        total = len(self.steps)

        print(
            f"[{self.current}/{total}] "
            f"{description}..."
        )

    def finish(self):
        self.steps = []
        self.current = 0