from dataclasses import dataclass , field

@dataclass
class Result:
    success: bool 
    output: str | None = None
    error : str | None = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
        }   