import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.products import _load_name_translations
from app.customer_service.runtime import customer_service_runtime
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from app.services.memory import memory_store

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def _recommendation_cards(session_id: str) -> list[dict[str, object]]:
    state = memory_store.get_state(session_id)
    if state.last_action != "search_products":
        return []
    names = _load_name_translations()
    cards: list[dict[str, object]] = []
    for sku in state.candidate_products[:3]:
        result = customer_service_runtime.executor.product.get(sku)
        product = result.data.get("product")
        if result.success and isinstance(product, dict):
            product["display_name"] = names.get(str(product.get("name", "")), product.get("name", ""))
            cards.append(product)
    return cards


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
        try:
            async for token in customer_service_runtime.stream_message(request.session_id, request.content):
                yield f"event: token\ndata: {json.dumps({'text': token}, ensure_ascii=False)}\n\n"
            result = memory_store.latest_assistant(request.session_id)
            if result is not None:
                yield f"event: message\ndata: {json.dumps(result.model_dump(mode='json'), ensure_ascii=False)}\n\n"
            products = _recommendation_cards(request.session_id)
            if products:
                yield f"event: products\ndata: {json.dumps(products, ensure_ascii=False)}\n\n"
        except Exception:
            logger.exception("Chat stream failed for session %s", request.session_id)
            yield f"event: error\ndata: {json.dumps({'message': 'The assistant timed out or is temporarily unavailable.'})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/handoff", response_model=MessageResponse)
def request_handoff(request: ChatRequest) -> MessageResponse:
    if memory_store.get_session(request.session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return customer_service_runtime.handoff(request.session_id)
