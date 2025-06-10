from dataclasses import dataclass
from .entity import Entiy
from .product import OrderProduct
from .payment import PaymentStatus


@dataclass
class Order(Entiy):
    user_id: int
    payment_id: str | None
    payment_status: PaymentStatus
    products: list[OrderProduct]

    @property
    def sum_(self) -> int:
        return sum(product.sum_ for product in self.products)
