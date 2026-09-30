"""Schemas for public transactional email routes."""

from typing import Literal

from pydantic import EmailStr, field_validator

from .common import StrictSchema, normalize_verification_code


class SenderBaseRequest(StrictSchema):
    email: EmailStr
    code: str

    @field_validator("code", mode="before")
    @classmethod
    def validate_code(cls, value) -> str:
        return normalize_verification_code(value)


class CreateAccountEmailRequest(SenderBaseRequest):
    pass


class ChangePasswordEmailRequest(SenderBaseRequest):
    pass


class Auth2EmailRequest(SenderBaseRequest):
    pass


class SenderResponse(StrictSchema):
    sent: bool
    type: Literal["create_account", "change_password", "auth2"]
    email: EmailStr
