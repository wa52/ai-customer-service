import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.customer_service.runtime import customer_service_runtime
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from app.services.memory import memory_store

router = APIRouter(prefix="/chat", tags=["chat"])


def _handle(request: ChatRequest) -> MessageResponse:
    if memory_store.get_session(request.session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return customer_service_runtime.handle_message(request.session_id, request.content)


@router.post("/messages", response_model=ChatResponse)
def send_message(request: ChatRequest) -> ChatResponse:
    result = _handle(request)
    return ChatResponse(message=result, session=memory_store.get_session(request.session_id))


@router.post("/messages/stream")
def stream_message(request: ChatRequest) -> StreamingResponse:
    result = _handle(request)

    def events() -> Iterator[str]:
        yield f"event: message\ndata: {json.dumps(result.model_dump(), ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/handoff", response_model=MessageResponse)
def request_handoff(request: ChatRequest) -> MessageResponse:
    if memory_store.get_session(request.session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return customer_service_runtime.handoff(request.session_id)

