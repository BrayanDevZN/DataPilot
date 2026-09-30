from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb
from src.backend.service.task.db.data_sources import delete_data_source


async def create(session: AsyncSession, data: dict) -> dict:
    return await ControlDb(redis.client, session).data_sources.insert(data)


async def get(session: AsyncSession, data_source_id: int) -> dict | None:
    return await ControlDb(redis.client, session).data_sources.select("id", data_source_id)


async def update(session: AsyncSession, data_source_id: int, data: dict) -> dict | None:
    return await ControlDb(redis.client, session).data_sources.update("id", data_source_id, data)


async def delete(session: AsyncSession, data_source_id: int) -> dict:
    result = delete_data_source.apply_async(args=[data_source_id], queue="database")
    return {"accepted": True, "task_id": result.id}
