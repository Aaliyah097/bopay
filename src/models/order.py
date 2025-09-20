from dataclasses import dataclass
from .entity import Entiy
from .product import OrderProduct
from .payment import PaymentStatus
from enum import Enum


class OrderStatus(Enum):
    NEW = 'new'
    SHIPPPED = 'shipped'
    TO_DESTROY = 'to_destroy'
    CANCELED = 'canceled'


class ReceiptStatus(Enum):
    NOT_SENT = 'not_sent'
    SENT = 'sent'
    DELIVERED = 'delivered'


@dataclass
class Order(Entiy):
    user_id: int
    user_email: str
    payment_id: str | None
    receipt_id: str | None
    receipt_status: ReceiptStatus
    payment_status: PaymentStatus
    products: list[OrderProduct]
    meta: dict | None
    status: OrderStatus = OrderStatus.NEW

    @property
    def sum_(self) -> int:
        return sum(product.sum_ for product in self.products)
