"""Schemas for email sender routes."""

from typing import Literal

from pydantic import EmailStr, field_validator

from .common import StrictSchema, normalize_verification_code


EmailTemplate = Literal["create_account", "change_password", "auth2"]


class SenderRequest(StrictSchema):
    email: EmailStr
    template: EmailTemplate
    code: str

    @field_validator("code", mode="before")
    @classmethod
    def validate_code(cls, value) -> str:
        return normalize_verification_code(value)


class SenderResponse(StrictSchema):
    sent: bool
    template: EmailTemplate
    email: EmailStr
