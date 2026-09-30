"""Shared access point for repository controls used by the service layer."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infra.manage import redis
from src.backend.repository.manage import ControlDb as RepositoryControlDb


class ControlRepository:
    def __call__(self, session: AsyncSession) -> RepositoryControlDb:
        return RepositoryControlDb(redis.client, session)


control_repository = ControlRepository()
