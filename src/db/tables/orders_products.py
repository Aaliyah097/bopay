from sqlalchemy import Column, String, Integer, UniqueConstraint, ForeignKey
from .base import Base


class OrdersProducts(Base):
    __tablename__ = 'orders_products'

    order_id = Column(ForeignKey(
        'orders.id', ondelete='CASCADE'), nullable=True, index=True)
    product_id = Column(ForeignKey(
        'products.id', ondelete='CASCADE'), nullable=True, index=True)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint('order_id', 'product_id'),
    )
