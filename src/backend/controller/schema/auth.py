"""Schemas for authentication routes."""

from pydantic import Field, field_validator

from .common import StrictSchema, normalize_verification_code
from .users import UserResponse


class LoginRequest(StrictSchema):
    identifier: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=72)
    code: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password must not exceed 72 UTF-8 bytes")
        return value

    @field_validator("code", mode="before")
    @classmethod
    def validate_code(cls, value) -> str | None:
        if value is None:
            return None
        return normalize_verification_code(value)


class LoginResponse(StrictSchema):
    authenticated: bool
    auth2_required: bool = False
    message: str | None = None
    access_expires_at: int | None = None
    refresh_expires_at: int | None = None
    user: UserResponse | None = None


class RefreshResponse(StrictSchema):
    authenticated: bool = True
    access_expires_at: int
    refresh_expires_at: int


class LogoutResponse(StrictSchema):
    logged_out: bool = True
