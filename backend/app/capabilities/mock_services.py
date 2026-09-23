from app.schemas.runtime import CapabilityResult


class MockPricingCapability:
    def quote(self, sku: str, quantity: int | None = None) -> CapabilityResult:
        prices = {"R1001": 2.80, "R1002": 3.20, "R1003": 4.10}
        price = prices.get(sku.upper())
        if price is None:
            return CapabilityResult(success=False, error={"code": "PRICE_NOT_FOUND", "message": "No mock price for this SKU"}, sources=["mock_pricing"])
        return CapabilityResult(success=True, data={"sku": sku.upper(), "currency": "USD", "unit_price": price, "quantity": quantity, "note": "Indicative mock price; final quote requires sales confirmation."}, confidence=0.95, sources=["mock_pricing"])

    def quote_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        quantity = arguments.get("quantity")
        return self.quote(str(arguments.get("sku", "")), int(quantity) if quantity is not None else None)


class MockKnowledgeCapability:
    def answer(self, question: str) -> CapabilityResult:
        return CapabilityResult(success=True, data={"answer": "Our stainless-steel jewelry uses 316L material by default. Samples and production details can be confirmed by sales.", "question": question, "mode": "mock"}, confidence=0.7, sources=["mock_knowledge_base"])

    def answer_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        return self.answer(str(arguments.get("question", "")))


class MockVisionCapability:
    def search(self, description: str) -> CapabilityResult:
        return CapabilityResult(success=True, data={"matches": [{"sku": "R1001", "similarity": 0.91}, {"sku": "R1002", "similarity": 0.86}], "description": description, "mode": "mock"}, confidence=0.6, sources=["mock_vision_search"])

    def search_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        return self.search(str(arguments.get("description", "")))
