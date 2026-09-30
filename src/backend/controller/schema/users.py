"""Schemas for user routes."""

from typing import Literal

from pydantic import EmailStr, Field, field_validator, model_validator

from .common import StrictSchema, normalize_verification_code


Gender = Literal["MASCULINO", "FEMININO", "PREFIRO NÃO DIZER"]


def _validate_password(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("password must not exceed 72 UTF-8 bytes")
    if not any(character.isupper() for character in value):
        raise ValueError("password must contain an uppercase letter")
    if not any(character.islower() for character in value):
        raise ValueError("password must contain a lowercase letter")
    if not any(character.isdigit() for character in value):
        raise ValueError("password must contain a number")
    return value


class UserCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=200)
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    age: int = Field(gt=0, le=130)
    gender: Gender
    profile_image: str | None = Field(default=None, max_length=2_000)
    auth2: bool = False
    code: str = Field(min_length=6, max_length=6)

    @field_validator("email")
    @classmethod
    def gmail_only(cls, value: EmailStr) -> EmailStr:
        if not str(value).lower().endswith("@gmail.com"):
            raise ValueError("email must use @gmail.com")
        return value

    @field_validator("password")
    @classmethod
    def password_rules(cls, value: str) -> str:
        return _validate_password(value)

    @field_validator("code", mode="before")
    @classmethod
    def code_rules(cls, value) -> str:
        return normalize_verification_code(value)


class UserUpdate(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    username: str | None = Field(default=None, min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$")
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    age: int | None = Field(default=None, gt=0, le=130)
    gender: Gender | None = None
    profile_image: str | None = Field(default=None, max_length=2_000)
    auth2: bool | None = None

    @field_validator("email")
    @classmethod
    def gmail_only(cls, value: EmailStr | None) -> EmailStr | None:
        if value is not None and not str(value).lower().endswith("@gmail.com"):
            raise ValueError("email must use @gmail.com")
        return value

    @field_validator("password")
    @classmethod
    def password_rules(cls, value: str | None) -> str | None:
        return _validate_password(value) if value is not None else None

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        nullable = {"profile_image"}
        for field in self.model_fields_set - nullable:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self
