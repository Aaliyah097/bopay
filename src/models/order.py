from dataclasses import dataclass
from .entity import Entiy
from .product import OrderProduct
from .payment import PaymentStatus
from enum import Enum


class OrderStatus(Enum):
    NEW = 'new'
    PAYED = 'payed'
    PRODUCT_SHIPPPED = 'product_shipped'
    RECEIPT_SENT = 'receipt_sent'
    FINISHED = 'finished'
    CANCELED = 'canceled'


@dataclass
class Order(Entiy):
    user_id: int
    user_email: str
    payment_id: str | None
    receipt_id: str | None
    payment_status: PaymentStatus
    products: list[OrderProduct]
    meta: dict | None
    status: OrderStatus = OrderStatus.NEW

    @property
    def sum_(self) -> int:
        return sum(product.sum_ for product in self.products)
