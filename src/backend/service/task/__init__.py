"""Celery task application and database task registration."""

from src.backend.infra.manage import celery

task_app = celery

from .db import (  # noqa: E402,F401
    collaboration_notifications,
    conversations,
    dashboards,
    data_sources,
    dashboard_collaborations,
    users,
)
