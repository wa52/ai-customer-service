from fastapi import APIRouter, HTTPException

from app.schemas.chat import SessionResponse
from app.services.memory import memory_store

router = APIRouter(prefix="/chat/sessions", tags=["session"])


@router.post("", response_model=SessionResponse)
def create_session() -> SessionResponse:
    return memory_store.create_session()


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str) -> SessionResponse:
    session = memory_store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

