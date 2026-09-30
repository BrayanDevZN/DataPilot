from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb as RepositoryControlDb


class DashboardCharts:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await RepositoryControlDb(redis.client, session).dashboard_charts.insert(data)

    async def get(self, session: AsyncSession, chart_id: int) -> dict | None:
        return await RepositoryControlDb(redis.client, session).dashboard_charts.select("id", chart_id)

    async def update(self, session: AsyncSession, chart_id: int, data: dict) -> dict | None:
        return await RepositoryControlDb(redis.client, session).dashboard_charts.update("id", chart_id, data)

    async def delete(self, session: AsyncSession, chart_id: int) -> dict:
        return await RepositoryControlDb(redis.client, session).dashboard_charts.delete("id", chart_id)
