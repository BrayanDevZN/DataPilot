"""Public account-verification routes."""

from secrets import randbelow
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_session
from src.backend.controller.schema.validation_account import (
    ValidationAccountConsume,
    ValidationAccountIssue,
)
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import sender


router = APIRouter(
    prefix="/validation-accounts",
    tags=["validation-accounts"],
)


def _code() -> str:
    return f"{randbelow(1_000_000):06d}"


@router.post("", status_code=status.HTTP_201_CREATED)
async def issue_account_validation(
    data: ValidationAccountIssue,
    session: AsyncSession = Depends(get_session),
):
    email = data.email.strip().lower()

    code = _code()

    try:
        result = await control_repository(
            session,
        ).validation_account.db.issue(email, code)
        await sender.create_account(email, code)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "issued": True,
        "validation_id": result["item"]["validation_id"],
        "email": email,
    }


@router.post("/consume")
async def consume_account_validation(
    data: ValidationAccountConsume,
    session: AsyncSession = Depends(get_session),
):
    email = data.email.strip().lower()
    number = data.number

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
