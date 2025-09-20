from .repository import (
    get_products_by_ids,
    create_order,
    create_payment_link,
    update_order,
    get_user_active_order,
    repeat_payment_link
)
from src.schemes.create_order import CreateOrder
from src.db.pg_client import db_session
from fastapi import HTTPException
from src.models.product import OrderProduct
from src.schemes.new_order_response import NewOrderResponse
from src.models.payment import PaymentStatus
from src.models.order import OrderStatus
import logging


async def new_order(request: CreateOrder) -> str:
    async with db_session() as session:
        user_active_orders = await get_user_active_order(
            session,
            request.user_id
        )

        if not user_active_orders:
            products = await get_products_by_ids(
                session,
                [product.id for product in request.products]
            )
            if len(products) != len(request.products):
                raise HTTPException(
                    status_code=422,
                    detail="Переданы несуществующие товары"
                )

            products = [
                OrderProduct(
                    order_id=None,
                    product_id=products[idx].id,
                    name=products[idx].name,
                    quantity=product.quantity,
                    price=products[idx].price
                ) for idx, product in enumerate(request.products)
            ]

            order = await create_order(
                session,
                request.user_id,
                request.email,
                products=products,
                meta={'candidate_id': request.candidate_id}
            )
        else:
            order = user_active_orders[0]
        
        if order.status in [
            OrderStatus.SHIPPPED.value, OrderStatus.SHIPPPED,
            OrderStatus.CANCELED.value, OrderStatus.CANCELED
        ]:
            raise HTTPException(
                status_code=400,
                detail="Ссылка на оплату более недействительна"
            )
        if order.payment_id:
            payment_link = repeat_payment_link(order.payment_id)
        else:
            try:
                payment = await create_payment_link(
                    amount=order.sum_,
                    order_id=order.id,
                    success_redirect_url=request.success_redirect_url
                )
            except KeyError as exc:
                logging.error(exc)
                raise HTTPException(
                    status_code=400,
                    detail="Ссылка более недействительна"
                )
            payment_link = payment.link
            await update_order(session, order.id, payment.id)

    return NewOrderResponse(
        order_id=order.id,
        payment_link=payment_link
    )
