"""HTTP routes for user dashboards."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.dashboards import DashboardCreate, DashboardUpdate
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import control_db


router = APIRouter(prefix="/dashboards", tags=["dashboards"])


async def _owned_dashboard(
    session: AsyncSession,
    dashboard_id: int,
    user_id: int,
) -> dict[str, Any]:
    result = await control_repository(session).dashboards.db.get(
        dashboard_id,
        filters={"user_id": user_id},
    )
    if not result["found"]:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return result["item"]


async def _validate_source(
    session: AsyncSession,
    source_id: int | None,
    user_id: int,
) -> None:
    if source_id is None:
        return

    result = await control_repository(session).data_sources.db.get(
        source_id,
        filters={"user_id": user_id},
    )
    if not result["found"]:
        raise HTTPException(
            status_code=400,
            detail="Data source does not belong to the current user",
        )


@router.get("")
async def list_dashboards(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await control_repository(
        session,
    ).dashboards.db.list_by_user(
        current_user["user_id"],
        limit=limit,
        offset=offset,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    data: DashboardCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    payload = data.model_dump()

    await _validate_source(
        session,
        payload.get("data_source_id"),
        current_user["user_id"],
    )

    payload["user_id"] = current_user["user_id"]

    try:
        return await control_db.dashboards.create(session, payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{dashboard_id}")
async def get_dashboard(
    dashboard_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await control_repository(
            session,
        ).dashboards.db.get_with_charts(
            dashboard_id,
            current_user["user_id"],
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Dashboard not found") from error

    return result["item"]


@router.patch("/{dashboard_id}")
async def update_dashboard(
    dashboard_id: int,
    data: DashboardUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_dashboard(session, dashboard_id, current_user["user_id"])

    payload = data.model_dump(exclude_unset=True)

    if "data_source_id" in payload:
        await _validate_source(
            session,
            payload["data_source_id"],
            current_user["user_id"],
        )

    if not payload:
        raise HTTPException(status_code=400, detail="No editable fields provided")

    try:
        result = await control_db.dashboards.update(
            session,
            dashboard_id,
            payload,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if result is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return result


@router.delete(
    "/{dashboard_id}",
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete_dashboard(
    dashboard_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_dashboard(session, dashboard_id, current_user["user_id"])
    return await control_db.dashboards.delete(session, dashboard_id)
