from sqlalchemy import select, update, and_
from src.db.pg_client import AsyncSession
from src.models.product import Product, OrderProduct
from src.db.tables.products import Products
from src.db.tables.orders import Orders
from src.db.tables.orders_products import OrdersProducts
from src.models.order import PaymentStatus, Order
from src.models.order import OrderStatus, ReceiptStatus
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
    """Получить заказы которые ожидают оплаты"""
    query = select(Orders).where(
        and_(
            Orders.payment_status.in_(
                (PaymentStatus.NOT_PAYED.value,
                 PaymentStatus.WAITING_FOR_CAPTURE.value)
            ),
            Orders.payment_id != None
        )
    )

    return await _get_orders(session, query)


async def get_shipped_orders(session: AsyncSession) -> list[Order]:
    query = select(Orders).where(
        and_(
            Orders.status == OrderStatus.SHIPPPED.value,
            Orders.payment_status == PaymentStatus.PAYED.value,
            Orders.receipt_status == ReceiptStatus.NOT_SENT.value
        )
    )
    return await _get_orders(session, query)


async def get_to_destroy_orders(session: AsyncSession) -> list[Order]:
    query = select(Orders).where(
        Orders.status == OrderStatus.TO_DESTROY.value
    )
    return await _get_orders(session, query)


async def get_paid_orders(session: AsyncSession) -> list[Order]:
    query = select(Orders).where(
        and_(
            Orders.status == OrderStatus.NEW.value,
            Orders.payment_status == PaymentStatus.WAITING_FOR_CAPTURE.value
        )
    )
    return await _get_orders(session, query)


async def get_orders_with_sent_checks(session: AsyncSession) -> list[Order]:
    query = select(Orders).where(
        Orders.receipt_status == ReceiptStatus.SENT.value
    )
    return await _get_orders(session, query)


async def _get_orders(session: AsyncSession, query: select) -> list[Order]:
    return [
        Order(
            id=order.id,
            user_id=order.user_id,
            user_email=order.user_email,
            created_at=order.created_at,
            updated_at=order.updated_at,
            payment_id=order.payment_id,
            receipt_id=order.receipt_id,
            receipt_status=order.receipt_status,
            payment_status=order.payment_status,
            meta=order.meta,
            products=[
                OrderProduct(
                    order_id=order_product.order_id,
                    product_id=order_product.product_id,
                    name=order_product.name,
                    price=order_product.price,
                    quantity=order_product.quantity,
                ) for order_product in order.orders_products
            ]
        ) for order in (await session.execute(query)).unique().scalars().all()
    ]


async def update_order(
    session: AsyncSession,
    order_id: str,
    payment_id: str | None = None,
    payment_status: PaymentStatus | None = None,
    order_status: OrderStatus | None = None,
    receipt_status: ReceiptStatus | None = None,
    cancel_reason: str | None = None,
    receipt_id: str | None = None
) -> None:
    payload = {}
    if payment_id:
        payload['payment_id'] = payment_id
    if payment_status:
        payload['payment_status'] = payment_status.value
    if order_status:
        payload['status'] = order_status.value
    if cancel_reason:
        payload['cancel_reason'] = cancel_reason
    if receipt_id:
        payload['receipt_id'] = receipt_id
    if receipt_status:
        payload['receipt_status'] = receipt_status.value

    if not payload:
        return

    query = update(Orders).where(
        Orders.id == order_id
    ).values(payload)
    await session.execute(query)


async def create_order(
    session: AsyncSession,
    user_id: str,
    user_email: str,
    products: list[OrdersProducts],
    meta: dict | None,
) -> Order:
    new_order = Orders(
        payment_id=None,
        receipt_id=None,
        payment_status=PaymentStatus.NOT_PAYED.value,
        receipt_status=ReceiptStatus.NOT_SENT.value,
        user_id=user_id,
        user_email=user_email,
        meta=meta,
        status=OrderStatus.NEW.value
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
        user_email=user_email,
        payment_id=None,
        receipt_id=None,
        payment_status=PaymentStatus.NOT_PAYED,
        receipt_status=ReceiptStatus.NOT_SENT,
        products=products,
        meta=meta
    )


async def check_order_status(order_id: str) -> OrderStatus | None:
    query = select(Orders.status).where(Orders.id == order_id)
    async with db_session() as session:
        return (await session.execute(query)).scalar_one_or_none()


async def get_products_list() -> list[ProductsResponse]:
    query = select(Products)
    async with db_session() as session:
        result = (await session.execute(query)).scalars().all()

    return [ProductsResponse(**row.to_dict()) for row in result]


async def get_user_active_order(session: AsyncSession, user_id: int) -> list[Order]:
    query = select(Orders).where(
        and_(
            Orders.user_id == int(user_id),
            Orders.payment_status == PaymentStatus.NOT_PAYED.value,
            Orders.status == OrderStatus.NEW.value
        )
    )
    return await _get_orders(session, query)
