import asyncio
from src.settings import settings
from src.db.pg_client import db_session
from src.repository import get_shipped_orders, send_receipt, update_order
from src.db.ekassa_client import EkassaClient
from src.models.order import Order, OrderStatus, ReceiptStatus
import logging


semaphore = asyncio.Semaphore(15)
logger = logging.getLogger(__name__)


async def _with_semaphore_send_receipt(
    client: EkassaClient,
    order: Order
) -> str | None:
    if not order.id:
        return
    async with semaphore:
        try:
            return await send_receipt(
                client,
                order.id,
                order.user_email,
                order.products
            )
        except Exception as exc:
            logger.error(exc)
    return None


async def manage_orders():
    async with db_session() as session:
        shipped_orders = await get_shipped_orders(session)

    async with EkassaClient().session(settings.EKASSA_BASE_URL) as client:
        receipts_ids = await asyncio.gather(
            *[
                _with_semaphore_send_receipt(client, order)
                for order in shipped_orders
            ],
            return_exceptions=True
        )
        assert len(shipped_orders) == len(receipts_ids)

    async with db_session() as session:
        for order, receipt_id in zip(shipped_orders, receipts_ids):
            if not receipt_id or isinstance(receipt_id, (Exception, BaseException)):
                continue
            await update_order(session, order.id, receipt_id=receipt_id, receipt_status=ReceiptStatus.SENT)


async def main():
    while True:
        await manage_orders()
        await asyncio.sleep(settings.PAYMENT_MONITORING_INTERVAL_SEC)
