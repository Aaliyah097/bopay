from sqladmin import ModelView
from src.db.tables.products import Products
from src.db.tables.orders import Orders
from src.db.tables.orders_products import OrdersProducts


class ProductsAdmin(ModelView, model=Products):
    column_list = ['id', 'name', 'price', 'created_at', 'updated_ad']


class OrdersAdmin(ModelView, model=Orders):
    column_list = ['id', 'user_id', 'payment_id',
                   'payment_status', 'created_at', 'updated_at']


class OrdersProductsAdmin(ModelView, model=OrdersProducts):
    column_list = ['id', 'created_at', 'updated_at',
                   'order_id', 'product_id', 'price', 'quantity']
