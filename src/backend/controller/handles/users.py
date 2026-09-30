"""HTTP routes for users."""

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.service.manage import control_db, hash


router = APIRouter(prefix="/users", tags=["users"])


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    data = dict(user)
    data.pop("password", None)
    return data


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    data: dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
):
    payload = dict(data)
    for field in ("user_id", "public_id", "created_at"):
        payload.pop(field, None)

    password = payload.get("password")
    if not isinstance(password, str) or not password:
        raise HTTPException(status_code=400, detail="Password is required")

    payload["password"] = hash.generate(password)
    payload.setdefault("role", "user")
    payload.setdefault("status", False)

    try:
        user = await control_db.users.create(session, payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return _public_user(user)


@router.get("/me")
async def get_me(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    return current_user


@router.patch("/me")
async def update_me(
    data: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    payload = dict(data)
    for field in ("user_id", "public_id", "role", "status", "created_at"):
        payload.pop(field, None)

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
