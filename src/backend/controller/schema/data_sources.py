"""Schemas for data-source routes."""

from typing import Any, Literal

from pydantic import Field, model_validator

from .common import StrictSchema


class DataSourceCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=300)
    file_name: str = Field(min_length=1, max_length=500)
    file_data: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    source_type: Literal["file", "web", "database"] = "file"
    connection_config: dict[str, Any] = Field(default_factory=dict)
    refresh_interval_days: int | None = Field(default=None, ge=1, le=3650)


class DataSourceUpdate(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    file_name: str | None = Field(default=None, min_length=1, max_length=500)
    file_data: list[dict[str, Any]] | None = None
    row_count: int | None = Field(default=None, ge=0)
    column_count: int | None = Field(default=None, ge=0)
    source_type: Literal["file", "web", "database"] | None = None
    connection_config: dict[str, Any] | None = None
    refresh_interval_days: int | None = Field(default=None, ge=1, le=3650)

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        nullable = {"refresh_interval_days"}
        for field in self.model_fields_set - nullable:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self
