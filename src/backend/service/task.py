"""Celery task application exposed to the service layer."""

from src.backend.infra.manage import celery


task_app = celery
