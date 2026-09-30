from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb as RepositoryControlDb


class DashboardChartSettings:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await RepositoryControlDb(redis.client, session).dashboard_chart_settings.insert(data)

    async def get(self, session: AsyncSession, setting_id: int) -> dict | None:
        return await RepositoryControlDb(redis.client, session).dashboard_chart_settings.select("id", setting_id)

    async def update(self, session: AsyncSession, setting_id: int, data: dict) -> dict | None:
        return await RepositoryControlDb(redis.client, session).dashboard_chart_settings.update("id", setting_id, data)

    async def delete(self, session: AsyncSession, setting_id: int) -> dict:
        return await RepositoryControlDb(redis.client, session).dashboard_chart_settings.delete("id", setting_id)
