"""Schemas for data-source routes."""

from pydantic import Field, model_validator

from .common import StrictSchema


class DataSourceUpdate(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    refresh_interval_days: int | None = Field(default=None, ge=1, le=3650)

    @model_validator(mode="after")
    def require_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


class SQLDataSourceCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=300)
    database_url: str = Field(min_length=1, max_length=2_000)
    query: str = Field(min_length=1, max_length=100_000)
    refresh_interval_days: int | None = Field(default=None, ge=1, le=3650)


class SQLDataSourceUpdate(StrictSchema):
    database_url: str | None = Field(default=None, min_length=1, max_length=2_000)
    query: str | None = Field(default=None, min_length=1, max_length=100_000)
    refresh_interval_days: int | None = Field(default=None, ge=1, le=3650)

    @model_validator(mode="after")
    def require_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


class SQLDataSourceExecute(StrictSchema):
    query: str | None = Field(default=None, min_length=1, max_length=100_000)
    save_query: bool = False
