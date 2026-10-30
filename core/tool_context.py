class ToolContext:
    def __init__(self, input_manager):
        self.input_manager = input_manager

    def say(self, message):
        print(message)

    def ask(self, prompt, timeout=30):
        return self.input_manager.ask(prompt, timeout=timeout)

    def confirm(self, prompt, timeout=30):
        answer = self.ask(f"{prompt} (yes/no): ", timeout=timeout)

        if answer is None:
            print("[DENIED] Confirmation timed out.")
            return False

        return answer.strip().lower() in {"yes", "y"}

    def progress(self, message):
        print(f"[PROGRESS] {message}")
