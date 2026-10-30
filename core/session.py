from dataclasses import dataclass, field
from datetime import datetime
from .message import Message
from config.settings import config
import json
from pathlib import Path
import uuid
import os


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Sessions"
    transcript: list[Message] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    owner: str = "local"


    def add_message(self, message: Message):
        self.transcript.append(message)


    def get_messages(self):
        return self.transcript


    def save(self):

        session_folder = Path(config["session_folder"])
        session_folder.mkdir(parents=True, exist_ok=True)

        file = session_folder / f"{self.id}.json"
        temp_file = session_folder/f"{self.id}.tmp"
        data = {
            "id": self.id,
            "title": self.title,
            "transcript": [
                {
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                    "metadata": message.metadata
                }
                for message in self.transcript
            ],
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "owner": self.owner
        }

        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            if not temp_file.exists():
                raise FileNotFoundError(
                    f"Temporary session file was not created: {temp_file}"
                )
            
            temp_file.replace(file)
        except Exception:
            if temp_file.exists():
                temp_file.unlink()
            raise


    @classmethod
    def load(cls, session_id):
        file = (
            Path(config["session_folder"])
            / f"{session_id}.json"
        )

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        transcript = [
            Message(
                role=message["role"],
                content=message["content"],
                timestamp=datetime.fromisoformat(
                    message["timestamp"]
                ),
                metadata=message["metadata"]
            )
            for message in data["transcript"]
        ]

        return cls(
            id=data["id"],
            title=data.get("title", "Untitled Session"),
            transcript=transcript,
            context=data["context"],
            created_at=datetime.fromisoformat(
                data["created_at"]
            ),
            owner=data["owner"]
        )