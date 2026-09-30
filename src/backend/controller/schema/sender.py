"""Schemas for public transactional email routes."""

from typing import Literal

from pydantic import EmailStr

from .common import StrictSchema


class SenderBaseRequest(StrictSchema):
    email: EmailStr


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
    expires_in: int
