from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb
from src.backend.service.task.db.dashboard_collaborations import delete_collaboration


async def create(session: AsyncSession, data: dict) -> dict:
    return await ControlDb(redis.client, session).dashboard_collaborations.insert(data)


async def get(session: AsyncSession, collaboration_id: int) -> dict | None:
    return await ControlDb(redis.client, session).dashboard_collaborations.select("id", collaboration_id)


async def update(session: AsyncSession, collaboration_id: int, data: dict) -> dict | None:
    return await ControlDb(redis.client, session).dashboard_collaborations.update("id", collaboration_id, data)


async def delete(session: AsyncSession, collaboration_id: int) -> dict:
    result = delete_collaboration.apply_async(args=[collaboration_id], queue="database")
    return {"accepted": True, "task_id": result.id}
