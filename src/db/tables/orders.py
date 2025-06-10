from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from .base import Base


class Orders(Base):
    __tablename__ = 'orders'

    payment_id = Column(String, nullable=True, unique=True)
    payment_status = Column(Integer, nullable=False, default=0)
    user_id = Column(Integer, nullable=False, index=True)

    orders_products = relationship(
        'OrdersProducts', backref='orders_products', lazy='joined'
    )
