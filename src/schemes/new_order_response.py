from pydantic import BaseModel


class NewOrderResponse(BaseModel):
    order_id: str
    payment_link: str
