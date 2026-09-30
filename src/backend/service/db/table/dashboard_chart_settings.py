from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.service.db.repository import control_repository



class DashboardChartSettings:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await control_repository(session).dashboard_chart_settings.insert(data)

    async def get(self, session: AsyncSession, setting_id: int) -> dict | None:
        return await control_repository(session).dashboard_chart_settings.select("id", setting_id)

    async def update(self, session: AsyncSession, setting_id: int, data: dict) -> dict | None:
        return await control_repository(session).dashboard_chart_settings.update("id", setting_id, data)

    async def delete(self, session: AsyncSession, setting_id: int) -> dict:
        return await control_repository(session).dashboard_chart_settings.delete("id", setting_id)
