from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.customer_service.runtime import customer_service_runtime
from app.services.memory import memory_store

router = APIRouter(prefix="/chat", tags=["upload"])


@router.post("/upload-image")
async def upload_image(
    session_id: str = Form(...),
    image: Annotated[UploadFile, File(description="Customer product image")] = None,
) -> dict[str, object]:
    if memory_store.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, and WebP are supported")
    content = await image.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image is too large")
    capability = customer_service_runtime.executor.vision
    if not hasattr(capability, "search_image_bytes"):
        raise HTTPException(status_code=503, detail="Image search is not enabled for the current vision data source")
    try:
        result = await run_in_threadpool(capability.search_image_bytes, content, image.filename or "upload.jpg")
    except (ImportError, ModuleNotFoundError) as exc:
        raise HTTPException(status_code=503, detail="Vision model dependencies are not installed") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Image search failed: {exc}") from exc
    return {"accepted": True, "filename": image.filename, "size": len(content), **result.model_dump(mode="json")}
