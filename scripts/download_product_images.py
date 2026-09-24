"""Download and locally cache the public product images referenced by the catalog CSV."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import os
from pathlib import Path
from urllib.parse import urlsplit

import httpx


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "products" / "products_public.csv"
IMAGE_DIR = ROOT / "data" / "products" / "images"
CONCURRENCY = 12


def _filename(url: str) -> str | None:
    suffix = Path(urlsplit(url).path).suffix.lower()
    if suffix not in {".webp", ".jpg", ".jpeg", ".png"}:
        return None
    return hashlib.sha256(url.encode("utf-8")).hexdigest() + suffix


async def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        urls = sorted({row["image_url"].strip() for row in csv.DictReader(handle) if row.get("image_url", "").strip()})

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(CONCURRENCY)
    completed = 0
    downloaded = 0
    failures: list[str] = []

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(25, connect=10),
        headers={"User-Agent": "SmartCustomerServiceCatalog/1.0"},
    ) as client:
        async def fetch(url: str) -> None:
            nonlocal completed, downloaded
            filename = _filename(url)
            if not filename:
                failures.append(url)
                return
            target = IMAGE_DIR / filename
            if target.is_file() and target.stat().st_size:
                completed += 1
                return

            async with semaphore:
                last_error: Exception | None = None
                for attempt in range(3):
                    try:
                        response = await client.get(url)
                        response.raise_for_status()
                        if not response.headers.get("content-type", "").lower().startswith("image/"):
                            raise ValueError("source did not return an image")
                        temporary = target.with_suffix(target.suffix + ".part")
                        temporary.write_bytes(response.content)
                        os.replace(temporary, target)
                        downloaded += 1
                        last_error = None
                        break
                    except (httpx.HTTPError, OSError, ValueError) as error:
                        last_error = error
                        if attempt < 2:
                            await asyncio.sleep(0.4 * (attempt + 1))
                if last_error:
                    failures.append(f"{url} ({last_error})")
                completed += 1
                if completed % 100 == 0 or completed == len(urls):
                    print(f"processed {completed}/{len(urls)}; downloaded {downloaded}; failed {len(failures)}", flush=True)

        await asyncio.gather(*(fetch(url) for url in urls))

    print(f"Done: {downloaded} downloaded, {len(urls) - downloaded - len(failures)} already cached, {len(failures)} failed.")
    if failures:
        failure_path = IMAGE_DIR / "download-failures.txt"
        failure_path.write_text("\n".join(failures), encoding="utf-8")
        print(f"Failed URLs written to {failure_path}")


if __name__ == "__main__":
    asyncio.run(main())
