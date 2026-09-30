"""Schemas for verification routes."""

from pydantic import Field, field_validator

from .common import StrictSchema


class ValidationConsume(StrictSchema):
    number: str = Field(min_length=6, max_length=6)

    @field_validator("number")
    @classmethod
    def digits_only(cls, value: str) -> str:
        if not value.isascii() or not value.isdigit():
            raise ValueError("number must contain six digits")
        return value
