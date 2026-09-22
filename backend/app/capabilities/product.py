from app.schemas.runtime import CapabilityResult


PRODUCTS: list[dict[str, object]] = [
    {"sku": "R1001", "name": "Classic Band Ring", "category": "ring", "gender": "men", "material": "316L", "color": "black", "style": "simple", "moq": 100, "reference_price": None},
    {"sku": "R1002", "name": "Edge Detail Ring", "category": "ring", "gender": "men", "material": "316L", "color": "black", "style": "simple", "moq": 100, "reference_price": None},
    {"sku": "R1003", "name": "Contour Ring", "category": "ring", "gender": "men", "material": "316L", "color": "black", "style": "simple", "moq": 200, "reference_price": None},
]


class ProductCapability:
    def search(self, conditions: dict[str, object]) -> CapabilityResult:
        matches = [product for product in PRODUCTS if all(product.get(key) == value for key, value in conditions.items() if key in product)]
        return CapabilityResult(success=True, data={"products": matches}, confidence=1.0, sources=["product_catalog"])

    def get(self, sku: str) -> CapabilityResult:
        product = next((item for item in PRODUCTS if item["sku"] == sku), None)
        if product is None:
            return CapabilityResult(success=False, error={"code": "NOT_FOUND", "message": "Product not found"}, sources=["product_catalog"])
        return CapabilityResult(success=True, data={"product": product}, confidence=1.0, sources=["product_catalog"])

    def search_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        return self.search(arguments)

    def get_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        return self.get(str(arguments.get("sku", "")))
