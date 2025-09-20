from httpx import AsyncClient
from src.settings import settings


class AuthRepo:
    @staticmethod
    async def login(username: str, password: str) -> tuple[str, str]:
        async with AsyncClient(
            base_url=settings.CREATE_TOKEN_URI
        ) as session:
            response = await session.post(
                '/',
                data={
                    'login_tg': username,
                    'password': password
                }
            )
            if not response.status_code == 200:
                response.raise_for_status()

            data = response.json()
            return (
                data['access'],
                data['refresh']
            )

    @staticmethod
    async def verify(token: str) -> bool:
        async with AsyncClient(
            base_url=settings.VERIFY_TOKEN_URI
        ) as session:
            response = await session.post(
                '/',
                data={
                    'token': token
                }
            )
            if response.status_code != 200:
                return False
        return True
