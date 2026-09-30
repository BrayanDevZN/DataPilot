"""Notification operations scoped to the recipient."""

from typing import Any

from sqlalchemy import update

from src.backend.logs.log import log_operation

from ..control_base import TableControl
from ..models import CollaborationNotification


class CollaborationNotificationsControl(TableControl):
    model = CollaborationNotification

    @log_operation
    async def list_by_user(self, user_id: int, *, limit: int = 30, offset: int = 0) -> dict[str, Any]:
        return await self.list(filters={"user_id": user_id}, limit=limit, offset=offset)

    @log_operation
    async def mark_read(self, notification_id: int, user_id: int) -> dict[str, Any]:
        return await self.update(notification_id, {"is_read": True}, filters={"user_id": user_id})

    @log_operation
    async def mark_all_read(self, user_id: int) -> dict[str, Any]:
        self._require_transaction()
        statement = update(self.table).where(
            self.table.c.user_id == user_id, self.table.c.is_read.is_(False),
        ).values(is_read=True).returning(self.table.c.id)
        ids = (await self.session.execute(statement)).scalars().all()
        return {"ids": ids, "count": len(ids)}
