from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.service.db.repository import control_repository



class Messages:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await control_repository(session).messages.insert(data)

    async def get(self, session: AsyncSession, message_id: int) -> dict | None:
        return await control_repository(session).messages.select("id", message_id)

    async def update(self, session: AsyncSession, message_id: int, data: dict) -> dict | None:
        return await control_repository(session).messages.update("id", message_id, data)

    async def delete(self, session: AsyncSession, message_id: int) -> dict:
        return await control_repository(session).messages.delete("id", message_id)
