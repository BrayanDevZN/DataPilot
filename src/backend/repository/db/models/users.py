from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .collaboration_notifications import CollaborationNotification
    from .conversations import Conversation
    from .dashboard_collaborations import DashboardCollaboration
    from .dashboards import Dashboard
    from .data_sources import DataSource
    from .validation import Validation


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, default=uuid4)
    name: Mapped[str] = mapped_column(Text)
    username: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(Text)
    password: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text, server_default="user")
    status: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    auth2: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(Text)
    profile_image: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("users_public_id_unique", public_id, unique=True),
        Index("users_username_lower_unique", func.lower(username), unique=True),
        Index("users_email_lower_unique", func.lower(email), unique=True),
    )

    validations: Mapped[list["Validation"]] = relationship(
        "Validation", back_populates="user", foreign_keys="Validation.user_id",
        lazy="raise", passive_deletes="all",
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="user", foreign_keys="Conversation.user_id",
        lazy="raise", passive_deletes="all",
    )

    data_sources: Mapped[list["DataSource"]] = relationship(
        "DataSource", back_populates="user", foreign_keys="DataSource.user_id",
        lazy="raise", passive_deletes="all",
    )

    dashboards: Mapped[list["Dashboard"]] = relationship(
        "Dashboard", back_populates="user", foreign_keys="Dashboard.user_id",
        lazy="raise", passive_deletes="all",
    )

    owned_collaborations: Mapped[list["DashboardCollaboration"]] = relationship(
        "DashboardCollaboration", back_populates="owner", foreign_keys="DashboardCollaboration.owner_user_id",
        lazy="raise", passive_deletes="all",
    )

    received_collaborations: Mapped[list["DashboardCollaboration"]] = relationship(
        "DashboardCollaboration", back_populates="collaborator", foreign_keys="DashboardCollaboration.collaborator_user_id",
        lazy="raise", passive_deletes="all",
    )

    notifications: Mapped[list["CollaborationNotification"]] = relationship(
        "CollaborationNotification", back_populates="user", foreign_keys="CollaborationNotification.user_id",
        lazy="raise", passive_deletes="all",
    )
