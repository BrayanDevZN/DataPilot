"""Schemas for dashboard chart routes."""

from typing import Any

from pydantic import Field, model_validator

from .common import StrictSchema


class DashboardChartCreate(StrictSchema):
    dashboard_id: int = Field(gt=0)
    chart_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    chart_data: dict[str, Any] | list[Any]
    chart_config: dict[str, Any] = Field(default_factory=dict)


class DashboardChartUpdate(StrictSchema):
    chart_type: str | None = Field(default=None, min_length=1, max_length=100)
    title: str | None = Field(default=None, min_length=1, max_length=300)
    chart_data: dict[str, Any] | list[Any] | None = None
    chart_config: dict[str, Any] | None = None

    @model_validator(mode="after")
    def reject_null_fields(self):
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self
