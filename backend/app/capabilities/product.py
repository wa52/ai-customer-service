from collections.abc import Iterable

from app.schemas.runtime import CapabilityResult


PRODUCTS: list[dict[str, object]] = [
    {"sku": "R1001", "name": "Classic Band Ring", "category": "ring", "gender": "men", "material": "316L", "color": "black", "style": "simple", "moq": 100, "reference_price": None},
    {"sku": "R1002", "name": "Edge Detail Ring", "category": "ring", "gender": "men", "material": "316L", "color": "black", "style": "simple", "moq": 100, "reference_price": None},
    {"sku": "R1003", "name": "Contour Ring", "category": "ring", "gender": "men", "material": "316L", "color": "black", "style": "simple", "moq": 200, "reference_price": None},
]


class ProductCapability:
    def __init__(self, products: Iterable[dict[str, object]] | None = None, source: str = "product_catalog") -> None:
        self.products = list(products) if products is not None else PRODUCTS
        self.source = source

    def search(self, conditions: dict[str, object]) -> CapabilityResult:
        matches = [product for product in self.products if all(product.get(key) == value for key, value in conditions.items() if key in product and value is not None)]
        return CapabilityResult(success=True, data={"products": matches}, confidence=1.0, sources=[self.source])

    def get(self, sku: str) -> CapabilityResult:
        product = next((item for item in self.products if str(item.get("sku", "")).upper() == sku.upper()), None)
        if product is None:
            return CapabilityResult(success=False, error={"code": "NOT_FOUND", "message": "Product not found"}, sources=[self.source])
        return CapabilityResult(success=True, data={"product": product}, confidence=1.0, sources=[self.source])

    def search_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        return self.search(arguments)

    def get_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        return self.get(str(arguments.get("sku", "")))
