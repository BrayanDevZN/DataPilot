"""HTTP routes for users."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.auth import LoginResponse
from src.backend.controller.schema.users import UserCreate, UserUpdate
from src.backend.controller.session import create_session
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import control_db, hash


router = APIRouter(prefix="/users", tags=["users"])


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    data = dict(user)
    data.pop("password", None)
    return data


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=LoginResponse,
)
async def create_user(
    data: UserCreate,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    payload = data.model_dump()
    code = payload.pop("code")
    email = str(payload["email"]).strip().lower()
    username = payload["username"].strip().lower()

    if await control_db.users.get(session, "email", email) is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    if await control_db.users.get(session, "username", username) is not None:
        raise HTTPException(status_code=409, detail="Username already registered")

    consumed = await control_repository(
        session,
    ).validation_account.db.consume(email, code)

    if not consumed["consumed"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification code",
        )

    payload["email"] = email
    payload["username"] = username
    payload["password"] = hash.generate(payload["password"])
    payload["role"] = "user"
    payload["status"] = True

    try:
        user = await control_db.users.create(session, payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return await create_session(response, user)


@router.get("/me")
async def get_me(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    return current_user


@router.patch("/me")
async def update_me(
    data: UserUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    payload = data.model_dump(exclude_unset=True)

    if "password" in payload:
        payload["password"] = hash.generate(payload["password"])

    if not payload:
        raise HTTPException(status_code=400, detail="No editable fields provided")

    try:
        user = await control_db.users.update(
            session,
            "user_id",
            current_user["user_id"],
            payload,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return _public_user(user)


@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
async def delete_me(
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await control_db.users.delete(
        session,
        current_user["user_id"],
    )
