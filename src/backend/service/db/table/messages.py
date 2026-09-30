from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb as RepositoryControlDb


class Messages:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await RepositoryControlDb(redis.client, session).messages.insert(data)

    async def get(self, session: AsyncSession, message_id: int) -> dict | None:
        return await RepositoryControlDb(redis.client, session).messages.select("id", message_id)

    async def update(self, session: AsyncSession, message_id: int, data: dict) -> dict | None:
        return await RepositoryControlDb(redis.client, session).messages.update("id", message_id, data)

    async def delete(self, session: AsyncSession, message_id: int) -> dict:
        return await RepositoryControlDb(redis.client, session).messages.delete("id", message_id)
