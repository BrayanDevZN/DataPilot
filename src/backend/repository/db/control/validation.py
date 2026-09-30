"""Password verification codes scoped and serialized by their user."""

from datetime import timedelta
from typing import Any

from sqlalchemy import delete, func, select

from src.backend.logs.log import log_operation

from ..control_base import RecordNotFoundError, TableControl
from ..models import User, Validation


class ValidationControl(TableControl):
    model = Validation

    @log_operation
    async def _lock_user(self, user_id: int) -> None:
        self._require_transaction()
        statement = select(User.user_id).where(User.user_id == user_id).with_for_update()
        if (await self.session.execute(statement)).scalar_one_or_none() is None:
            raise RecordNotFoundError("User not found")

    @log_operation
    async def issue(self, user_id: int, number: str) -> dict[str, Any]:
        if len(number) != 6 or not number.isascii() or not number.isdigit():
            raise ValueError("Verification code must contain six digits")
        await self._lock_user(user_id)
        await self.session.execute(delete(self.table).where(self.table.c.user_id == user_id))
        return await self.create({"user_id": user_id, "number": number})

    @log_operation
    async def consume(self, user_id: int, number: str, *, max_age: timedelta = timedelta(minutes=10)) -> dict[str, Any]:
        if max_age.total_seconds() <= 0:
            raise ValueError("Code lifetime must be positive")
        await self._lock_user(user_id)
        latest = select(self.primary_key).where(self.table.c.user_id == user_id).order_by(
            self.table.c.created_at.desc(), self.primary_key.desc(),
        ).limit(1).scalar_subquery()
        statement = delete(self.table).where(
            self.primary_key == latest, self.table.c.number == number,
            self.table.c.created_at >= func.clock_timestamp() - max_age,
            self.table.c.created_at <= func.clock_timestamp(),
        ).returning(*self.table.c)
        row = (await self.session.execute(statement)).mappings().one_or_none()
        return {"consumed": row is not None, "item": dict(row) if row is not None else None}
