"""OpenAI function tool for deterministic dataframe analysis."""

from typing import Any

import polars as pl
from pyspark.sql import DataFrame
from pyspark.sql.types import DateType, NumericType, TimestampType

from src.backend.utils.manage import DataToolsManager


ANALYTICS_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "analyze_data",
    "description": (
        "Executa uma operação analítica determinística sobre o dataset atual. "
        "Use esta tool para contagem, agrupamento, série temporal, scatter, KPI, "
        "tabela, filtros e agregações. Use somente colunas existentes no dataset."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "groupby",
                    "count",
                    "time_groupby",
                    "scatter",
                    "kpi",
                    "table",
                ],
                "description": "Operação analítica a executar.",
            },
            "group_by": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Colunas usadas para agrupamento.",
            },
            "metric": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Colunas numéricas usadas como métricas.",
            },
            "aggregation": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "sum",
                        "mean",
                        "avg",
                        "count",
                        "max",
                        "min",
                        "median",
                        "none",
                    ],
                },
                "description": "Agregação aplicada às métricas.",
            },
            "x": {
                "type": ["string", "null"],
                "description": "Coluna do eixo X quando aplicável.",
            },
            "y": {
                "type": ["string", "null"],
                "description": "Coluna do eixo Y quando aplicável.",
            },
            "time_column": {
                "type": ["string", "null"],
                "description": "Coluna temporal usada em time_groupby.",
            },
            "time_freq": {
                "type": "string",
                "enum": ["D", "W", "M", "Q", "Y"],
                "description": "Frequência temporal.",
            },
            "filters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "column": {"type": "string"},
                        "operator": {
                            "type": "string",
                            "enum": ["equals", "not_equals", "contains", "in"],
                        },
                        "value": {},
                    },
                    "required": ["column", "operator", "value"],
                    "additionalProperties": False,
                },
                "description": "Filtros aplicados antes da operação.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 500,
                "description": "Limite máximo de linhas retornadas.",
            },
            "sort": {
                "type": "string",
                "enum": ["asc", "desc", "none"],
                "description": "Ordenação do resultado.",
            },
            "title": {
                "type": "string",
                "description": "Título opcional para identificar o resultado.",
            },
        },
        "required": ["operation"],
        "additionalProperties": False,
    },
}


class AgentDataTools:
    def __init__(
        self,
        data,
        *,
        spark_threshold: int = 100_000,
    ) -> None:
        self.manager = DataToolsManager(
            data,
            spark_threshold=spark_threshold,
        )
        self.tool = self.manager.get_tool()
        self.data = self.manager.get_data()

    @property
    def definition(self) -> dict[str, Any]:
        return ANALYTICS_TOOL

    @property
    def engine(self) -> str:
        return self.manager.engine

    @property
    def row_count(self) -> int:
        return self.manager.row_count

    def dataset_schema(self) -> dict[str, Any]:
        if isinstance(self.data, DataFrame):
            columns = [field.name for field in self.data.schema.fields]
            numeric_columns = [
                field.name
                for field in self.data.schema.fields
                if isinstance(field.dataType, NumericType)
            ]
            datetime_columns = [
                field.name
                for field in self.data.schema.fields
                if isinstance(field.dataType, (DateType, TimestampType))
            ]
            categorical_columns = [
                column
                for column in columns
                if column not in set(numeric_columns + datetime_columns)
            ]
            dtypes = {
                field.name: field.dataType.simpleString()
                for field in self.data.schema.fields
            }
        else:
            schema = self.data.collect_schema()
            columns = schema.names()
            numeric_columns = [
                name
                for name, dtype in schema.items()
                if dtype.is_numeric()
            ]
            datetime_columns = [
                name
                for name, dtype in schema.items()
                if dtype.is_temporal()
            ]
            categorical_columns = [
                column
                for column in columns
                if column not in set(numeric_columns + datetime_columns)
            ]
            dtypes = {
                name: str(dtype)
                for name, dtype in schema.items()
            }

        unique_columns = categorical_columns[:20]
        unique_values = self.tool.unique_values(
            self.data,
            columns=unique_columns,
            limit=12,
        )

        return {
            "columns": columns,
            "dtypes": dtypes,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "datetime_columns": datetime_columns,
            "unique_values": unique_values,
            "row_count": self.row_count,
            "engine": self.engine,
        }

    def execute_many(self, plans: list[dict]) -> list[dict]:
        return self.tool.execute_many(
            self.data,
            plans,
        )

    def execute(self, arguments: dict[str, Any]) -> list[dict]:
        return self.tool.execute(
            self.data,
            arguments,
        )
