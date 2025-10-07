import uuid

class InMemorySessionStore:
    def __init__(self):
        self.sessions = {}

    def create(self, data: dict) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = data
        return session_id

    def get(self, session_id: str) -> dict | None:
        return self.sessions.get(session_id)

    def delete(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

session_store = InMemorySessionStore()