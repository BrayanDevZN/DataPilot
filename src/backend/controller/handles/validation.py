"""Authenticated verification-code routes."""

from secrets import randbelow
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.validation import ValidationConsume
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import sender


router = APIRouter(prefix="/validation", tags=["validation"])


def _code() -> str:
    return f"{randbelow(1_000_000):06d}"


@router.post("/", status_code=status.HTTP_201_CREATED)
async def issue_validation(
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    code = _code()

    try:
        result = await control_repository(
            session,
        ).validation.db.issue(current_user["user_id"], code)
        await sender.change_password(current_user["email"], code)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "issued": True,
        "validation_id": result["item"]["validation_id"],
    }


@router.post("/consume")
async def consume_validation(
    data: ValidationConsume,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    number = data.number

    try:
        result = await control_repository(
            session,
        ).validation.db.consume(
            current_user["user_id"],
            number,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if not result["consumed"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification code",
        )

    return {"validated": True}
