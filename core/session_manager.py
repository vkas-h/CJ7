from pathlib import Path

from .session import Session
from config.settings import config


class SessionManager:

    def __init__(self):
        self.session_folder = Path(
            config["session_folder"]
        )

        self.session_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        self.current_session = None


    def create(self):
        session = Session()

        self.current_session = session

        return session


    def load_session(self, session_id):
        session = Session.load(session_id)

        self.current_session = session

        return session


    def list_sessions(self):
        sessions = []

        for file in self.session_folder.glob("*.json"):

            try:
                session = Session.load(file.stem)

                sessions.append({
                    "id": session.id,
                    "title": session.title,
                    "created_at": session.created_at
                })

            except Exception as e:
                print(
                    f"[WARNING] Failed to load session: {file.name}"
                )
                print(f"[ERROR] {e}")

        # Newest first
        sessions.sort(
            key=lambda session: session["created_at"],
            reverse=True
        )

        return sessions


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

        return Session.load(
            sessions[0]["id"]
        )


    def rename_session(self, index, new_title):

        session = self.get_by_index(index)

        if session is None:
            return None

        session.title = new_title

        session.save()

        # If we renamed the active session,
        # update the active object too.
        if (
            self.current_session is not None
            and self.current_session.id == session.id
        ):
            self.current_session.title = new_title

        return session


session_manager = SessionManager()