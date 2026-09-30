from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb as RepositoryControlDb
from src.backend.service.task.db.conversations import delete_conversation


class Conversations:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await RepositoryControlDb(redis.client, session).conversations.insert(data)

    async def get(self, session: AsyncSession, conversation_id: int) -> dict | None:
        return await RepositoryControlDb(redis.client, session).conversations.select("id", conversation_id)

    async def update(self, session: AsyncSession, conversation_id: int, data: dict) -> dict | None:
        return await RepositoryControlDb(redis.client, session).conversations.update("id", conversation_id, data)

    async def delete(self, session: AsyncSession, conversation_id: int) -> dict:
        result = delete_conversation.apply_async(args=[conversation_id], queue="database")
        return {"accepted": True, "task_id": result.id}
