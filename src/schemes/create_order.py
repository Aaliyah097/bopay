from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    quantity: int = Field(gt=0)


class CreateOrder(BaseModel):
    user_id: int
    candidate_id: int
    email: str
    products: list[Product]
    success_redirect_url: str | None
