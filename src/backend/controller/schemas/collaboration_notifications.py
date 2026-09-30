"""Schemas for collaboration-notification routes."""

from pydantic import Field

from .common import StrictSchema


class CollaborationNotificationCreate(StrictSchema):
    collaboration_id: int | None = Field(default=None, gt=0)
    dashboard_id: int | None = Field(default=None, gt=0)
    message: str = Field(min_length=1, max_length=5_000)
    notification_type: str = Field(min_length=1, max_length=40)


class CollaborationNotificationUpdate(StrictSchema):
    is_read: bool
