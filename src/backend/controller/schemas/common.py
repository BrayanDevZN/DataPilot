"""Shared Pydantic schemas for controller routes."""

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Pagination(StrictSchema):
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
