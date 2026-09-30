from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb as RepositoryControlDb
from src.backend.service.task.db.dashboards import delete_dashboard


class Dashboards:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await RepositoryControlDb(redis.client, session).dashboards.insert(data)

    async def get(self, session: AsyncSession, dashboard_id: int) -> dict | None:
        return await RepositoryControlDb(redis.client, session).dashboards.select("id", dashboard_id)

    async def update(self, session: AsyncSession, dashboard_id: int, data: dict) -> dict | None:
        return await RepositoryControlDb(redis.client, session).dashboards.update("id", dashboard_id, data)

    async def delete(self, session: AsyncSession, dashboard_id: int) -> dict:
        result = delete_dashboard.apply_async(args=[dashboard_id], queue="database")
        return {"accepted": True, "task_id": result.id}
