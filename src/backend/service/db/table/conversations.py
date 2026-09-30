from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.service.db.repository import control_repository

from src.backend.service.task.db.conversations import delete_conversation


class Conversations:
    async def create(self, session: AsyncSession, data: dict) -> dict:
        return await control_repository(session).conversations.insert(data)

    async def get(self, session: AsyncSession, conversation_id: int) -> dict | None:
        return await control_repository(session).conversations.select("id", conversation_id)

    async def update(self, session: AsyncSession, conversation_id: int, data: dict) -> dict | None:
        return await control_repository(session).conversations.update("id", conversation_id, data)

    async def delete(self, session: AsyncSession, conversation_id: int) -> dict:
        result = delete_conversation.apply_async(args=[conversation_id], queue="database")
        return {"accepted": True, "task_id": result.id}
