from dataclasses import dataclass , field
from datetime import datetime

@dataclass
class Message:
    role : str
    content : str
    timestamp : datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    