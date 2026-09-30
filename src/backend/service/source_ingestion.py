"""Read uploaded datasets and execute persisted read-only SQL sources."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Any

import polars as pl
import sqlglot
from sqlalchemy import text
from sqlalchemy.engine import make_url

from src.backend.infra.manage import infra


@dataclass(frozen=True)
class DataSnapshot:
    rows: list[dict[str, Any]]
    row_count: int
    column_count: int


class DataFileReader:
    MAX_FILE_BYTES = 25 * 1024 * 1024
    SUPPORTED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls", ".parquet"}

    def _extension(self, filename: str) -> str:
        clean = str(filename or "").strip().lower()
        for extension in self.SUPPORTED_EXTENSIONS:
            if clean.endswith(extension):
                return extension
        raise ValueError(
            "Unsupported file type. Use CSV, JSON, XLS, XLSX or Parquet"
        )

    def _records(self, frame: pl.DataFrame) -> DataSnapshot:
        rows = json.loads(
            json.dumps(
                frame.to_dicts(),
                default=str,
                ensure_ascii=False,
            )
        )
        return DataSnapshot(
            rows=rows,
            row_count=frame.height,
            column_count=frame.width,
        )

    def _read_csv(self, content: bytes) -> pl.DataFrame:
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            decoded = content.decode("latin-1")

        sample = decoded[:8192]
        try:
            separator = csv.Sniffer().sniff(
                sample,
                delimiters=",;\t|",
            ).delimiter
        except csv.Error:
            separator = ","

        return pl.read_csv(
            io.StringIO(decoded),
            separator=separator,
            infer_schema_length=10_000,
            try_parse_dates=True,
        )

    def _read_json(self, content: bytes) -> pl.DataFrame:
        try:
            payload = json.loads(content.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Invalid JSON file") from error

        if isinstance(payload, list):
            if not all(isinstance(item, dict) for item in payload):
                raise ValueError("JSON dataset must be a list of objects")
            return pl.from_dicts(payload, infer_schema_length=None)

        if isinstance(payload, dict):
            for key in ("data", "items", "rows", "results"):
                value = payload.get(key)
                if isinstance(value, list) and all(
                    isinstance(item, dict) for item in value
                ):
                    return pl.from_dicts(value, infer_schema_length=None)
            return pl.from_dicts([payload], infer_schema_length=None)

        raise ValueError("JSON dataset must contain objects")

    def read(self, filename: str, content: bytes) -> DataSnapshot:
        if not content:
            raise ValueError("Uploaded file is empty")

        if len(content) > self.MAX_FILE_BYTES:
            raise ValueError("Uploaded file exceeds the 25 MiB limit")

        extension = self._extension(filename)

        try:
            if extension == ".csv":
                frame = self._read_csv(content)
            elif extension == ".json":
                frame = self._read_json(content)
            elif extension in {".xlsx", ".xls"}:
                frame = pl.read_excel(io.BytesIO(content))
            else:
                frame = pl.read_parquet(io.BytesIO(content))
        except ValueError:
            raise
        except Exception as error:
            raise ValueError("Unable to read uploaded dataset") from error

        if frame.width == 0:
            raise ValueError("Dataset does not contain columns")

        return self._records(frame)


class SQLQueryTool:
    MAX_ROWS = 50_000
    FORBIDDEN_NODE_KEYS = {
        "insert",
        "update",
        "delete",
        "create",
        "drop",
        "alter",
        "merge",
        "command",
        "transaction",
        "grant",
        "revoke",
        "copy",
        "truncate",
    }

    def validate_query(self, query: str) -> str:
        query = str(query or "").strip()
        if not query:
            raise ValueError("SQL query is required")

        try:
            statements = sqlglot.parse(query, read="postgres")
        except Exception as error:
            raise ValueError("Invalid PostgreSQL query") from error

        statements = [
            statement
            for statement in statements
            if statement is not None
        ]

        if len(statements) != 1:
            raise ValueError("Only one SQL statement is allowed")

        statement = statements[0]
        keys = {
            str(getattr(node, "key", "")).lower()
            for node in statement.walk()
        }

        if keys & self.FORBIDDEN_NODE_KEYS:
            raise ValueError("Only read-only SQL queries are allowed")

        if "select" not in keys:
            raise ValueError("SQL query must read data with SELECT")

        return query.rstrip(";")

    def validate_database_url(self, database_url: str) -> str:
        try:
            url = make_url(str(database_url).strip())
        except Exception as error:
            raise ValueError("Invalid database URL") from error

        if url.get_backend_name() not in {"postgres", "postgresql"}:
            raise ValueError("Only PostgreSQL data sources are supported")

        if not url.host or not url.database or not url.username:
            raise ValueError(
                "Database URL must contain host, database and username"
            )

        return str(database_url).strip()

    async def execute(
        self,
        database_url: str,
        query: str,
    ) -> DataSnapshot:
        database_url = self.validate_database_url(database_url)
        query = self.validate_query(query)

        connection = infra.external_database(
            database_url,
            connect_args={"connect_timeout": 10},
        )

        try:
            async with connection.connect() as external:
                async with external.begin():
                    await external.execute(
                        text("SET TRANSACTION READ ONLY")
                    )
                    await external.execute(
                        text("SET LOCAL statement_timeout = '15000ms'")
                    )
                    result = await external.execute(text(query))
                    mappings = result.mappings().fetchmany(
                        self.MAX_ROWS + 1
                    )

            if len(mappings) > self.MAX_ROWS:
                raise ValueError(
                    f"SQL result exceeds {self.MAX_ROWS} rows"
                )

            rows = json.loads(
                json.dumps(
                    [dict(row) for row in mappings],
                    default=str,
                    ensure_ascii=False,
                )
            )

            columns = len(result.keys()) if result.returns_rows else 0

            return DataSnapshot(
                rows=rows,
                row_count=len(rows),
                column_count=columns,
            )
        finally:
            await connection.close()


file_reader = DataFileReader()
sql_query_tool = SQLQueryTool()
