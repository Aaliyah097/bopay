import asyncio
from src.settings import settings
from src.db.repos.db_repo import get_to_destroy_orders, update_order
from src.db.pg_client import db_session
from src.db.repos.backend_repo import destroy_candidate
from aiohttp import ClientSession
from src.models.order import OrderStatus
import logging


semaphore = asyncio.Semaphore(5)
logger = logging.getLogger(__name__)


async def _with_semaphore_destroy_candidate(
    session: ClientSession,
    candidate_id: int | str
) -> int:
    async with semaphore:
        try:
            await destroy_candidate(session, candidate_id)
            return 1
        except Exception as exc:
            logger.error(exc)
    return 0


async def manage_orders():
    async with db_session() as session:
        to_destroy_orders = await get_to_destroy_orders(session)

    async with ClientSession() as session:
        destroy_statuses = await asyncio.gather(
            *[
                _with_semaphore_destroy_candidate(
                    session, order.meta['candidate_id'])
                for order in to_destroy_orders if (order.meta and 'candidate_id' in order.meta)
            ],
            return_exceptions=True
        )

    async with db_session() as session:
        for order, destroy_status in zip(to_destroy_orders, destroy_statuses):
            try:
                if not destroy_status or isinstance(destroy_status, (Exception, BaseException)):
                    continue
                await update_order(session, order.id, order_status=OrderStatus.CANCELED)
            except Exception as exc:
                logger.error(exc)


async def main():
    while True:
        await manage_orders()
        await asyncio.sleep(settings.PAYMENT_MONITORING_INTERVAL_SEC)


if __name__ == '__main__':
    asyncio.run(main())
