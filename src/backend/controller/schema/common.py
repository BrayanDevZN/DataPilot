"""Shared Pydantic schemas for controller routes."""

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Pagination(StrictSchema):
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


def normalize_verification_code(value) -> str:
    if isinstance(value, bool):
        raise ValueError("verification code must contain six digits")

    if isinstance(value, int):
        if not 0 <= value <= 999_999:
            raise ValueError("verification code must contain six digits")
        return f"{value:06d}"

    text = str(value).strip()
    if len(text) != 6 or not text.isascii() or not text.isdigit():
        raise ValueError("verification code must contain six digits")
    return text
