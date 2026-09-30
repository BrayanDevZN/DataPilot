from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .dashboard_collaborations import DashboardCollaboration
    from .dashboards import Dashboard
    from .users import User


class CollaborationNotification(Base):
    __tablename__ = "collaboration_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    collaboration_id: Mapped[int | None] = mapped_column(ForeignKey("dashboard_collaborations.id", ondelete="SET NULL"))
    dashboard_id: Mapped[int | None] = mapped_column(ForeignKey("dashboards.id", ondelete="SET NULL"))
    message: Mapped[str] = mapped_column(Text)
    notification_type: Mapped[str] = mapped_column(String(40))
    is_read: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("collaboration_notifications_user_idx", user_id, created_at.desc()),)

    user: Mapped["User"] = relationship(
        "User", back_populates="notifications", foreign_keys="CollaborationNotification.user_id", lazy="raise",
    )

    dashboard: Mapped["Dashboard | None"] = relationship(
        "Dashboard", back_populates="notifications", foreign_keys="CollaborationNotification.dashboard_id", lazy="raise",
    )

    collaboration: Mapped["DashboardCollaboration | None"] = relationship(
        "DashboardCollaboration", back_populates="notifications", foreign_keys="CollaborationNotification.collaboration_id", lazy="raise",
    )
