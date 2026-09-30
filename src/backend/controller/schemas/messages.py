"""Schemas for message routes."""

from typing import Literal

from pydantic import Field

from .common import StrictSchema


class MessageCreate(StrictSchema):
    conversation_id: int = Field(gt=0)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=100_000)


class MessageUpdate(StrictSchema):
    role: Literal["user", "assistant"] | None = None
    content: str | None = Field(default=None, min_length=1, max_length=100_000)
