import asyncio
from src.settings import settings
from src.db.pg_client import db_session
from src.db.ekassa_client import EkassaClient
from src.repository import check_receipt_status, get_orders_with_sent_checks, update_order
import logging
from src.models.order import ReceiptStatus


semaphore = asyncio.Semaphore(15)
logger = logging.getLogger(__name__)


async def _with_semaphore_check_receipt(
    client: EkassaClient,
    receipt_id: int
) -> int | None:
    if not receipt_id:
        return None
    async with semaphore:
        try:
            return await check_receipt_status(
                client,
                receipt_id=receipt_id
            )
        except Exception as exc:
            logger.error(exc)
    return None


async def finish_orders():
    async with db_session() as session:
        check_sent_orders = await get_orders_with_sent_checks(session)

    async with EkassaClient().session(settings.EKASSA_BASE_URL) as client:
        checks_statuses = await asyncio.gather(
            *[
                _with_semaphore_check_receipt(client, order.receipt_id)
                for order in check_sent_orders
            ],
            return_exceptions=True
        )
        assert len(check_sent_orders) == len(checks_statuses)

    async with db_session() as session:
        for order, check_status in zip(check_sent_orders, checks_statuses):
            if not check_status or isinstance(check_status, (Exception, BaseException)):
                continue
            await update_order(session, order.id, receipt_status=ReceiptStatus.DELIVERED)


async def main():
    while True:
        await finish_orders()
        await asyncio.sleep(settings.PAYMENT_MONITORING_INTERVAL_SEC)
