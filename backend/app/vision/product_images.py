"""Shared content-addressed cache lookup for catalog product images."""

import hashlib
from pathlib import Path
from urllib.parse import urlsplit


SUPPORTED_IMAGE_SUFFIXES = {".webp", ".jpg", ".jpeg", ".png"}


def product_image_filename(image_url: str) -> str | None:
    suffix = Path(urlsplit(image_url).path).suffix.lower()
    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        return None
    return hashlib.sha256(image_url.encode("utf-8")).hexdigest() + suffix


def cached_product_image_path(image_url: str, image_dir: Path) -> Path | None:
    filename = product_image_filename(image_url)
    if filename is None:
        return None
    path = image_dir / filename
    return path if path.is_file() and path.stat().st_size else None
