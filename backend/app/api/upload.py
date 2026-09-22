from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.memory import memory_store

router = APIRouter(prefix="/chat", tags=["upload"])


@router.post("/upload-image")
async def upload_image(
    session_id: str,
    image: Annotated[UploadFile, File(description="Customer product image")],
) -> dict[str, object]:
    if memory_store.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, and WebP are supported")
    content = await image.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image is too large")
    return {"accepted": True, "filename": image.filename, "size": len(content), "vision_search": "not_configured"}

