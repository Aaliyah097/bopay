import logging
import os
import sys

from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from src.schemes.create_order import CreateOrder

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
    force=True,
)
from src.auth.actions import auth_router
from src.auth.auth import auth
from src.service import new_order
from sqladmin import Admin
from src.db.pg_client import pg_engine
from src.admin.tables import ProductsAdmin, OrdersAdmin, OrdersProductsAdmin
from src.admin.auth import AdminAuth
from src.settings import settings
from src.schemes.new_order_response import NewOrderResponse
from src.models.payment import PaymentStatus
from src.repository import check_order_status, get_products_list
from src.schemes.products_response import ProductsResponse
from contextlib import asynccontextmanager
from src.workers import monitor_payments
from src.workers import send_receipts
from src.workers import ship_orders
from src.workers import verify_receipts
from src.workers import destroy_candidates
import asyncio


@asynccontextmanager
async def lifespan(_: FastAPI):
    asyncio.create_task(monitor_payments.main())
    asyncio.create_task(ship_orders.main())
    asyncio.create_task(send_receipts.main())
    asyncio.create_task(verify_receipts.main())
    asyncio.create_task(destroy_candidates.main())
    yield


app = FastAPI(lifespan=lifespan)
admin = Admin(
    app,
    pg_engine,
    authentication_backend=AdminAuth(settings.ADMIN_SECRET_KEY)
)
admin.add_view(ProductsAdmin)
admin.add_view(OrdersAdmin)
admin.add_view(OrdersProductsAdmin)

app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    '/orders/',
    summary="Создать новый заказ и ссылку на оплату",
    response_model=NewOrderResponse
)
async def create_order(
    request: CreateOrder,
    # _=Depends(auth)  # TODO
) -> str:
    # TODO сделать проверку юзер_ид при создании заказа с тем что в токене
    return await new_order(request)


@app.get(
    '/orders/{order_id}/status',
    summary="Узнать статус оплаты заказа",
    response_model=PaymentStatus,
    responses={
        '200': {'descrition': 'OK'},
        '404': {'descrition': 'Заказ не найден'}
    }
)
async def get_order(
    order_id: str,
    _=Depends(auth)
):
    # TODO сделать проверку юзер_ид при создании заказа с тем что в токене
    status = await check_order_status(order_id)
    if status is None:
        return Response(status_code=404)
    return status


@app.get(
    '/products',
    summary='Список товаров',
    response_model=list[ProductsResponse]
)
async def list_products(
    _=Depends(auth)
):
    return await get_products_list()
