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

    async def _auth(self) -> None:
        assert self.is_active()
        async with self._session.post(
            'fiscalorder/v4/getToken',
            auth=BasicAuth(settings.EKASSA_LOGIN, settings.EKASSA_PASSWORD),
            json={
                'login': settings.EKASSA_LOGIN,
                'pass': settings.EKASSA_PASSWORD
            }
        ) as response:
            print("Ekass auth", await response.text(), response.status)
            if response.status != 200:
                response.raise_for_status()
            self._token = (await response.json())['token']

        self._decoded_token = jwt.decode(
            self._token,
            options={"verify_signature": False}
        )

    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> dict:
        assert self.is_active()
        if not self._is_token_alive():
            await self._auth()

        async with self._session.request(
            method=method,
            url=endpoint,
            headers={'token': self._token},
            **kwargs
        ) as response:
            print(f"Ekassa {endpoint}", await response.text(), response.status)
            if response.status != 200:
                response.raise_for_status()
            return await response.json()

    def _is_token_alive(self) -> bool:
        if not self._token:
            return False
        if self._decoded_token['exp'] <= datetime.now().timestamp():
            return False
        return True

    def is_active(self) -> bool:
        return (self._session is not None and not self._session.closed)

    @asynccontextmanager
    async def session(self, base_url: str) -> AsyncGenerator[type[Self], None]:
        async with ClientSession(base_url=base_url) as session:
            self._session = session
            yield self
            self._session = None
