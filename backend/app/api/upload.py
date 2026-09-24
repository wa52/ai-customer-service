from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from app.customer_service.runtime import customer_service_runtime
from app.services.memory import memory_store
from app.api.products import PRODUCT_IMAGE_DIR, _image_filename, _load_name_translations

router = APIRouter(prefix="/chat", tags=["upload"])


@router.post("/upload-image")
async def upload_image(
    request: Request,
    session_id: str = Form(...),
    image: Annotated[UploadFile, File(description="Customer product image")] = None,
) -> dict[str, object]:
    if memory_store.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, and WebP are supported")
    content = await image.read(10 * 1024 * 1024 + 1)
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
    payload = result.model_dump(mode="json")
    result_data = payload.get("data")
    if isinstance(result_data, dict):
        translations = _load_name_translations()
        matches = result_data.get("matches")
        if isinstance(matches, list):
            for match in matches:
                if not isinstance(match, dict) or not match.get("sku"):
                    continue
                match["display_name"] = translations.get(str(match.get("name", "")), match.get("name", ""))
                source_image = str(match.get("image_url") or "")
                filename = _image_filename(source_image) if source_image else None
                if filename and (PRODUCT_IMAGE_DIR / filename).is_file():
                    match["image_url"] = f"{str(request.base_url).rstrip('/')}/api/v1/products/images/{filename}"
    return {"accepted": True, "filename": image.filename, "size": len(content), **payload}
