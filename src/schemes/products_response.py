from pydantic import BaseModel
from datetime import datetime


class ProductsResponse(BaseModel):
    id: str
    name: str
    price: int
    created_at: datetime
    updated_at: datetime | None
