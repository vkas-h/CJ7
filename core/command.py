from typing import Callable
from dataclasses import dataclass, field


@dataclass
class Command:
    name: str
    function: Callable
    description: str = " "
    aliases: list[str] = field(default_factory=list)
    enabled: bool = True
    parameters: dict = field(default_factory=dict)

    # Permission level for AI execution.
    # safe       = execute automatically
    # confirm    = ask the user first
    # dangerous  = never allow AI to execute directly
    permission: str = "safe"