"""Schemas for dashboard collaboration routes."""

from typing import Literal

from pydantic import Field

from .common import StrictSchema


class DashboardCollaborationCreate(StrictSchema):
    dashboard_id: int = Field(gt=0)
    collaborator_user_id: int = Field(gt=0)
    permission: Literal["read", "edit", "full"]


class DashboardCollaborationUpdate(StrictSchema):
    permission: Literal["read", "edit", "full"]


class DashboardCollaborationRespond(StrictSchema):
    response: Literal["accepted", "declined"]
