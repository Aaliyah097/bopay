import asyncio
from src.repository import check_payment_status, update_order, get_unpaid_orders
from src.db.pg_client import db_session
from src.models.payment import PaymentStatus
from src.settings import settings


async def manage_orders():
    to_update: list[tuple[str, PaymentStatus]] = []
    async with db_session() as session:
        unpaid_orders = await get_unpaid_orders(session)

    for order in unpaid_orders:
        if not order.payment_id:
            continue
        try:
            payment_status = await check_payment_status(order.payment_id)
        except Exception as e:
            print(str(e))
            continue
        if payment_status != order.payment_status:
            to_update.append((order.id, payment_status))

    if not to_update:
        return

    async with db_session() as session:
        for order_id, payment_status in to_update:
            await update_order(session, order_id, payment_status=payment_status)


async def main():
    while True:
        await manage_orders()
        await asyncio.sleep(settings.PAYMENT_MONITORING_INTERVAL_SEC)


if __name__ == '__main__':
    asyncio.run(main())
