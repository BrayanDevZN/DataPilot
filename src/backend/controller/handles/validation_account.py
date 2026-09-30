"""Public account-verification routes backed by Redis."""

from fastapi import APIRouter, HTTPException, status

from src.backend.controller.schema.validation_account import (
    ValidationAccountConsume,
    ValidationAccountIssue,
)
from src.backend.service.manage import sender, verification_codes


router = APIRouter(
    prefix="/validation-accounts",
    tags=["validation-accounts"],
)


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def issue_account_validation(
    data: ValidationAccountIssue,
):
    email = str(data.email).strip().lower()

    code = await verification_codes.issue(
        "create_account",
        email,
        expire=None,
    )

    try:
        await sender.create_account(email, code)
    except Exception:
        await verification_codes.delete(
            "create_account",
            email,
        )
        raise

    return {
        "issued": True,
        "email": email,
        "expires_in": 60,
    }


@router.post("/consume")
async def consume_account_validation(
    data: ValidationAccountConsume,
):
    email = str(data.email).strip().lower()

    consumed = await verification_codes.consume(
        "create_account",
        email,
        data.number,
    )

    if not consumed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    return {
        "validated": True,
        "email": email,
    }
