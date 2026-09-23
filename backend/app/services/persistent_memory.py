import json
from app.services.memory import ConversationState, InMemoryMemoryStore, Session
from app.schemas.chat import MessageResponse


def _serialize(session: Session) -> str:
    payload = {
        "id": session.id,
        "status": session.status,
        "language": session.language,
        "summary": session.summary,
        "state": {
            "current_intent": session.state.current_intent,
            "requirements": session.state.requirements,
            "candidate_products": session.state.candidate_products,
            "selected_product": session.state.selected_product,
            "missing_information": session.state.missing_information,
            "last_action": session.state.last_action,
        },
        "messages": [message.model_dump(mode="json") for message in session.messages],
    }
    return json.dumps(payload, ensure_ascii=False)


def _deserialize(raw: str) -> Session:
    payload = json.loads(raw)
    state = ConversationState(**payload["state"])
    messages = [MessageResponse.model_validate(message) for message in payload["messages"]]
    return Session(id=payload["id"], status=payload["status"], language=payload["language"], summary=payload["summary"], state=state, messages=messages)


class RedisMemoryStore(InMemoryMemoryStore):
    def __init__(self, url: str) -> None:
        import redis

        super().__init__()
        self.client = redis.Redis.from_url(url, decode_responses=True)

    def _save(self, session: Session) -> None:
        self.client.set(f"customer-service:session:{session.id}", _serialize(session))

    def _load(self, session_id: str) -> Session | None:
        raw = self.client.get(f"customer-service:session:{session_id}")
        return _deserialize(raw) if raw else None


class PostgresMemoryStore(InMemoryMemoryStore):
    def __init__(self, url: str) -> None:
        import psycopg

        super().__init__()
        self.connection = psycopg.connect(url.replace("postgresql+asyncpg://", "postgresql://"), autocommit=True)
        with self.connection.cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS customer_service_sessions (id TEXT PRIMARY KEY, payload JSONB NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")

    def _save(self, session: Session) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO customer_service_sessions (id, payload, updated_at) VALUES (%s, %s::jsonb, NOW()) ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW()", (session.id, _serialize(session)))

    def _load(self, session_id: str) -> Session | None:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT payload::text FROM customer_service_sessions WHERE id = %s", (session_id,))
            row = cursor.fetchone()
        return _deserialize(row[0]) if row else None
