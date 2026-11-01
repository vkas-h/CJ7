
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import uuid

from .message import Message
from .store import store


@dataclass
class Session:

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Session"
    transcript: list[Message] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    owner: str = "local"

    def __post_init__(self):
        self._ensure_context_column()

    @staticmethod
    def _ensure_context_column():
        with store.connection() as db:
            columns = {
                row["name"]
                for row in db.execute(
                    "PRAGMA table_info(sessions)"
                ).fetchall()
            }

            if "context_json" not in columns:
                db.execute("""
                    ALTER TABLE sessions
                    ADD COLUMN context_json TEXT DEFAULT '{}'
                """)

    # --------------------------------------------------
    # TRANSCRIPT
    # --------------------------------------------------

    def add_message(self, message: Message):
        self.transcript.append(message)

    def get_messages(self):
        return self.transcript

    # --------------------------------------------------
    # PERSISTENCE
    # --------------------------------------------------

    def save(self):
        store.save_session(self)

        with store.connection() as db:
            db.execute("""
                UPDATE sessions
                SET context_json = ?
                WHERE id = ?
            """, (
                json.dumps(
                    self.context,
                    ensure_ascii=False,
                    default=str
                ),
                self.id
            ))

    @classmethod
    def load(cls, session_id):

        stored = store.get_session(session_id)

        if stored is None:
            raise FileNotFoundError(
                f"Session not found: {session_id}"
            )

        session_data = stored["session"]

        transcript = []

        for item in stored["messages"]:

            metadata = json.loads(
                item.get("metadata_json") or "{}"
            )

            if item.get("tool_name"):
                metadata.setdefault(
                    "tool_name",
                    item["tool_name"]
                )

            if item.get("tool_calls_json"):
                metadata.setdefault(
                    "tool_calls",
                    json.loads(item["tool_calls_json"])
                )

            transcript.append(
                Message(
                    role=item["role"],
                    content=item["content"],
                    timestamp=datetime.fromisoformat(
                        item["created_at"]
                    ),
                    metadata=metadata
                )
            )

        context = json.loads(
            session_data.get("context_json") or "{}"
        )

        return cls(
            id=session_data["id"],
            title=session_data["title"],
            transcript=transcript,
            context=context,
            created_at=datetime.fromisoformat(
                session_data["created_at"]
            ),
            owner=session_data.get("owner", "local")
        )
