from dataclasses import dataclass , field
from datetime import datetime
from typing import Any



@dataclass
class Event:
    type: str
    data: dict [str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)