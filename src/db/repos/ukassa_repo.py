from src.models.payment import Payment, PaymentStatus
from src.db.ukassa_client import UkassaClient
from src.settings import settings


def repeat_payment_link(payment_id: str) -> str | None:
    if not payment_id:
        return None
    return f"https://yoomoney.ru/checkout/payments/v2/contract?orderId={payment_id}"


async def create_payment_link(
    amount: int,
    order_id: str,
    success_redirect_url: str
) -> Payment:
    async with UkassaClient().session(settings.UKASSA_BASE_URL) as client:
        response = await client.request(
            'POST',
            f'payments',
            json={
                "amount": {
                    "value": amount,
                    "currency": "RUB"
                },
                "capture": False,
                "confirmation": {
                    "type": "redirect",
                    "return_url": success_redirect_url or settings.COMPANY_WEBSITE_URL
                },
                "description": f"Заказ №{order_id}"
            },
            headers={
                'Idempotence-Key': str(order_id),
                'Content-Type': 'application/json'
            },
        )
    
    return Payment(
        id=response['id'],
        link=response['confirmation']['confirmation_url']
    )


async def cancel_payment(client: UkassaClient, payment_id: str, order_id: str):
    await client.request(
        'POST',
        f'payments/{str(payment_id)}/cancel',
        headers={
            'Idempotence-Key': str(order_id),
            'Content-Type': 'application/json'
        },
    )


async def accept_payment(client: UkassaClient, payment_id: str, order_id: str, amount: int):
    await client.request(
        'POST',
        f'payments/{str(payment_id)}/capture',
        headers={
            'Idempotence-Key': str(order_id),
            'Content-Type': 'application/json'
        },
        json={
            "amount": {
                "value": amount,
                "currency": "RUB"
            }
        }
    )


async def check_payment_status(client: UkassaClient, payment_id: str) -> PaymentStatus:
    assert payment_id
    # async with UkassaClient().session(settings.UKASSA_BASE_URL) as session:
    response = await client.request(
        'GET',
        f'payments/{str(payment_id)}',
    )
    status = response['status']

    match status:
        case 'pending':
            return PaymentStatus.NOT_PAYED
        case 'waiting_for_capture':
            return PaymentStatus.WAITING_FOR_CAPTURE
        case 'succeeded':
            return PaymentStatus.PAYED
        case 'canceled':
            return PaymentStatus.CANCELED
        case _:
            print(f"Неизвестный статус чека: {status}")
            return PaymentStatus.NOT_PAYED
