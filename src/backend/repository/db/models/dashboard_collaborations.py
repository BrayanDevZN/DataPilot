from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .collaboration_notifications import CollaborationNotification
    from .dashboards import Dashboard
    from .users import User


class DashboardCollaboration(Base):
    __tablename__ = "dashboard_collaborations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id", ondelete="CASCADE"))
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    collaborator_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    permission: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(10), server_default="accepted")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("dashboard_id", "collaborator_user_id"),
        CheckConstraint("permission IN ('read', 'edit', 'full')"),
        CheckConstraint("status IN ('pending', 'accepted', 'declined')"),
        CheckConstraint("owner_user_id <> collaborator_user_id"),
        Index("dashboard_collaborations_collaborator_idx", "collaborator_user_id"),
    )

    owner: Mapped["User"] = relationship(
        "User", back_populates="owned_collaborations", foreign_keys="DashboardCollaboration.owner_user_id", lazy="raise",
    )

    collaborator: Mapped["User"] = relationship(
        "User", back_populates="received_collaborations", foreign_keys="DashboardCollaboration.collaborator_user_id", lazy="raise",
    )

    dashboard: Mapped["Dashboard"] = relationship(
        "Dashboard", back_populates="collaborations", foreign_keys="DashboardCollaboration.dashboard_id", lazy="raise",
    )

    notifications: Mapped[list["CollaborationNotification"]] = relationship(
        "CollaborationNotification", back_populates="collaboration", foreign_keys="CollaborationNotification.collaboration_id",
        lazy="raise", passive_deletes="all",
    )
