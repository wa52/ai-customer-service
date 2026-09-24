import logging
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from app.customer_service.runtime import customer_service_runtime

router = APIRouter(prefix="/products", tags=["products"])
logger = logging.getLogger(__name__)
PRODUCT_IMAGE_DIR = Path(__file__).resolve().parents[3] / "data" / "products" / "images"
PRODUCT_NAME_TRANSLATIONS_PATH = Path(__file__).resolve().parents[3] / "data" / "products" / "product_names_zh.json"


def _load_name_translations() -> dict[str, str]:
    try:
        payload = json.loads(PRODUCT_NAME_TRANSLATIONS_PATH.read_text(encoding="utf-8"))
        return payload.get("names", {})
    except (OSError, json.JSONDecodeError, AttributeError):
        return {}


def _image_filename(url: str) -> str | None:
    suffix = Path(urlsplit(url).path).suffix.lower()
    if suffix not in {".webp", ".jpg", ".jpeg", ".png"}:
        return None
    return f"{hashlib.sha256(url.encode('utf-8')).hexdigest()}{suffix}"


@router.get("")
def list_products(
    request: Request,
    q: str = Query(default="", max_length=120),
    category: str | None = Query(default=None, max_length=40),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=48),
) -> dict[str, object]:
    capability = customer_service_runtime.executor.product
    conditions = {"category": category} if category else {}
    query = q.strip() or None
    try:
        result = capability.search(conditions, query=query, limit=page_size, offset=(page - 1) * page_size)
        total = capability.repository.count(conditions, query) if capability.repository else len(capability.search(conditions, query=query, limit=100_000).data["products"])
    except Exception as error:
        logger.exception("Product catalog query failed")
        raise HTTPException(status_code=503, detail="Product catalog is temporarily unavailable") from error
    items = result.data["products"]
    translations = _load_name_translations()
    for item in items:
        item["display_name"] = translations.get(str(item.get("name", "")), item.get("name", ""))
        source_image = str(item.get("image_url") or "")
        filename = _image_filename(source_image) if source_image else None
        if filename and (PRODUCT_IMAGE_DIR / filename).is_file():
            item["image_url"] = f"{str(request.base_url).rstrip('/')}/api/v1/products/images/{filename}"
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "source": result.sources[0] if result.sources else "product_catalog",
        "is_external_reference": True,
    }


@router.get("/images/{image_name}", include_in_schema=False)
def get_product_image(image_name: str) -> FileResponse:
    if not re.fullmatch(r"[a-f0-9]{64}\.(?:webp|jpg|jpeg|png)", image_name):
        raise HTTPException(status_code=404, detail="Image not found")
    path = PRODUCT_IMAGE_DIR / image_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})
