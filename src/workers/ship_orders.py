import asyncio
from src.settings import settings
from src.db.repos.db_repo import get_paid_orders, update_order
from src.db.pg_client import db_session
from src.db.repos.backend_repo import unlock_candidate
from aiohttp import ClientSession
from src.models.order import OrderStatus
from src.db.ukassa_client import UkassaClient
from src.repository import (
    cancel_payment,
    accept_payment,
)
import logging


semaphore = asyncio.Semaphore(5)
logger = logging.getLogger(__name__)


async def _with_semaphore_unlock_candidate(
    session: ClientSession,
    candidate_id: int | str
) -> int:
    async with semaphore:
        try:
            await unlock_candidate(session, candidate_id)
            return 1
        except Exception as exc:
            logger.error(exc)
    return 0


async def manage_orders():
    async with db_session() as session:
        paid_orders = await get_paid_orders(session)

    async with ClientSession() as session:
        unlock_statuses = await asyncio.gather(
            *[
                _with_semaphore_unlock_candidate(
                    session, order.meta['candidate_id'])
                for order in paid_orders if (order.meta and 'candidate_id' in order.meta)
            ],
            return_exceptions=True
        )

    async with UkassaClient().session(settings.UKASSA_BASE_URL) as client:
        async with db_session() as session:
            for order, unlock_status in zip(paid_orders, unlock_statuses):
                try:
                    if not unlock_status or isinstance(unlock_status, (Exception, BaseException)):
                        await cancel_payment(client, order.payment_id, order.id)
                        await update_order(session, order.id, order_status=OrderStatus.TO_DESTROY, cancel_reason='Не удалось разблокировать кандидата')
                    else:
                        await accept_payment(client, order.payment_id, order.id, order.sum_)
                        await update_order(session, order.id, order_status=OrderStatus.SHIPPPED)
                except Exception as exc:
                    logger.error(exc)


async def main():
    while True:
        await manage_orders()
        await asyncio.sleep(settings.PAYMENT_MONITORING_INTERVAL_SEC)


if __name__ == '__main__':
    asyncio.run(main())
