from dataclasses import dataclass
from enum import Enum


class PaymentStatus(Enum):
    PAYED = 'paid'
    NOT_PAYED = 'not_paid'
    CANCELED = 'canceled'
    WAITING_FOR_CAPTURE = 'waiting_for_capture'


@dataclass
class Payment:
    id: str
    link: str
