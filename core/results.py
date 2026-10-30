from dataclasses import dataclass , field

@dataclass
class Result:
    success: bool 
    output: str | None = None
    error : str | None = None