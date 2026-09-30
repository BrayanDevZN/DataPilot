"""Schemas for verification routes."""

from pydantic import Field, field_validator

from .common import StrictSchema, normalize_verification_code


class ValidationConsume(StrictSchema):
    number: str = Field(min_length=6, max_length=6)

    @field_validator("number", mode="before")
    @classmethod
    def digits_only(cls, value) -> str:
        return normalize_verification_code(value)
