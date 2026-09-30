"""HTTP routes for user data sources."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.data_sources import DataSourceCreate, DataSourceUpdate
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import control_db


router = APIRouter(prefix="/data-sources", tags=["data-sources"])


async def _owned(
    session: AsyncSession,
    data_source_id: int,
    user_id: int,
) -> dict[str, Any]:
    result = await control_repository(session).data_sources.db.get(
        data_source_id,
        filters={"user_id": user_id},
    )
    if not result["found"]:
        raise HTTPException(status_code=404, detail="Data source not found")
    return result["item"]


@router.get("/")
async def list_data_sources(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await control_repository(
        session,
    ).data_sources.db.list_by_user(
        current_user["user_id"],
        limit=limit,
        offset=offset,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_data_source(
    data: DataSourceCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    payload = data.model_dump()
    payload["user_id"] = current_user["user_id"]

    try:
        return await control_db.data_sources.create(session, payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{data_source_id}")
async def get_data_source(
    data_source_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await _owned(
        session,
        data_source_id,
        current_user["user_id"],
    )


@router.patch("/")
async def update_data_source(
    data: DataSourceUpdate,
    data_source_id: int = Query(..., gt=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned(session, data_source_id, current_user["user_id"])

    payload = data.model_dump(exclude_unset=True)

    if not payload:
        raise HTTPException(status_code=400, detail="No editable fields provided")

    try:
        result = await control_db.data_sources.update(
            session,
            data_source_id,
            payload,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if result is None:
        raise HTTPException(status_code=404, detail="Data source not found")
    return result


@router.delete(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete_data_source(
    data_source_id: int = Query(..., gt=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned(session, data_source_id, current_user["user_id"])
    return await control_db.data_sources.delete(session, data_source_id)
