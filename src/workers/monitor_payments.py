from datetime import datetime
import asyncio
from src.repository import (
    check_payment_status,
    update_order,
    get_unpaid_orders,
    cancel_payment,
)
from src.db.pg_client import db_session
from src.models.order import OrderStatus
from src.models.payment import PaymentStatus
from src.settings import settings
from src.db.ukassa_client import UkassaClient
import logging


semaphore = asyncio.Semaphore(15)
logger = logging.getLogger(__name__)


async def _with_semaphore_check_payment_status(client: UkassaClient, payment_id: str | None) -> PaymentStatus | None:
    if not payment_id:
        return None
    async with semaphore:
        try:
            return await check_payment_status(client, payment_id)
        except Exception as exc:
            logger.error(exc)
    return None


async def manage_orders():
    async with db_session() as session:
        unpaid_orders = await get_unpaid_orders(session)

    async with UkassaClient().session(settings.UKASSA_BASE_URL) as client:
        payment_statuses = await asyncio.gather(
            *[
                _with_semaphore_check_payment_status(client, order.payment_id)
                for order in unpaid_orders
            ],
            return_exceptions=True
        )
        assert len(unpaid_orders) == len(payment_statuses)

        now = datetime.now()
        async with db_session() as session:
            for order, payment_status in zip(unpaid_orders, payment_statuses):
                if payment_status is None or isinstance(payment_status, (Exception, BaseException)):
                    continue
                if (
                    payment_status in [PaymentStatus.WAITING_FOR_CAPTURE, PaymentStatus.NOT_PAYED] and
                    (now - order.created_at).total_seconds() > settings.PAYING_TIME_LIMIT_SEC
                ):
                    if payment_status == PaymentStatus.WAITING_FOR_CAPTURE:
                        try:
                            await cancel_payment(client, order.payment_id, order.id)
                        except Exception as exc:
                            logger.error(exc)
                            continue
                    await update_order(
                        session,
                        order.id,
                        order_status=OrderStatus.TO_DESTROY,
                        cancel_reason='Истекло время на оплату',
                        payment_status=payment_status
                    )
                    continue
                if str(payment_status) == str(order.payment_status):
                    continue
                if payment_status == PaymentStatus.WAITING_FOR_CAPTURE:
                    await update_order(
                        session,
                        order.id,
                        payment_status=payment_status
                    )
                if payment_status == PaymentStatus.CANCELED:
                    await update_order(
                        session,
                        order.id,
                        order_status=OrderStatus.TO_DESTROY,
                        payment_status=payment_status
                    )
                else:
                    await update_order(session, order.id, payment_status=payment_status)

    # https://yookassa.ru/developers/api#capture_payment
    # https://yookassa.ru/developers/api#cancel_payment
    # https://ecomkassa.ru/dokumentacija_cheki_12


async def main():
    while True:
        await manage_orders()
        await asyncio.sleep(settings.PAYMENT_MONITORING_INTERVAL_SEC)


if __name__ == '__main__':
    asyncio.run(main())
