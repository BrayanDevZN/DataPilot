from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb


async def create(session: AsyncSession, data: dict) -> dict:
    return await ControlDb(redis.client, session).dashboard_chart_settings.insert(data)


async def get(session: AsyncSession, setting_id: int) -> dict | None:
    return await ControlDb(redis.client, session).dashboard_chart_settings.select("id", setting_id)


async def update(session: AsyncSession, setting_id: int, data: dict) -> dict | None:
    return await ControlDb(redis.client, session).dashboard_chart_settings.update("id", setting_id, data)


async def delete(session: AsyncSession, setting_id: int) -> dict:
    return await ControlDb(redis.client, session).dashboard_chart_settings.delete("id", setting_id)
