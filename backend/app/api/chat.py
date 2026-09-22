import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.customer_service.runtime import customer_service_runtime
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from app.services.memory import memory_store

router = APIRouter(prefix="/chat", tags=["chat"])


def _validate_session(request: ChatRequest) -> None:
    if memory_store.get_session(request.session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/messages", response_model=ChatResponse)
async def send_message(request: ChatRequest) -> ChatResponse:
    _validate_session(request)
    result = await customer_service_runtime.handle_message(request.session_id, request.content)
    return ChatResponse(message=result, session=memory_store.get_session(request.session_id))


@router.post("/messages/stream")
async def stream_message(request: ChatRequest) -> StreamingResponse:
    _validate_session(request)

    async def events() -> AsyncIterator[str]:
        async for token in customer_service_runtime.stream_message(request.session_id, request.content):
            yield f"event: token\ndata: {json.dumps({'text': token}, ensure_ascii=False)}\n\n"
        result = memory_store.latest_assistant(request.session_id)
        if result is not None:
            yield f"event: message\ndata: {json.dumps(result.model_dump(mode='json'), ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/handoff", response_model=MessageResponse)
def request_handoff(request: ChatRequest) -> MessageResponse:
    if memory_store.get_session(request.session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return customer_service_runtime.handoff(request.session_id)
