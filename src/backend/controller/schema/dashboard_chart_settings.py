"""Schemas for dashboard chart-setting routes."""

from pydantic import Field, model_validator

from .common import StrictSchema


class DashboardChartSettingsSave(StrictSchema):
    dashboard_id: int = Field(gt=0)
    chart_id: int | None = Field(default=None, gt=0)
    chart_color: str = Field(default="#4f46e5", min_length=1, max_length=100)
    chart_background: str = Field(default="#f8fafc", min_length=1, max_length=100)
    x_axis_text_color: str = Field(default="#0f172a", min_length=1, max_length=100)
    y_axis_text_color: str = Field(default="#0f172a", min_length=1, max_length=100)
    grid_color: str = Field(default="#cbd5e1", min_length=1, max_length=100)
    grid_style: str = Field(default="3 3", min_length=1, max_length=100)
    bar_style: str = Field(default="rounded", min_length=1, max_length=100)
    pie_colors: list[str] = Field(default_factory=list, max_length=100)
    show_legend: bool = True


class DashboardChartSettingsUpdate(StrictSchema):
    chart_color: str | None = Field(default=None, min_length=1, max_length=100)
    chart_background: str | None = Field(default=None, min_length=1, max_length=100)
    x_axis_text_color: str | None = Field(default=None, min_length=1, max_length=100)
    y_axis_text_color: str | None = Field(default=None, min_length=1, max_length=100)
    grid_color: str | None = Field(default=None, min_length=1, max_length=100)
    grid_style: str | None = Field(default=None, min_length=1, max_length=100)
    bar_style: str | None = Field(default=None, min_length=1, max_length=100)
    pie_colors: list[str] | None = Field(default=None, max_length=100)
    show_legend: bool | None = None

    @model_validator(mode="after")
    def reject_null_fields(self):
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self
