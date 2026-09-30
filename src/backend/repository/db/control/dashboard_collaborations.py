"""Concurrent-safe invitations and state transitions for dashboard sharing."""

from typing import Any, Literal

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from src.backend.logs.log import log_operation

from ..control_base import DashboardChildControl
from ..models import DashboardCollaboration


class DashboardCollaborationsControl(DashboardChildControl):
    model = DashboardCollaboration

    @log_operation
    async def invite(self, dashboard_id: int, owner_user_id: int, collaborator_user_id: int,
                     permission: Literal["read", "edit", "full"]) -> dict[str, Any]:
        if permission not in ("read", "edit", "full") or owner_user_id == collaborator_user_id:
            raise ValueError("Invalid collaboration permission or users")
        await self._lock_dashboard(dashboard_id, owner_user_id=owner_user_id)
        columns = self.table.c
        statement = insert(self.table).values(
            dashboard_id=dashboard_id, owner_user_id=owner_user_id,
            collaborator_user_id=collaborator_user_id, permission=permission, status="pending",
        ).on_conflict_do_update(
            index_elements=[columns.dashboard_id, columns.collaborator_user_id],
            set_={"permission": permission, "status": "pending", "updated_at": func.clock_timestamp()},
        ).returning(*self.table.c)
        row = (await self.session.execute(statement)).mappings().one()
        return {"item": dict(row)}

    @log_operation
    async def respond(self, collaboration_id: int, collaborator_user_id: int,
                      response: Literal["accepted", "declined"]) -> dict[str, Any]:
        if response not in ("accepted", "declined"):
            raise ValueError("Invalid invitation response")
        # The pending status is checked in the UPDATE, not in an earlier SELECT.
        return await self.update(collaboration_id, {"status": response},
                                 filters={"collaborator_user_id": collaborator_user_id},
                                 expected={"status": "pending"})
