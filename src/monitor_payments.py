import asyncio
from src.repository import check_payment_status, update_order, get_unpaid_orders
from src.db.pg_client import db_session
from src.models.payment import PaymentStatus
from src.settings import settings
from asyncio import Semaphore
from src.db.ukassa_client import UkassaClient


semaphore = Semaphore(15)


async def _with_semaphore_check_payment_status(client: UkassaClient, payment_id: str | None) -> PaymentStatus | None:
    if not payment_id:
        return None
    async with semaphore:
        return await check_payment_status(client, payment_id)


async def manage_orders():
    async with db_session() as session:
        unpaid_orders = await get_unpaid_orders(session)

    async with UkassaClient().session(settings.UKASSA_BASE_URL) as client:
        payment_statuses = await asyncio.gather(
            *[
                _with_semaphore_check_payment_status(client, order.payment_id)
                for order in unpaid_orders
            ]
        )
    assert len(unpaid_orders) == len(payment_statuses)

    async with db_session() as session:
        for order, payment_status in zip(unpaid_orders, payment_statuses):
            if not payment_status:
                continue
            if payment_status == order.payment_status:
                continue
            await update_order(session, order.id, payment_status=payment_status)


async def main():
    while True:
        await manage_orders()
        await asyncio.sleep(settings.PAYMENT_MONITORING_INTERVAL_SEC)


if __name__ == '__main__':
    asyncio.run(main())
