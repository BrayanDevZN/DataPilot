"""Shared database operations with context-managed AsyncSession transactions."""

from functools import wraps
from typing import Any, Callable

from sqlalchemy import Table, delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import SessionTransactionOrigin

from src.backend.logs.log import logger, log_operation

from .base import Base
from .models import Dashboard


class TransactionRequiredError(RuntimeError):
    """An implicit transaction must be finished before calling a control."""


class RecordNotFoundError(LookupError):
    """The requested record does not match the supplied scope."""


def transactional(function: Callable[..., Any]) -> Callable[..., Any]:
    """Open a context-managed transaction or join an explicit caller transaction."""
    @wraps(function)
    async def wrapper(self, *args, **kwargs):
        transaction = self.session.get_transaction()
        if transaction is not None:
            if transaction.sync_transaction.origin is not SessionTransactionOrigin.BEGIN:
                raise TransactionRequiredError("Finish the implicit transaction before using a control")
            return await function(self, *args, **kwargs)
        async with self.session.begin():
            return await function(self, *args, **kwargs)
    return wrapper


class TableControl:
    model: type[Base]

    @log_operation
    def __init__(self, session: AsyncSession) -> None:
        if not isinstance(session, AsyncSession):
            raise TypeError("Control requires a SQLAlchemy AsyncSession")
        self.session = session
        self.table: Table = self.model.__table__
        self.primary_key = next(iter(self.table.primary_key.columns))

    @log_operation
    def _require_transaction(self) -> None:
        transaction = self.session.get_transaction()
        if transaction is None or transaction.sync_transaction.origin is not SessionTransactionOrigin.BEGIN:
            raise TransactionRequiredError("Use 'async with session.begin()' before writes or row locks")

    @log_operation
    def _values(self, data: dict[str, Any], *, updating: bool = False) -> dict[str, Any]:
        if not isinstance(data, dict) or not data:
            raise ValueError("Provide a non-empty dictionary of column values")
        unknown = set(data) - set(self.table.c.keys())
        if unknown:
            raise ValueError("Unknown columns")
        protected = {column.name for column in self.table.c if column.primary_key}
        if updating:
            protected |= {column.name for column in self.table.c if column.foreign_keys}
            protected |= {"created_at", "updated_at", "public_id"}
        if protected & set(data):
            raise ValueError("Identifiers, ownership and creation timestamps cannot be reassigned")
        values = dict(data)
        if updating and "updated_at" in self.table.c:
            values["updated_at"] = func.clock_timestamp()
        return values

    @log_operation
    def _conditions(self, filters: dict[str, Any] | None) -> list:
        if filters is None:
            return []
        if not isinstance(filters, dict) or set(filters) - set(self.table.c.keys()):
            raise ValueError("Filters must contain mapped column names")
        return [self.table.c[key] == value for key, value in filters.items()]

    @log_operation
    @transactional
    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        self._require_transaction()
        statement = insert(self.table).values(**self._values(data)).returning(*self.table.c)
        row = (await self.session.execute(statement)).mappings().one()
        logger.info("Registro criado em %s", self.table.name)
        return {"item": dict(row)}

    @log_operation
    @transactional
    async def get(self, record_id: int, *, filters: dict[str, Any] | None = None,
                  for_update: bool = False) -> dict[str, Any]:
        statement = select(self.table).where(self.primary_key == record_id, *self._conditions(filters))
        if for_update:
            self._require_transaction()
            statement = statement.with_for_update()
        row = (await self.session.execute(statement)).mappings().one_or_none()
        return {"found": row is not None, "item": dict(row) if row is not None else None}

    @log_operation
    @transactional
    async def list(self, *, filters: dict[str, Any] | None = None,
                   limit: int = 100, offset: int = 0) -> dict[str, Any]:
        if not 1 <= limit <= 1000 or offset < 0:
            raise ValueError("Use limit between 1 and 1000 and a non-negative offset")
        statement = select(self.table).where(*self._conditions(filters)).order_by(self.primary_key).limit(limit).offset(offset)
        rows = (await self.session.execute(statement)).mappings().all()
        return {"items": [dict(row) for row in rows], "count": len(rows)}

    @log_operation
    @transactional
    async def update(self, record_id: int, data: dict[str, Any], *,
                     filters: dict[str, Any] | None = None,
                     expected: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_transaction()
        statement = update(self.table).where(
            self.primary_key == record_id, *self._conditions(filters), *self._conditions(expected),
        ).values(**self._values(data, updating=True)).returning(*self.table.c)
        row = (await self.session.execute(statement)).mappings().one_or_none()
        return {"updated": row is not None, "item": dict(row) if row is not None else None}

    @log_operation
    @transactional
    async def delete(self, record_id: int, *, filters: dict[str, Any] | None = None,
                     expected: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_transaction()
        statement = delete(self.table).where(
            self.primary_key == record_id, *self._conditions(filters), *self._conditions(expected),
        ).returning(self.primary_key)
        deleted = (await self.session.execute(statement)).scalar_one_or_none()
        return {"deleted": deleted is not None, "id": deleted}

    @log_operation
    async def _lock_dashboard(self, dashboard_id: int, *, owner_user_id: int | None = None) -> dict[str, Any]:
        self._require_transaction()
        table = Dashboard.__table__
        statement = select(table).where(table.c.id == dashboard_id)
        if owner_user_id is not None:
            statement = statement.where(table.c.user_id == owner_user_id)
        row = (await self.session.execute(statement.with_for_update())).mappings().one_or_none()
        if row is None:
            raise RecordNotFoundError("Dashboard not found in the requested scope")
        return dict(row)


class DashboardChildControl(TableControl):
    """Use the dashboard as the common lock for concurrent child mutations."""

    @log_operation
    @transactional
    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        await self._lock_dashboard(data["dashboard_id"])
        return await super().create(data)

    @log_operation
    async def _lock_child_parent(self, record_id: int, filters: dict[str, Any] | None) -> bool:
        self._require_transaction()
        record = await self.get(record_id, filters=filters)
        if not record["found"]:
            return False
        await self._lock_dashboard(record["item"]["dashboard_id"])
        return True

    @log_operation
    @transactional
    async def update(self, record_id: int, data: dict[str, Any], *,
                     filters: dict[str, Any] | None = None,
                     expected: dict[str, Any] | None = None) -> dict[str, Any]:
        if not await self._lock_child_parent(record_id, filters):
            return {"updated": False, "item": None}
        return await super().update(record_id, data, filters=filters, expected=expected)

    @log_operation
    @transactional
    async def delete(self, record_id: int, *, filters: dict[str, Any] | None = None,
                     expected: dict[str, Any] | None = None) -> dict[str, Any]:
        if not await self._lock_child_parent(record_id, filters):
            return {"deleted": False, "id": None}
        return await super().delete(record_id, filters=filters, expected=expected)
