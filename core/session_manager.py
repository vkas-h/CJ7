
from datetime import datetime

from .session import Session
from .store import store


class SessionManager:

    def __init__(self):
        self.current_session = None

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    def create(self):
        session = Session()

        session.save()

        self.current_session = session

        return session

    # --------------------------------------------------
    # LOAD
    # --------------------------------------------------

    def load_session(self, session_id):
        session = Session.load(session_id)

        self.current_session = session

        return session

    def get_by_index(self, index):

        sessions = self.list_sessions()

        if index < 1 or index > len(sessions):
            return None

        session_id = sessions[index - 1]["id"]

        return Session.load(session_id)

    def load_by_index(self, index):

        session = self.get_by_index(index)

        if session is None:
            return None

        self.current_session = session

        return session

    def get_latest_session(self):

        sessions = self.list_sessions()

        if not sessions:
            return None

        return Session.load(sessions[0]["id"])

    # --------------------------------------------------
    # LIST
    # --------------------------------------------------

    def list_sessions(self):

        sessions = store.list_sessions()

        for session in sessions:
            session["created_at"] = datetime.fromisoformat(
                session["created_at"]
            )

            session["updated_at"] = datetime.fromisoformat(
                session["updated_at"]
            )

        return sessions

    # --------------------------------------------------
    # RENAME
    # --------------------------------------------------

    def rename_session(self, index, new_title):

        session = self.get_by_index(index)

        if session is None:
            return None

        if not new_title or not new_title.strip():
            return None

        new_title = new_title.strip()

        updated = store.rename_session(
            session.id,
            new_title
        )

        if not updated:
            return None

        session.title = new_title

        if (
            self.current_session is not None
            and self.current_session.id == session.id
        ):
            self.current_session.title = new_title

        return session


session_manager = SessionManager()
