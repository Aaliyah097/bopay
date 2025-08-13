from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import Base


class Orders(Base):
    __tablename__ = 'orders'

    payment_id = Column(String, nullable=True)
    receipt_id = Column(String, nullable=True)
    payment_status = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=True)
    cancel_reason = Column(String, nullable=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_email = Column(String, nullable=True)
    meta = Column(JSONB, nullable=True)

    orders_products = relationship(
        'OrdersProducts', backref='orders_products', lazy='joined'
    )
