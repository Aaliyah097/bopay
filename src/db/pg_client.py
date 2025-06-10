from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    create_async_engine)
from sqlalchemy.orm import sessionmaker

from src.settings import settings

pg_engine: AsyncEngine = create_async_engine(
    settings.async_pg_conn_string, echo=False)
session_maker = sessionmaker(
    pg_engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            raise exc
