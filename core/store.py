
import json
import sqlite3

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


DATABASE_PATH = Path("data/cj7.db")


class Store:

    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.initialize()

    # --------------------------------------------------
    # CONNECTION
    # --------------------------------------------------

    def connect(self):
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    @contextmanager
    def connection(self):
        db = self.connect()

        try:
            with db:
                yield db
        finally:
            db.close()

    # --------------------------------------------------
    # DATABASE INITIALIZATION
    # --------------------------------------------------

    def initialize(self):
        with self.connection() as db:

            db.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    summary TEXT DEFAULT '',
                    summarized_upto INTEGER DEFAULT 0,
                    owner TEXT DEFAULT 'local'
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_name TEXT,
                    tool_calls_json TEXT,
                    metadata_json TEXT DEFAULT '{}',
                    provenance_json TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,

                    FOREIGN KEY(session_id)
                        REFERENCES sessions(id)
                        ON DELETE CASCADE,

                    UNIQUE(session_id, position)
                );

                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL,

                    source_type TEXT NOT NULL DEFAULT 'user',
                    source_ref TEXT,
                    session_id TEXT,
                    message_id INTEGER,

                    FOREIGN KEY(session_id)
                        REFERENCES sessions(id)
                        ON DELETE SET NULL,

                    FOREIGN KEY(message_id)
                        REFERENCES messages(id)
                        ON DELETE SET NULL
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS search_fts
                USING fts5(text, source, ref);

                CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, position);

                CREATE INDEX IF NOT EXISTS idx_notes_session
                ON notes(session_id);
            """)

    # --------------------------------------------------
    # SESSIONS
    # --------------------------------------------------

    def create_session(self, session):
        now = datetime.now().isoformat()

        with self.connection() as db:
            db.execute("""
                INSERT INTO sessions (
                    id,
                    title,
                    created_at,
                    updated_at,
                    owner
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO NOTHING
            """, (
                session.id,
                session.title,
                session.created_at.isoformat(),
                now,
                session.owner
            ))

    def save_session(self, session):
        now = datetime.now().isoformat()

        with self.connection() as db:

            db.execute("""
                INSERT INTO sessions (
                    id,
                    title,
                    created_at,
                    updated_at,
                    owner
                )
                VALUES (?, ?, ?, ?, ?)

                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    updated_at = excluded.updated_at,
                    owner = excluded.owner
            """, (
                session.id,
                session.title,
                session.created_at.isoformat(),
                now,
                session.owner
            ))

            for position, message in enumerate(session.transcript):

                metadata = message.metadata or {}

                tool_name = metadata.get("tool_name")
                tool_calls = metadata.get("tool_calls")
                provenance = metadata.get("provenance", {})

                tool_calls_json = (
                    json.dumps(
                        tool_calls,
                        ensure_ascii=False,
                        default=str
                    )
                    if tool_calls is not None else None
                )

                metadata_json = json.dumps(
                    metadata,
                    ensure_ascii=False,
                    default=str
                )

                provenance_json = json.dumps(
                    provenance,
                    ensure_ascii=False,
                    default=str
                )

                existing = db.execute("""
                    SELECT id
                    FROM messages
                    WHERE session_id = ?
                    AND position = ?
                """, (
                    session.id,
                    position
                )).fetchone()

                if existing:

                    message_id = existing["id"]

                    db.execute("""
                        UPDATE messages
                        SET
                            role = ?,
                            content = ?,
                            tool_name = ?,
                            tool_calls_json = ?,
                            metadata_json = ?,
                            provenance_json = ?,
                            created_at = ?
                        WHERE id = ?
                    """, (
                        message.role,
                        message.content,
                        tool_name,
                        tool_calls_json,
                        metadata_json,
                        provenance_json,
                        message.timestamp.isoformat(),
                        message_id
                    ))

                else:

                    cursor = db.execute("""
                        INSERT INTO messages (
                            session_id,
                            position,
                            role,
                            content,
                            tool_name,
                            tool_calls_json,
                            metadata_json,
                            provenance_json,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session.id,
                        position,
                        message.role,
                        message.content,
                        tool_name,
                        tool_calls_json,
                        metadata_json,
                        provenance_json,
                        message.timestamp.isoformat()
                    ))

                    message_id = cursor.lastrowid

                # Keep the FTS entry synchronized.
                db.execute("""
                    DELETE FROM search_fts
                    WHERE source = 'message'
                    AND ref = ?
                """, (str(message_id),))

                # Tool outputs are stored but not indexed.
                if message.role in {"user", "assistant"} and message.content.strip():

                    db.execute("""
                        INSERT INTO search_fts (
                            text,
                            source,
                            ref
                        )
                        VALUES (?, 'message', ?)
                    """, (
                        message.content,
                        str(message_id)
                    ))

    def get_session(self, session_id):

        with self.connection() as db:

            session = db.execute("""
                SELECT *
                FROM sessions
                WHERE id = ?
            """, (session_id,)).fetchone()

            if session is None:
                return None

            messages = db.execute("""
                SELECT *
                FROM messages
                WHERE session_id = ?
                ORDER BY position ASC
            """, (session_id,)).fetchall()

            return {
                "session": dict(session),
                "messages": [
                    dict(message)
                    for message in messages
                ]
            }

    def list_sessions(self):

        with self.connection() as db:

            rows = db.execute("""
                SELECT
                    id,
                    title,
                    created_at,
                    updated_at
                FROM sessions
                ORDER BY updated_at DESC
            """).fetchall()

            return [dict(row) for row in rows]

    def rename_session(self, session_id, new_title):

        with self.connection() as db:

            cursor = db.execute("""
                UPDATE sessions
                SET
                    title = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                new_title,
                datetime.now().isoformat(),
                session_id
            ))

            return cursor.rowcount > 0

    # --------------------------------------------------
    # NOTES
    # --------------------------------------------------

    def add_note(
        self,
        text,
        source_type="user",
        source_ref=None,
        session_id=None,
        message_id=None
    ):

        if not text or not text.strip():
            raise ValueError("Note text cannot be empty.")

        created_at = datetime.now().isoformat()
        text = text.strip()

        with self.connection() as db:

            cursor = db.execute("""
                INSERT INTO notes (
                    text,
                    created_at,
                    source_type,
                    source_ref,
                    session_id,
                    message_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                text,
                created_at,
                source_type,
                source_ref,
                session_id,
                message_id
            ))

            note_id = cursor.lastrowid

            db.execute("""
                INSERT INTO search_fts (
                    text,
                    source,
                    ref
                )
                VALUES (?, 'note', ?)
            """, (
                text,
                str(note_id)
            ))

            return note_id

    def get_note(self, note_id):

        with self.connection() as db:

            row = db.execute("""
                SELECT *
                FROM notes
                WHERE id = ?
            """, (note_id,)).fetchone()

            return dict(row) if row else None

    def list_notes(self, limit=100):

        with self.connection() as db:

            rows = db.execute("""
                SELECT *
                FROM notes
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [
                dict(row)
                for row in rows
            ]

    # --------------------------------------------------
    # FULL TEXT SEARCH
    # --------------------------------------------------

    def search(self, query, limit=5):

        if not query or not query.strip():
            return []

        terms = query.strip().split()

        safe_query = " AND ".join(
            '"' + term.replace('"', '""') + '"'
            for term in terms
        )

        with self.connection() as db:

            rows = db.execute("""
                SELECT
                    text,
                    source,
                    ref,
                    bm25(search_fts) AS score
                FROM search_fts
                WHERE search_fts MATCH ?
                ORDER BY score
                LIMIT ?
            """, (
                safe_query,
                limit
            )).fetchall()

            return [
                dict(row)
                for row in rows
            ]


# --------------------------------------------------
# SHARED STORE INSTANCE
# --------------------------------------------------

store = Store()
