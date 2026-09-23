from app.capabilities.product import ProductCapability
from app.repositories.product_repository import ProductRepository


class RepositoryProductCapability(ProductCapability):
    def __init__(self, repository: ProductRepository, source: str) -> None:
        super().__init__(repository=repository, source=source)
