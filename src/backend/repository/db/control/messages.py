"""Messages are appended only after locking an owned conversation."""

from typing import Any, Literal

from sqlalchemy import func, select, update

from src.backend.logs.log import log_operation

from ..control_base import RecordNotFoundError, TableControl
from ..models import Conversation, Message


class MessagesControl(TableControl):
    model = Message

    @log_operation
    async def append(self, conversation_id: int, user_id: int,
                     role: Literal["user", "assistant"], content: str) -> dict[str, Any]:
        self._require_transaction()
        if role not in ("user", "assistant") or not content.strip():
            raise ValueError("Provide a valid message role and non-empty content")
        parent = Conversation.__table__
        statement = select(parent.c.id).where(parent.c.id == conversation_id, parent.c.user_id == user_id).with_for_update()
        if (await self.session.execute(statement)).scalar_one_or_none() is None:
            raise RecordNotFoundError("Conversation not found for this user")
        result = await self.create({"conversation_id": conversation_id, "role": role, "content": content})
        await self.session.execute(update(parent).where(parent.c.id == conversation_id).values(updated_at=func.clock_timestamp()))
        return result

    @log_operation
    async def list_by_conversation(self, conversation_id: int, user_id: int,
                                   *, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        if not 1 <= limit <= 1000 or offset < 0:
            raise ValueError("Invalid pagination")
        parent = Conversation.__table__
        statement = select(self.table).join(parent, self.table.c.conversation_id == parent.c.id).where(
            parent.c.id == conversation_id, parent.c.user_id == user_id,
        ).order_by(self.table.c.id).limit(limit).offset(offset)
        rows = (await self.session.execute(statement)).mappings().all()
        return {"items": [dict(row) for row in rows], "count": len(rows)}
