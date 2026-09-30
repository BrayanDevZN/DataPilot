from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb as RepositoryControlDb


class ValidationAccount:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await RepositoryControlDb(redis.client, session).validation_account.insert(data)

    async def get(self, session: AsyncSession, identifier: str, value) -> dict | None:
        return await RepositoryControlDb(redis.client, session).validation_account.select(identifier, value)

    async def update(self, session: AsyncSession, identifier: str, value, data: dict) -> dict | None:
        return await RepositoryControlDb(redis.client, session).validation_account.update(identifier, value, data)

    async def delete(self, session: AsyncSession, identifier: str, value) -> dict:
        return await RepositoryControlDb(redis.client, session).validation_account.delete(identifier, value)
