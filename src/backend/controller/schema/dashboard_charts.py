"""Schemas for dashboard chart routes."""

from typing import Any

from pydantic import Field

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
