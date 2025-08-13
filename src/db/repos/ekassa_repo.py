from datetime import datetime
from src.models.product import OrderProduct
from src.db.ekassa_client import EkassaClient
from src.settings import settings


async def send_receipt(
    client: EkassaClient,
    order_id: str,
    email: str,
    products: list[OrderProduct],
) -> str:
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
                "payment_address": settings.COMPANY_WEBSITE_URL,
                "sno": "usn_income"
            },
            "items": [
                {
                    "name": product.name,
                    "price": product.price,
                    "quantity": product.quantity,
                    "sum": product.sum_,
                    'measure': 0,
                    "payment_object": 4,
                    "vat": {
                        "type": 'none'
                    },
                    "payment_method": 'full_payment'
                } for product in products
            ],
            "payments": [
                {
                    'type': 1,
                    'sum': total_cost
                }
            ],
            "vats": [],
            "total": total_cost
        },
        "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
    }

    response = await client.request(
        'POST',
        f'fiscalorder/v5/{settings.EKASSA_GROUP_CODE}/sell',
        json=payload
    )

    return str(response['uuid'])


async def check_receipt_status(
    client: EkassaClient,
    receipt_id: str
) -> int:
    response = await client.request(
        'GET',
        f'/fiscalorder/v4/{settings.EKASSA_GROUP_CODE}/report/{receipt_id}'
    )
    status = response['status']

    match status:
        case 'done':
            return 1
        case 'fail':
            print(f"Отправка чека не удалась на стороне провайдера", response)
            return -1
        case 'wait':
            return 0
        case _:
            print(f"Неизвестный статус чека: {status}")
            return 0
