"""Database operations for users; uniqueness is enforced by PostgreSQL indexes."""

from typing import Any

from sqlalchemy import func, select

from src.backend.logs.log import log_operation

from ..control_base import transactional, TableControl
from ..models import User


class UsersControl(TableControl):
    model = User

    @log_operation
    @transactional
    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        values = dict(data)
        for field in ("email", "username"):
            if field in values:
                values[field] = values[field].strip().lower()
        return await super().create(values)

    @log_operation
    @transactional
    async def update(self, record_id: int, data: dict[str, Any], *,
                     filters: dict[str, Any] | None = None,
                     expected: dict[str, Any] | None = None) -> dict[str, Any]:
        values = dict(data)
        for field in ("email", "username"):
            if field in values:
                values[field] = values[field].strip().lower()
        return await super().update(record_id, values, filters=filters, expected=expected)

    @log_operation
    @transactional
    async def get_by_email(self, email: str) -> dict[str, Any]:
        statement = select(self.table).where(func.lower(self.table.c.email) == email.strip().lower())
        row = (await self.session.execute(statement)).mappings().one_or_none()
        return {"found": row is not None, "item": dict(row) if row is not None else None}

    @log_operation
    @transactional
    async def get_by_username(self, username: str) -> dict[str, Any]:
        statement = select(self.table).where(func.lower(self.table.c.username) == username.strip().lower())
        row = (await self.session.execute(statement)).mappings().one_or_none()
        return {"found": row is not None, "item": dict(row) if row is not None else None}
