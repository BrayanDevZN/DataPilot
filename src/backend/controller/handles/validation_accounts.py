"""Public account-verification routes."""

from secrets import randbelow
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_session
from src.backend.service.db.repository import control_repository


router = APIRouter(
    prefix="/validation-accounts",
    tags=["validation-accounts"],
)


def _code() -> str:
    return f"{randbelow(1_000_000):06d}"


@router.post("", status_code=status.HTTP_201_CREATED)
async def issue_account_validation(
    data: dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
):
    email = str(data.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        result = await control_repository(
            session,
        ).validation_account.db.issue(email, _code())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "issued": True,
        "validation_id": result["item"]["validation_id"],
        "email": email,
    }


@router.post("/consume")
async def consume_account_validation(
    data: dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
):
    email = str(data.get("email") or "").strip().lower()
    number = str(data.get("number") or "").strip()

    if not email or not number:
        raise HTTPException(
            status_code=400,
            detail="Email and verification code are required",
        )

    try:
        result = await control_repository(
            session,
        ).validation_account.db.consume(email, number)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if not result["consumed"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification code",
        )

    return {"validated": True, "email": email}
