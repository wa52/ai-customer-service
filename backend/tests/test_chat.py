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
    assert response.json()["action"] == "request_human_handoff"


def test_memory_does_not_repeat_confirmed_style() -> None:
    session = client.post("/api/v1/chat/sessions").json()
    session_id = session["id"]
    first = client.post("/api/v1/chat/messages", json={"session_id": session_id, "content": "I need rings"}).json()
    assert "style" in first["session"]["missing_information"]
    second = client.post("/api/v1/chat/messages", json={"session_id": session_id, "content": "Simple style"}).json()
    assert second["session"]["requirements"]["style"] == "simple"
    assert "style" not in second["session"]["missing_information"]
    assert "style" not in second["message"]["content"].lower()


def test_product_search_executor_and_second_reference() -> None:
    session_id = client.post("/api/v1/chat/sessions").json()["id"]
    client.post("/api/v1/chat/messages", json={"session_id": session_id, "content": "I need simple men's black 316L rings, 500 pcs"})
    session = client.get(f"/api/v1/chat/sessions/{session_id}").json()
    assert session["candidate_products"] == ["R1001", "R1002", "R1003"]
    response = client.post("/api/v1/chat/messages", json={"session_id": session_id, "content": "How much is the second one?"}).json()
    assert response["session"]["selected_product"] == "R1002"
    assert response["message"]["action"] == "get_product_information"


def test_stream_returns_multiple_token_events() -> None:
    session_id = client.post("/api/v1/chat/sessions").json()["id"]
    response = client.post("/api/v1/chat/messages/stream", json={"session_id": session_id, "content": "Hello"})
    assert response.status_code == 200
    assert response.text.count("event: token") > 1
    assert "event: done" in response.text
