"""HTTP routes for dashboard charts."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.dashboard_charts import DashboardChartCreate, DashboardChartUpdate
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import control_db


router = APIRouter(
    prefix="/dashboard-charts",
    tags=["dashboard-charts"],
)


async def _owned_dashboard(
    session: AsyncSession,
    dashboard_id: int,
    user_id: int,
) -> None:
    result = await control_repository(session).dashboards.db.get(
        dashboard_id,
        filters={"user_id": user_id},
    )
    if not result["found"]:
        raise HTTPException(status_code=404, detail="Dashboard not found")


async def _owned_chart(
    session: AsyncSession,
    chart_id: int,
    user_id: int,
) -> dict[str, Any]:
    result = await control_repository(session).dashboard_charts.db.get(
        chart_id,
    )
    if not result["found"]:
        raise HTTPException(status_code=404, detail="Chart not found")

    await _owned_dashboard(
        session,
        result["item"]["dashboard_id"],
        user_id,
    )
    return result["item"]


@router.get("")
async def list_dashboard_charts(
    dashboard_id: int = Query(..., ge=1),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_dashboard(
        session,
        dashboard_id,
        current_user["user_id"],
    )
    return await control_repository(
        session,
    ).dashboard_charts.db.list_by_dashboard(
        dashboard_id,
        limit=limit,
        offset=offset,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_dashboard_chart(
    data: DashboardChartCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    payload = data.model_dump()
    dashboard_id = data.dashboard_id

    await _owned_dashboard(
        session,
        dashboard_id,
        current_user["user_id"],
    )

    payload["dashboard_id"] = dashboard_id

    try:
        return await control_db.dashboard_charts.create(session, payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{chart_id}")
async def get_dashboard_chart(
    chart_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await _owned_chart(
        session,
        chart_id,
        current_user["user_id"],
    )


@router.patch("/{chart_id}")
async def update_dashboard_chart(
    chart_id: int,
    data: DashboardChartUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_chart(session, chart_id, current_user["user_id"])

    payload = data.model_dump(exclude_unset=True)

    if not payload:
        raise HTTPException(status_code=400, detail="No editable fields provided")

    result = await control_db.dashboard_charts.update(
        session,
        chart_id,
        payload,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Chart not found")
    return result


@router.delete("/{chart_id}")
async def delete_dashboard_chart(
    chart_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_chart(session, chart_id, current_user["user_id"])
    return await control_db.dashboard_charts.delete(session, chart_id)
