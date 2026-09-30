"""Schemas for conversation routes."""

from pydantic import Field

from .common import StrictSchema


class ConversationCreate(StrictSchema):
    title: str = Field(min_length=1, max_length=300)


class ConversationUpdate(StrictSchema):
    title: str = Field(min_length=1, max_length=300)
