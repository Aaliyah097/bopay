from sqlalchemy import Column, String, Integer
from .base import Base


class Products(Base):
    __tablename__ = 'products'

    name = Column(String, nullable=False, unique=True)
    price = Column(Integer, nullable=False)
