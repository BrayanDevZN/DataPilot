"""Schemas for account verification routes."""

from pydantic import EmailStr, Field, field_validator

from .common import StrictSchema, normalize_verification_code


class ValidationAccountIssue(StrictSchema):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def gmail_only(cls, value: EmailStr) -> EmailStr:
        if not str(value).lower().endswith("@gmail.com"):
            raise ValueError("email must use @gmail.com")
        return value


class ValidationAccountConsume(ValidationAccountIssue):
    number: str = Field(min_length=6, max_length=6)

    @field_validator("number", mode="before")
    @classmethod
    def digits_only(cls, value) -> str:
        return normalize_verification_code(value)
