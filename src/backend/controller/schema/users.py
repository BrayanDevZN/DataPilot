"""Schemas for user routes."""

from pydantic import EmailStr, Field, model_validator

from .common import StrictSchema


class UserCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=200)
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    age: int = Field(ge=13, le=130)
    gender: str = Field(min_length=1, max_length=50)
    profile_image: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        nullable = {"profile_image"}
        for field in self.model_fields_set - nullable:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class UserUpdate(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    username: str | None = Field(default=None, min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    age: int | None = Field(default=None, ge=13, le=130)
    gender: str | None = Field(default=None, min_length=1, max_length=50)
    profile_image: str | None = Field(default=None, max_length=2_000)

