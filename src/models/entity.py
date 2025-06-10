from datetime import datetime
from dataclasses import dataclass


@dataclass
class Entiy:
    id: str | None
    created_at: datetime
    updated_at: datetime
