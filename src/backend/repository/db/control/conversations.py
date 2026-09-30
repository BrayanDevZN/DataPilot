"""Database operations for conversations, scoped to their owner."""

from typing import Any

from src.backend.logs.log import log_operation

from ..control_base import transactional, TableControl
from ..models import Conversation


class ConversationsControl(TableControl):
    model = Conversation

    @log_operation
    @transactional
    async def list_by_user(self, user_id: int, *, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return await self.list(filters={"user_id": user_id}, limit=limit, offset=offset)

    @log_operation
    @transactional
    async def get_owned(self, conversation_id: int, user_id: int, *, for_update: bool = False) -> dict[str, Any]:
        return await self.get(conversation_id, filters={"user_id": user_id}, for_update=for_update)

    @log_operation
    @transactional
    async def delete_owned(self, conversation_id: int, user_id: int) -> dict[str, Any]:
        return await self.delete(conversation_id, filters={"user_id": user_id})
