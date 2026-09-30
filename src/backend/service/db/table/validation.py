from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb


async def create(session: AsyncSession, data: dict) -> dict:
    return await ControlDb(redis.client, session).validation.insert(data)


async def get(session: AsyncSession, identifier: str, value) -> dict | None:
    return await ControlDb(redis.client, session).validation.select(identifier, value)


async def update(session: AsyncSession, identifier: str, value, data: dict) -> dict | None:
    return await ControlDb(redis.client, session).validation.update(identifier, value, data)


async def delete(session: AsyncSession, identifier: str, value) -> dict:
    return await ControlDb(redis.client, session).validation.delete(identifier, value)


class Validation:
    create = staticmethod(create)
    get = staticmethod(get)
    update = staticmethod(update)
    delete = staticmethod(delete)
