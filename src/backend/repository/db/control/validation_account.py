"""Account verification codes: serialized issuance and atomic one-time consumption."""

from datetime import timedelta
from typing import Any

from sqlalchemy import delete, func, select, update

from src.backend.logs.log import log_operation

from ..control_base import TableControl
from ..models import ValidationAccount


class ValidationAccountControl(TableControl):
    model = ValidationAccount

    @log_operation
    async def _lock_email(self, email: str) -> None:
        self._require_transaction()
        await self.session.execute(select(func.pg_advisory_xact_lock(func.hashtextextended("validation_account:" + email, 0))))

    @log_operation
    async def issue(self, email: str, number: str) -> dict[str, Any]:
        email = email.strip().lower()
        if len(number) != 6 or not number.isascii() or not number.isdigit():
            raise ValueError("Verification code must contain six digits")
        await self._lock_email(email)
        # Keep only the current code. Serializing by email also covers an absent row.
        await self.session.execute(delete(self.table).where(self.table.c.email == email))
        return await self.create({"email": email, "number": number})

    @log_operation
    async def consume(self, email: str, number: str, *, max_age: timedelta = timedelta(minutes=10)) -> dict[str, Any]:
        email = email.strip().lower()
        if max_age.total_seconds() <= 0:
            raise ValueError("Code lifetime must be positive")
        await self._lock_email(email)
        latest = select(self.primary_key).where(self.table.c.email == email).order_by(
            self.table.c.created_at.desc(), self.primary_key.desc(),
        ).limit(1).scalar_subquery()
        statement = update(self.table).where(
            self.primary_key == latest, self.table.c.number == number,
            self.table.c.used.is_(False), self.table.c.created_at >= func.clock_timestamp() - max_age,
            self.table.c.created_at <= func.clock_timestamp(),
        ).values(used=True).returning(*self.table.c)
        row = (await self.session.execute(statement)).mappings().one_or_none()
        return {"consumed": row is not None, "item": dict(row) if row is not None else None}
