from urllib.parse import urlparse, parse_qs
from datetime import datetime
from sqlalchemy import select, update, and_
from src.db.pg_client import AsyncSession
from src.models.product import Product, OrderProduct
from src.db.tables.products import Products
from src.db.tables.orders import Orders
from src.db.tables.orders_products import OrdersProducts
from src.models.order import PaymentStatus, Order
from src.db.ekassa_client import EkassaClient
from src.settings import settings
from src.models.payment import Payment
from src.db.http_client import UkassaClient
from src.db.pg_client import db_session
from src.schemes.products_response import ProductsResponse


async def get_products_by_ids(session: AsyncSession, products_ids: list[str]) -> list[Product]:
    query = select(Products).where(Products.id.in_(products_ids))
    result = (await session.execute(query)).scalars().all()
    return [
        Product(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            name=row.name,
            price=row.price
        ) for row in result
    ]


async def get_unpaid_orders(session: AsyncSession) -> list[Order]:
    query = select(Orders).where(
        and_(
            Orders.payment_status == PaymentStatus.NOT_PAYED.value,
            Orders.payment_id != None
        )
    )

    result = (await session.execute(query)).unique().scalars().all()
    return [
        Order(
            id=order.id,
            user_id=order.user_id,
            created_at=order.created_at,
            updated_at=order.updated_at,
            payment_id=order.payment_id,
            payment_status=order.payment_status,
            products=[
                OrderProduct(
                    order_id=order_product.order_id,
                    product_id=order_product.product_id,
                    name=order_product.name,
                    price=order_product.price,
                    quantity=order_product.quantity,
                ) for order_product in order.orders_products
            ]
        ) for order in result
    ]


async def update_order(
    session: AsyncSession,
    order_id: str,
    payment_id: str | None = None,
    payment_status: PaymentStatus | None = None
) -> None:
    payload = {}
    if payment_id:
        payload['payment_id'] = payment_id
    if payment_status:
        payload['payment_status'] = payment_status.value

    if not payload:
        return

    query = update(Orders).where(
        Orders.id == order_id
    ).values(payload)
    await session.execute(query)


async def create_order(
    session: AsyncSession,
    user_id: str,
    products: list[OrdersProducts]
) -> Order:
    new_order = Orders(
        payment_id=None,
        payment_status=PaymentStatus.NOT_PAYED,
        user_id=user_id
    )

    session.add(new_order)
    await session.flush([new_order])

    session.add_all(
        [
            OrdersProducts(
                order_id=new_order.id,
                product_id=product.product_id,
                name=product.name,
                quantity=product.quantity,
                price=product.price
            ) for product in products
        ]
    )

    return Order(
        id=new_order.id,
        created_at=new_order.created_at,
        updated_at=new_order.updated_at,
        user_id=user_id,
        payment_id=None,
        payment_status=PaymentStatus.NOT_PAYED,
        products=products
    )


async def create_payment_link(
    order_id: str,
    email: str,
    products: list[OrderProduct],
) -> Payment:
    total_cost = sum(product.sum_ for product in products)
    payload = {
        "external_id": order_id,
        "receipt": {
            "client": {
                "email": email,
            },
            "company": {
                "email": settings.COMPANY_EMAIL,
                "inn": str(settings.COMPANY_INN),
                "payment_address": settings.COMPANY_WEBSITE_URL
            },
            "items": [
                {
                    "name": product.name,
                    "price": product.price,
                    "quantity": product.quantity,
                    "sum": product.sum_,
                    "payment_object": 'service',
                    "vat": {
                        "type": 'none'
                    }
                } for product in products
            ],
            "payments": [
                {
                    'type': settings.EKASSA_PAYMENT_CODE,
                    'sum': total_cost
                }
            ],
            "vats": [],
            "total": total_cost
        },
        "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
    }

    async with EkassaClient.session(settings.EKASSA_BASE_URL) as session:
        response = await session.request(
            'POST',
            f'fiscalorder/v4/{settings.EKASSA_GROUP_CODE}/sell',
            json=payload
        )

    link = response['invoice_payload']['link']
    return Payment(
        id=str(parse_qs(urlparse(link, allow_fragments=False).query)
               ['orderId'][0]),
        link=link
    )


async def check_receipt_status(payment_id: str) -> PaymentStatus:
    assert payment_id
    async with EkassaClient.session(settings.EKASSA_BASE_URL) as session:
        response = await session.request(
            'GET',
            f'/fiscalorder/v4/{settings.EKASSA_GROUP_CODE}/report/{payment_id}'
        )
        status = response['status']

    match status:
        case 'done':
            return PaymentStatus.PAYED
        case 'fail':
            return PaymentStatus.CANCELED
        case 'wait':
            return PaymentStatus.NOT_PAYED
        case _:
            print(f"Неизвестный статус чека: {status}")
            return PaymentStatus.NOT_PAYED


async def check_payment_status(payment_id: str) -> PaymentStatus:
    assert payment_id
    async with UkassaClient.session(settings.UKASSA_BASE_URL) as session:
        response = await session.request(
            'GET',
            f'payments/{str(payment_id)}',
        )
        status = response['status']

    match status:
        case 'pending':
            return PaymentStatus.NOT_PAYED
        case 'waiting_for_capture':
            return PaymentStatus.PAYED
        case 'succeeded':
            return PaymentStatus.PAYED
        case 'canceled':
            return PaymentStatus.CANCELED
        case _:
            print(f"Неизвестный статус чека: {status}")
            return PaymentStatus.NOT_PAYED


async def check_order_status(order_id: str) -> PaymentStatus | None:
    query = select(Orders.payment_status).where(Orders.id == order_id)
    async with db_session() as session:
        return (await session.execute(query)).scalar_one_or_none()


async def get_products_list() -> list[ProductsResponse]:
    query = select(Products)
    async with db_session() as session:
        result = (await session.execute(query)).scalars().all()

    return [ProductsResponse(**row.to_dict()) for row in result]
