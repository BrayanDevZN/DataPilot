"""Schemas for dashboard routes."""

from pydantic import Field, model_validator

from .common import StrictSchema


class DashboardCreate(StrictSchema):
    title: str = Field(min_length=1, max_length=300)
    prompt: str = Field(default="", max_length=20_000)
    ai_suggestion: str | None = Field(default=None, max_length=100_000)
    file_name: str | None = Field(default=None, max_length=500)
    data_source_id: int | None = Field(default=None, gt=0)
    is_outdated: bool = False


class DashboardUpdate(StrictSchema):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    prompt: str | None = Field(default=None, max_length=20_000)
    ai_suggestion: str | None = Field(default=None, max_length=100_000)
    file_name: str | None = Field(default=None, max_length=500)
    data_source_id: int | None = Field(default=None, gt=0)
    is_outdated: bool | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        nullable = {"ai_suggestion", "file_name", "data_source_id"}
        for field in self.model_fields_set - nullable:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self
