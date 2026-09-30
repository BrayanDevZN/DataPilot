"""Schemas for account verification routes."""

from pydantic import EmailStr, Field, field_validator

from .common import StrictSchema


class ValidationAccountIssue(StrictSchema):
    email: EmailStr


class ValidationAccountConsume(ValidationAccountIssue):
    number: str = Field(min_length=6, max_length=6)

    @field_validator("number")
    @classmethod
    def digits_only(cls, value: str) -> str:
        if not value.isascii() or not value.isdigit():
            raise ValueError("number must contain six digits")
        return value
