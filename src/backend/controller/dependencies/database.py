"""Database session dependency for HTTP handlers."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import database


async def get_session() -> AsyncIterator[AsyncSession]:
    async with database.session_factory() as session:
        yield session
