from collections.abc import Iterable
import re

from app.schemas.runtime import CapabilityResult
from app.repositories.product_repository import ProductRepository


PRODUCTS: list[dict[str, object]] = [
    {"sku": "R1001", "name": "Classic Band Ring", "category": "ring", "gender": "men", "material": "316L", "color": "black", "style": "simple", "moq": 100, "reference_price": None},
    {"sku": "R1002", "name": "Edge Detail Ring", "category": "ring", "gender": "men", "material": "316L", "color": "black", "style": "simple", "moq": 100, "reference_price": None},
    {"sku": "R1003", "name": "Contour Ring", "category": "ring", "gender": "men", "material": "316L", "color": "black", "style": "simple", "moq": 200, "reference_price": None},
]


class ProductCapability:
    def __init__(self, products: Iterable[dict[str, object]] | None = None, source: str = "product_catalog", repository: ProductRepository | None = None) -> None:
        self.products = list(products) if products is not None else PRODUCTS
        self.source = source
        self.repository = repository

    def search(self, conditions: dict[str, object], query: str | None = None, limit: int = 100, offset: int = 0) -> CapabilityResult:
        if self.repository:
            matches = self.repository.search(conditions, query, limit, offset)
        else:
            matches = [product for product in self.products if all(product.get(key) == value for key, value in conditions.items() if key in product and value is not None)]
            if query:
                terms = query.casefold().split()
                matches = [product for product in matches if all(term in " ".join(str(value) for value in product.values()).casefold() for term in terms)]
            matches = matches[offset:offset + limit]
        return CapabilityResult(success=True, data={"products": matches}, confidence=1.0, sources=[self.source])

    def get(self, sku: str) -> CapabilityResult:
        product = self.repository.get(sku) if self.repository else next((item for item in self.products if str(item.get("sku", "")).upper() == sku.upper()), None)
        if product is None:
            return CapabilityResult(success=False, error={"code": "NOT_FOUND", "message": "Product not found"}, sources=[self.source])
        return CapabilityResult(success=True, data={"product": product}, confidence=1.0, sources=[self.source])

    def search_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        conditions = {key: value for key, value in arguments.items() if key not in {"query", "limit"}}
        result = self.search(conditions, query=str(arguments["query"]) if arguments.get("query") else None, limit=100)
        products = result.data.get("products", [])
        distinct: list[dict[str, object]] = []
        seen: set[str] = set()
        for product in products:
            name = str(product.get("name", ""))
            style_name = re.sub(r"\s*/\s*[^/]*$", "", name).casefold().strip() or str(product.get("sku", ""))
            if style_name in seen:
                continue
            seen.add(style_name)
            distinct.append(product)
            if len(distinct) >= min(int(arguments.get("limit", 3)), 3):
                break
        result.data["products"] = distinct
        return result

    def get_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        return self.get(str(arguments.get("sku", "")))
