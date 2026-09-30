from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb


async def create(session: AsyncSession, data: dict) -> dict:
    return await ControlDb(redis.client, session).messages.insert(data)


async def get(session: AsyncSession, message_id: int) -> dict | None:
    return await ControlDb(redis.client, session).messages.select("id", message_id)


async def update(session: AsyncSession, message_id: int, data: dict) -> dict | None:
    return await ControlDb(redis.client, session).messages.update("id", message_id, data)


async def delete(session: AsyncSession, message_id: int) -> dict:
    return await ControlDb(redis.client, session).messages.delete("id", message_id)
