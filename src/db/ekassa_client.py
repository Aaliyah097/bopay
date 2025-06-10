from typing import AsyncGenerator, Self
from aiohttp import ClientSession, BasicAuth
from contextlib import asynccontextmanager
import jwt
from datetime import datetime
from src.settings import settings


class EkassaClient:
    _session: ClientSession | None = None
    _token: str | None = None
    _decoded_token: str | None = None

    @classmethod
    async def _auth(cls) -> None:
        assert cls.is_active()
        async with cls._session.post(
            'fiscalorder/v4/getToken',
            auth=BasicAuth(settings.EKASSA_LOGIN, settings.EKASSA_PASSWORD),
            json={
                'login': settings.EKASSA_LOGIN,
                'pass': settings.EKASSA_PASSWORD
            }
        ) as response:
            print(await response.text(), response.status)
            if response.status != 200:
                response.raise_for_status()
            cls._token = (await response.json())['token']

        cls._decoded_token = jwt.decode(
            cls._token,
            options={"verify_signature": False}
        )

    @classmethod
    async def request(
        cls,
        method: str,
        endpoint: str,
        **kwargs
    ) -> dict:
        assert cls.is_active()
        if not cls._is_token_alive():
            await cls._auth()

        async with cls._session.request(
            method=method,
            url=endpoint,
            headers={'token': cls._token},
            **kwargs
        ) as response:
            print(await response.text(), response.status)
            if response.status != 200:
                response.raise_for_status()
            return await response.json()

    @classmethod
    def _is_token_alive(cls) -> bool:
        if not cls._token:
            return False
        if cls._decoded_token['exp'] <= datetime.now().timestamp():
            return False
        return True

    @classmethod
    def is_active(cls) -> bool:
        return (cls._session is not None and not cls._session.closed)

    @classmethod
    @asynccontextmanager
    async def session(cls, base_url: str) -> AsyncGenerator[type[Self], None]:
        async with ClientSession(base_url=base_url) as session:
            cls._session = session
            yield cls
            await cls._session.close()
            cls._session = None
