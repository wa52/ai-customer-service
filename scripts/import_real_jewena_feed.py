"""Import the public Jewena merchant feed into the product capability tables."""

import csv
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FEED_URL = "https://jewena.com/merchant-feed.xml"
SOURCE_NAME = "Jewena"
NS = {"g": "http://base.google.com/ns/1.0"}


def text(item: ET.Element, name: str) -> str:
    return (item.findtext(f"g:{name}", default="", namespaces=NS) or "").strip()


def category(title: str) -> str:
    value = title.lower()
    for name, terms in (("ring", ("ring",)), ("necklace", ("necklace", "choker", "pendant")), ("earring", ("earring", "huggie", "hoop")), ("bracelet", ("bracelet", "bangle", "anklet"))):
        if any(term in value for term in terms):
            return name
    return "jewelry"


def material(title: str, description: str) -> str:
    value = f"{title} {description}".lower()
    if "316l" in value:
        return "316L"
    if re.search(r"\b316\b", value):
        return "316"
    if "304" in value:
        return "304"
    return "stainless steel"


def finish(title: str) -> str:
    value = title.lower()
    for name in ("PVD", "gold-plated", "silver-plated", "polished"):
        if name.lower() in value:
            return name
    return ""


def main() -> None:
    request = urllib.request.Request(FEED_URL, headers={"User-Agent": "ai-customer-service-public-data-import/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        root = ET.fromstring(response.read())
    products = []
    for item in root.findall(".//item"):
        sku = text(item, "id")
        title = text(item, "title")
        link = text(item, "link")
        price = text(item, "price")
        if not sku or not title or not link:
            continue
        amount, _, currency = price.partition(" ")
        try:
            reference_price = float(amount)
        except ValueError:
            reference_price = None
        description = text(item, "description")
        products.append({
            "external_id": sku,
            "name": title,
            "category": category(title),
            "material": material(title, description),
            "plating": finish(title),
            "color": "",
            "size": "",
            "style": "",
            "gender": "unisex",
            "stone": "",
            "moq": 1,
            "reference_price": reference_price,
            "currency": currency or "USD",
            "image_url": text(item, "image_link"),
            "source_url": link,
            "source_name": SOURCE_NAME,
            "data_kind": "external_reference",
            "is_external_reference": "true",
        })
    products_dir = DATA / "products"
    products_dir.mkdir(parents=True, exist_ok=True)
    fields = list(products[0])
    with (products_dir / "products_public.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(products)
    price_fields = ["external_id", "reference_price", "currency", "price_basis", "source_url", "source_name", "retrieved_at", "data_kind", "is_external_reference"]
    with (products_dir / "external_prices.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=price_fields)
        writer.writeheader()
        for product in products:
            writer.writerow({"external_id": product["external_id"], "reference_price": product["reference_price"] or "", "currency": product["currency"], "price_basis": "public merchant feed single-piece price", "source_url": product["source_url"], "source_name": SOURCE_NAME, "retrieved_at": date.today().isoformat(), "data_kind": "external_reference", "is_external_reference": "true"})
    print(f"Imported {len(products)} real Jewena product variants.")


if __name__ == "__main__":
    main()
