from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_session_and_contextual_clarification() -> None:
    session = client.post("/api/v1/chat/sessions").json()
    response = client.post("/api/v1/chat/messages", json={"session_id": session["id"], "content": "I need rings"})
    assert response.status_code == 200
    assert "style" in response.json()["session"]["missing_information"]


def test_handoff_marks_session() -> None:
    session = client.post("/api/v1/chat/sessions").json()
    response = client.post("/api/v1/chat/handoff", json={"session_id": session["id"], "content": "human please"})
    assert response.status_code == 200
    assert response.json()["message"]["action"] == "request_human_handoff"

