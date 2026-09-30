from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb


async def create(session: AsyncSession, data: dict) -> dict:
    return await ControlDb(redis.client, session).dashboard_charts.insert(data)


async def get(session: AsyncSession, chart_id: int) -> dict | None:
    return await ControlDb(redis.client, session).dashboard_charts.select("id", chart_id)


async def update(session: AsyncSession, chart_id: int, data: dict) -> dict | None:
    return await ControlDb(redis.client, session).dashboard_charts.update("id", chart_id, data)


async def delete(session: AsyncSession, chart_id: int) -> dict:
    return await ControlDb(redis.client, session).dashboard_charts.delete("id", chart_id)
