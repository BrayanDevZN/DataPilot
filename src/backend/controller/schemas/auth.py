"""Schemas for authentication routes."""

from pydantic import Field, field_validator

from .common import StrictSchema


class LoginRequest(StrictSchema):
    identifier: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=72)
    auth2: bool = False
    code: str | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) != 6 or not value.isascii() or not value.isdigit():
            raise ValueError("code must contain six digits")
        return value


class LoginResponse(StrictSchema):
    authenticated: bool
    auth2_required: bool = False
    access_expires_at: int | None = None
    refresh_expires_at: int | None = None
    user: dict | None = None


class RefreshResponse(StrictSchema):
    authenticated: bool = True
    access_expires_at: int
    refresh_expires_at: int


class LogoutResponse(StrictSchema):
    logged_out: bool = True
