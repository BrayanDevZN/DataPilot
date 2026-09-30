"""HTTP routes for user-owned file and SQL data sources."""

from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.data_sources import (
    DataSourceUpdate,
    SQLDataSourceCreate,
    SQLDataSourceExecute,
    SQLDataSourceUpdate,
)
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import control_db
from src.backend.service.source_ingestion import file_reader, sql_query_tool


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found",
        )

    return result["item"]


def _schedule(
    refresh_interval_days: int | None,
) -> tuple[datetime, datetime | None]:
    now = datetime.now()
    next_sync_at = (
        now + timedelta(days=refresh_interval_days)
        if refresh_interval_days is not None
        else None
    )
    return now, next_sync_at


def _database_url(source: dict[str, Any]) -> str | None:
    config = source.get("connection_config") or {}
    value = config.get("database_url")
    return str(value).strip() if value else None


@router.get("/")
async def list_data_sources(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await control_repository(
        session,
    ).data_sources.db.list_by_user(
        current_user["user_id"],
        limit=limit,
        offset=offset,
    )

    return {
        "data_sources": result["items"],
        "count": result["count"],
    }


@router.get("/linked-dashboards")
async def get_linked_dashboards(
    data_source_id: int = Query(..., gt=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned(
        session,
        data_source_id,
        current_user["user_id"],
    )

    result = await control_repository(
        session,
    ).dashboards.db.list(
        filters={
            "user_id": current_user["user_id"],
            "data_source_id": data_source_id,
        },
        limit=1000,
    )

    return {
        "dashboards": result["items"],
        "count": result["count"],
    }


@router.get("/{data_source_id}")
async def get_data_source(
    data_source_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    source = await _owned(
        session,
        data_source_id,
        current_user["user_id"],
    )
    return {"data_source": source}


@router.post(
    "/file",
    status_code=status.HTTP_201_CREATED,
)
async def create_file_data_source(
    name: Annotated[str, Form(min_length=1, max_length=300)],
    file: Annotated[UploadFile, File()],
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    filename = file.filename or "dataset"

    try:
        content = await file.read()
        snapshot = file_reader.read(filename, content)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    finally:
        await file.close()

    payload = {
        "user_id": current_user["user_id"],
        "name": name.strip(),
        "file_name": filename,
        "file_data": snapshot.rows,
        "row_count": snapshot.row_count,
        "column_count": snapshot.column_count,
        "source_type": "file",
        "connection_config": {},
        "sql_query": None,
        "refresh_interval_days": None,
        "last_synced_at": None,
        "next_sync_at": None,
    }

    try:
        source = await control_db.data_sources.create(
            session,
            payload,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return {"data_source": source}


@router.post(
    "/sql",
    status_code=status.HTTP_201_CREATED,
)
async def create_sql_data_source(
    data: SQLDataSourceCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        snapshot = await sql_query_tool.execute(
            data.database_url,
            data.query,
        )
        database_url = sql_query_tool.validate_database_url(
            data.database_url
        )
        query = sql_query_tool.validate_query(data.query)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to query external database",
        ) from error

    last_synced_at, next_sync_at = _schedule(
        data.refresh_interval_days
    )

    payload = {
        "user_id": current_user["user_id"],
        "name": data.name,
        "file_name": "PostgreSQL query",
        "file_data": snapshot.rows,
        "row_count": snapshot.row_count,
        "column_count": snapshot.column_count,
        "source_type": "database",
        "connection_config": {
            "database_url": database_url,
        },
        "sql_query": query,
        "refresh_interval_days": data.refresh_interval_days,
        "last_synced_at": last_synced_at,
        "next_sync_at": next_sync_at,
    }

    try:
        source = await control_db.data_sources.create(
            session,
            payload,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return {"data_source": source}


@router.patch("/")
async def update_data_source_metadata(
    data: DataSourceUpdate,
    data_source_id: int = Query(..., gt=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    source = await _owned(
        session,
        data_source_id,
        current_user["user_id"],
    )

    payload = data.model_dump(exclude_unset=True)

    if "refresh_interval_days" in payload:
        days = payload["refresh_interval_days"]
        payload["next_sync_at"] = (
            datetime.now() + timedelta(days=days)
            if days is not None
            and source["source_type"] in {"database", "web"}
            else None
        )

    try:
        updated = await control_db.data_sources.update(
            session,
            data_source_id,
            payload,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found",
        )

    return {"data_source": updated}


@router.patch("/file")
async def update_file_data_source(
    data_source_id: int = Query(..., gt=0),
    file: Annotated[UploadFile, File()],
    name: Annotated[str | None, Form(max_length=300)] = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned(
        session,
        data_source_id,
        current_user["user_id"],
    )

    filename = file.filename or "dataset"

    try:
        content = await file.read()
        snapshot = file_reader.read(filename, content)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    finally:
        await file.close()

    payload: dict[str, Any] = {
        "file_name": filename,
        "file_data": snapshot.rows,
        "row_count": snapshot.row_count,
        "column_count": snapshot.column_count,
        "source_type": "file",
        "connection_config": {},
        "sql_query": None,
        "refresh_interval_days": None,
        "last_synced_at": None,
        "next_sync_at": None,
    }

    if name is not None and name.strip():
        payload["name"] = name.strip()

    try:
        updated = await control_db.data_sources.update(
            session,
            data_source_id,
            payload,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return {"data_source": updated}


@router.patch("/sql")
async def update_sql_data_source(
    data: SQLDataSourceUpdate,
    data_source_id: int = Query(..., gt=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    source = await _owned(
        session,
        data_source_id,
        current_user["user_id"],
    )

    database_url = (
        data.database_url
        if data.database_url is not None
        else _database_url(source)
    )
    query = (
        data.query
        if data.query is not None
        else source.get("sql_query")
    )

    if not database_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database URL is required",
        )

    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SQL query is required",
        )

    refresh_interval_days = (
        data.refresh_interval_days
        if "refresh_interval_days" in data.model_fields_set
        else source.get("refresh_interval_days")
    )

    try:
        snapshot = await sql_query_tool.execute(
            database_url,
            query,
        )
        database_url = sql_query_tool.validate_database_url(
            database_url
        )
        query = sql_query_tool.validate_query(query)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to query external database",
        ) from error

    last_synced_at, next_sync_at = _schedule(
        refresh_interval_days
    )

    payload = {
        "file_name": "PostgreSQL query",
        "file_data": snapshot.rows,
        "row_count": snapshot.row_count,
        "column_count": snapshot.column_count,
        "source_type": "database",
        "connection_config": {
            "database_url": database_url,
        },
        "sql_query": query,
        "refresh_interval_days": refresh_interval_days,
        "last_synced_at": last_synced_at,
        "next_sync_at": next_sync_at,
    }

    try:
        updated = await control_db.data_sources.update(
            session,
            data_source_id,
            payload,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return {"data_source": updated}


@router.post("/sql/execute")
async def execute_saved_sql_query(
    data: SQLDataSourceExecute,
    data_source_id: int = Query(..., gt=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    source = await _owned(
        session,
        data_source_id,
        current_user["user_id"],
    )

    if source.get("source_type") != "database":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data source is not a database source",
        )

    database_url = _database_url(source)
    query = data.query or source.get("sql_query")

    if not database_url or not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database source is missing connection or query",
        )

    try:
        snapshot = await sql_query_tool.execute(
            database_url,
            query,
        )
        query = sql_query_tool.validate_query(query)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to query external database",
        ) from error

    refresh_interval_days = source.get(
        "refresh_interval_days"
    )
    last_synced_at, next_sync_at = _schedule(
        refresh_interval_days
    )

    payload: dict[str, Any] = {
        "file_data": snapshot.rows,
        "row_count": snapshot.row_count,
        "column_count": snapshot.column_count,
        "last_synced_at": last_synced_at,
        "next_sync_at": next_sync_at,
    }

    if data.query is not None and data.save_query:
        payload["sql_query"] = query

    updated = await control_db.data_sources.update(
        session,
        data_source_id,
        payload,
    )

    return {
        "data_source": updated,
        "executed_query": query,
        "saved_query": (
            query
            if data.query is not None and data.save_query
            else source.get("sql_query")
        ),
    }


@router.delete(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete_data_source(
    data_source_id: int = Query(..., gt=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned(
        session,
        data_source_id,
        current_user["user_id"],
    )
    return await control_db.data_sources.delete(
        session,
        data_source_id,
    )
