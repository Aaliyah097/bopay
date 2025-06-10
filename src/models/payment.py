from dataclasses import dataclass
from enum import IntEnum


class PaymentStatus(IntEnum):
    PAYED = 1
    NOT_PAYED = 0
    CANCELED = -1


@dataclass
class Payment:
    id: str
    link: str
