from dataclasses import dataclass , field
import uuid


@dataclass
class Action :
    type: str
    arguments: dict = field (default_factory=dict)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

# ai = Action("open" ,{"args":["chrome"]})

# print(ai.type)
# ai.arguments["args"]
