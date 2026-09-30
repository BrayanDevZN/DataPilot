from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb
from src.backend.service.task.db.collaboration_notifications import create_notification


async def create(session: AsyncSession, data: dict) -> dict:
    result = create_notification.apply_async(args=[data], queue="database")
    return {"accepted": True, "task_id": result.id}


async def get(session: AsyncSession, notification_id: int) -> dict | None:
    return await ControlDb(redis.client, session).collaboration_notifications.select("id", notification_id)


async def update(session: AsyncSession, notification_id: int, data: dict) -> dict | None:
    return await ControlDb(redis.client, session).collaboration_notifications.update("id", notification_id, data)


async def delete(session: AsyncSession, notification_id: int) -> dict:
    return await ControlDb(redis.client, session).collaboration_notifications.delete("id", notification_id)
