"""Data-source operations and short-lived claims for background synchronization."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import case, func, select, update

from src.backend.logs.log import log_operation

from ..control_base import transactional, TableControl
from ..models import DataSource


class DataSourcesControl(TableControl):
    model = DataSource

    @log_operation
    @transactional
    async def list_by_user(self, user_id: int, *, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return await self.list(filters={"user_id": user_id}, limit=limit, offset=offset)

    @log_operation
    @transactional
    async def claim_due(self, user_id: int, *, limit: int = 20,
                        lease: timedelta = timedelta(minutes=5)) -> dict[str, Any]:
        self._require_transaction()
        if not 1 <= limit <= 1000 or lease.total_seconds() <= 0:
            raise ValueError("Invalid claim limit or lease")
        columns = self.table.c
        statement = select(columns.id).where(
            columns.user_id == user_id, columns.source_type.in_(("web", "database")),
            columns.refresh_interval_days.is_not(None), columns.next_sync_at <= func.clock_timestamp(),
        ).order_by(columns.next_sync_at, columns.id).limit(limit).with_for_update(skip_locked=True)
        ids = (await self.session.execute(statement)).scalars().all()
        if not ids:
            return {"items": [], "count": 0}
        # The returned next_sync_at is the lease token used by finish_sync.
        claimed = update(self.table).where(columns.id.in_(ids)).values(
            next_sync_at=func.clock_timestamp() + lease,
        ).returning(*self.table.c)
        rows = (await self.session.execute(claimed)).mappings().all()
        return {"items": [dict(row) for row in rows], "count": len(rows)}

    @log_operation
    @transactional
    async def finish_sync(self, source_id: int, user_id: int, data: dict[str, Any],
                          expected_next_sync_at: datetime) -> dict[str, Any]:
        self._require_transaction()
        allowed = {"file_data", "file_name", "row_count", "column_count"}
        if not data or set(data) - allowed:
            raise ValueError("Only source snapshot fields can be supplied")
        columns = self.table.c
        values = self._values(data, updating=True)
        values.update(last_synced_at=func.clock_timestamp(), next_sync_at=case(
            (columns.refresh_interval_days.is_(None), None),
            else_=func.clock_timestamp() + columns.refresh_interval_days * timedelta(days=1),
        ))
        statement = update(self.table).where(
            columns.id == source_id, columns.user_id == user_id,
            columns.next_sync_at == expected_next_sync_at,
            columns.next_sync_at > func.clock_timestamp(),
        ).values(**values).returning(*self.table.c)
        row = (await self.session.execute(statement)).mappings().one_or_none()
        return {"updated": row is not None, "item": dict(row) if row is not None else None}
