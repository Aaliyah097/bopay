from .repository import get_products_by_ids, create_order, create_payment_link, update_order
from src.schemes.create_order import CreateOrder
from src.db.pg_client import db_session
from fastapi import HTTPException
from src.models.product import OrderProduct
from src.schemes.new_order_response import NewOrderResponse


async def new_order(request: CreateOrder) -> str:
    async with db_session() as session:
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

        payment = await create_payment_link(
            amount=sum(product.sum_ for product in products),
            order_id=order.id,
            success_redirect_url=request.success_redirect_url
        )

        await update_order(session, order.id, payment.id)

    return NewOrderResponse(
        order_id=order.id,
        payment_link=payment.link
    )
