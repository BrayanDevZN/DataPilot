from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.service.db.repository import control_repository

from src.backend.service.task.db.dashboard_collaborations import delete_collaboration


class DashboardCollaborations:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await control_repository(session).dashboard_collaborations.insert(data)

    async def get(self, session: AsyncSession, collaboration_id: int) -> dict | None:
        return await control_repository(session).dashboard_collaborations.select("id", collaboration_id)

    async def update(self, session: AsyncSession, collaboration_id: int, data: dict) -> dict | None:
        return await control_repository(session).dashboard_collaborations.update("id", collaboration_id, data)

    async def delete(self, session: AsyncSession, collaboration_id: int) -> dict:
        result = delete_collaboration.apply_async(args=[collaboration_id], queue="database")
        return {"accepted": True, "task_id": result.id}
