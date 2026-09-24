"""Translate public product titles into Chinese through the configured model provider."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.config.local_config import load_admin_settings
from app.config.settings import get_settings


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "products" / "products_public.csv"
DESTINATION = ROOT / "data" / "products" / "product_names_zh.json"
SYSTEM_PROMPT = """你是珠宝电商的中文商品标题编辑。把英文商品标题翻译成自然、准确、简洁的简体中文。
规则：保留品牌/型号/SKU、数字、尺寸、单位和颜色对应关系；保留 316L、PVD、CZ 等行业缩写；把商品品类和材质译成常用中文；不增加原标题没有的卖点；只返回 JSON 数组，每项格式为 {\"id\": 输入编号, \"name_zh\": 中文标题}，不要 Markdown。"""


def _read_progress() -> dict[str, str]:
    if not DESTINATION.exists():
        return {}
    try:
        payload = json.loads(DESTINATION.read_text(encoding="utf-8"))
        return payload.get("names", {})
    except (OSError, json.JSONDecodeError, AttributeError):
        return {}


def _save_progress(translations: dict[str, str]) -> None:
    payload = {
        "language": "zh-CN",
        "source": "public product catalog titles; translated with configured model",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "names": translations,
    }
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=DESTINATION.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        temp_path = Path(handle.name)
    os.replace(temp_path, DESTINATION)


def _parse_json(content: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, list):
        raise ValueError("Model response was not a JSON list")
    return parsed


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=35)
    parser.add_argument("--concurrency", type=int, default=3)
    args = parser.parse_args()

    settings = load_admin_settings(get_settings())
    if not (settings.llm_base_url and settings.llm_api_key and settings.llm_model):
        raise SystemExit("No configured model found. Configure a provider in the backend admin page first.")

    with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
        names = list(dict.fromkeys(row["name"].strip() for row in csv.DictReader(handle) if row.get("name", "").strip()))
    translations = _read_progress()
    pending = [name for name in names if not translations.get(name)]
    batches = [pending[index:index + args.batch_size] for index in range(0, len(pending), args.batch_size)]
    semaphore = asyncio.Semaphore(args.concurrency)
    timeout = httpx.Timeout(60, connect=15)
    endpoint = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=timeout) as client:
        async def translate(index: int, batch: list[str]) -> tuple[int, list[tuple[str, str]]]:
            async with semaphore:
                items = [{"id": item_index, "name": name} for item_index, name in enumerate(batch)]
                payload = {
                    "model": settings.llm_model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps(items, ensure_ascii=False)},
                    ],
                }
                last_error: Exception | None = None
                for _ in range(3):
                    content = ""
                    try:
                        response = await client.post(endpoint, headers=headers, json=payload)
                        response.raise_for_status()
                        content = response.json()["choices"][0]["message"]["content"]
                        rows = _parse_json(content)
                        mapped: dict[int, str] = {}
                        for row_index, row in enumerate(rows):
                            if isinstance(row, str):
                                mapped[row_index] = row.strip()
                                continue
                            translated_name = next((row[key] for key in ("name_zh", "translation", "translated_name", "title_zh", "chinese_name", "name") if row.get(key)), "")
                            mapped[int(row.get("id", row_index))] = str(translated_name).strip()
                        if set(mapped) != set(range(len(batch))) or any(not value for value in mapped.values()):
                            raise ValueError("Translation response was incomplete")
                        return index, [(name, mapped[item_index]) for item_index, name in enumerate(batch)]
                    except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                        last_error = RuntimeError(f"{error}; response={content[:500]}")
                raise RuntimeError(f"Translation batch {index + 1} failed: {last_error}")

        tasks = [asyncio.create_task(translate(index, batch)) for index, batch in enumerate(batches)]
        finished = 0
        try:
            for task in asyncio.as_completed(tasks):
                _, translated = await task
                translations.update(translated)
                _save_progress(translations)
                finished += 1
                if finished % 5 == 0 or finished == len(batches):
                    print(f"translated {len(translations)}/{len(names)} titles", flush=True)
        except Exception:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

    if len(translations) != len(names):
        raise SystemExit(f"Incomplete translation: {len(translations)}/{len(names)}")
    print(f"Saved {len(translations)} Chinese product names to {DESTINATION}")


if __name__ == "__main__":
    asyncio.run(main())
