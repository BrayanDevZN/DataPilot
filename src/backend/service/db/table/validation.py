from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.service.db.repository import control_repository



class Validation:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await control_repository(session).validation.insert(data)

    async def get(self, session: AsyncSession, identifier: str, value) -> dict | None:
        return await control_repository(session).validation.select(identifier, value)

    async def update(self, session: AsyncSession, identifier: str, value, data: dict) -> dict | None:
        return await control_repository(session).validation.update(identifier, value, data)

    async def delete(self, session: AsyncSession, identifier: str, value) -> dict:
        return await control_repository(session).validation.delete(identifier, value)
