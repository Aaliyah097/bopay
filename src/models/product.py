from dataclasses import dataclass
from .entity import Entiy


@dataclass
class Product(Entiy):
    name: str
    price: int


@dataclass
class OrderProduct:
    order_id: str | None
    product_id: str
    name: str
    quantity: int
    price: int

    @property
    def sum_(self) -> int:
        return self.quantity * self.price
