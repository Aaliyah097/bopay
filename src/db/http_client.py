from typing import Self, AsyncGenerator
from aiohttp import ClientSession, BasicAuth
from contextlib import asynccontextmanager
from src.settings import settings


class UkassaClient:
    _session: ClientSession | None = None

    @classmethod
    async def request(
        cls,
        method: str,
        endpoint: str,
        **kwargs
    ) -> dict:
        assert cls._session is not None
        async with cls._session.request(
            method=method,
            url=endpoint,
            auth=BasicAuth(str(settings.UKASSA_SHOP_ID),
                           settings.UKASSA_API_KEY),
            ** kwargs
        ) as response:
            print(await response.text(), response.status)
            if response.status != 200:
                response.raise_for_status()
            return await response.json()

    @classmethod
    @asynccontextmanager
    async def session(cls, base_url: str) -> AsyncGenerator[type[Self], None]:
        async with ClientSession(base_url=base_url) as session:
            cls._session = session
            yield cls
            await cls._session.close()
            cls._session = None
