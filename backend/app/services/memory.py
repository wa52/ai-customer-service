from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.chat import MessageResponse, SessionResponse


@dataclass
class ConversationState:
    requirements: dict[str, object] = field(default_factory=dict)
    candidate_products: list[str] = field(default_factory=list)
    selected_product: str | None = None
    missing_information: list[str] = field(default_factory=list)
    last_action: str | None = None


@dataclass
class Session:
    id: str
    status: str = "active"
    language: str = "en"
    summary: str = ""
    state: ConversationState = field(default_factory=ConversationState)
    messages: list[MessageResponse] = field(default_factory=list)


class InMemoryMemoryStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create_session(self) -> SessionResponse:
        session = Session(id=f"S-{uuid4().hex[:10].upper()}")
        self._sessions[session.id] = session
        return self._response(session)

    def get_session(self, session_id: str) -> SessionResponse | None:
        session = self._sessions.get(session_id)
        return self._response(session) if session else None

    def get_state(self, session_id: str) -> ConversationState:
        return self._sessions[session_id].state

    def append(self, session_id: str, role: str, content: str, action: str | None = None, intent: str | None = None) -> MessageResponse:
        message = MessageResponse(id=f"M-{uuid4().hex[:10]}", role=role, content=content, created_at=datetime.now(timezone.utc), action=action, intent=intent)
        self._sessions[session_id].messages.append(message)
        return message

    def set_status(self, session_id: str, status: str) -> None:
        self._sessions[session_id].status = status

    @staticmethod
    def _response(session: Session) -> SessionResponse:
        return SessionResponse(id=session.id, status=session.status, language=session.language, summary=session.summary, requirements=session.state.requirements, candidate_products=session.state.candidate_products, selected_product=session.state.selected_product, missing_information=session.state.missing_information, messages=session.messages)


memory_store = InMemoryMemoryStore()

