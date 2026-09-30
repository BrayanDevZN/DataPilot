"""Authenticated password-verification routes backed by Redis."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.backend.controller.dependencies import get_current_user
from src.backend.controller.schema.validation import ValidationConsume
from src.backend.service.manage import sender, verification_codes


router = APIRouter(prefix="/validation", tags=["validation"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def issue_validation(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    email = str(current_user["email"]).strip().lower()

    code = await verification_codes.issue(
        "change_password",
        email,
        expire=None,
    )

    try:
        await sender.change_password(email, code)
    except Exception:
        await verification_codes.delete(
            "change_password",
            email,
        )
        raise

    return {
        "issued": True,
        "email": email,
        "expires_in": 60,
    }


@router.post("/consume")
async def consume_validation(
    data: ValidationConsume,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    email = str(current_user["email"]).strip().lower()

    consumed = await verification_codes.consume(
        "change_password",
        email,
        data.number,
    )

    if not consumed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    return {"validated": True}
