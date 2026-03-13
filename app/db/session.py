from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.db.url import normalize_asyncpg_database_url


def create_engine(settings: Settings) -> AsyncEngine:
    """Create the SQLAlchemy async engine.

    Notes:
      - Neon commonly uses `?sslmode=require`. asyncpg does not support `sslmode` kwarg,
        so we normalize the URL and pass SSL via SQLAlchemy connect_args instead.
    """
    normalized = normalize_asyncpg_database_url(settings.database_url)

    return create_async_engine(
        normalized.sqlalchemy_url,
        pool_pre_ping=True,
        connect_args=normalized.connect_args,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


# PUBLIC_INTERFACE
async def get_db_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an AsyncSession.

    Contract:
      - Yields a single session per request.
      - Always closes session.

    Args:
      session_factory: async_sessionmaker configured at app startup.

    Yields:
      AsyncSession: Database session for the request.
    """
    async with session_factory() as session:
        yield session
