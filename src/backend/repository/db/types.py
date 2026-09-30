"""Database types shared by PostgreSQL and SQLite models."""

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB


JSONType = JSON().with_variant(JSONB(), "postgresql")
