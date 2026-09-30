from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb as RepositoryControlDb
from src.backend.service.task.db.users import delete_user


class Users:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await RepositoryControlDb(redis.client, session).users.insert(data)

    async def get(self, session: AsyncSession, identifier: str, value) -> dict | None:
        return await RepositoryControlDb(redis.client, session).users.select(identifier, value)

    async def update(self, session: AsyncSession, identifier: str, value, data: dict) -> dict | None:
        return await RepositoryControlDb(redis.client, session).users.update(identifier, value, data)

    async def delete(self, session: AsyncSession, user_id: int) -> dict:
        result = delete_user.apply_async(args=[user_id], queue="database")
        return {"accepted": True, "task_id": result.id}
