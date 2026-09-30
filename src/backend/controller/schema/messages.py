"""Schemas for message routes."""

from typing import Literal

from pydantic import Field, model_validator

from .common import StrictSchema


class MessageCreate(StrictSchema):
    conversation_id: int = Field(gt=0)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=100_000)


class MessageUpdate(StrictSchema):
    role: Literal["user", "assistant"] | None = None
    content: str | None = Field(default=None, min_length=1, max_length=100_000)

    @model_validator(mode="after")
    def reject_null_fields(self):
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self
