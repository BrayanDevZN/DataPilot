"""Deterministic PySpark tools mirroring PolarsTools for DataPilot AI agents."""

import re
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import NumericType


class SparkTools:
    VALID_OPERATIONS = {
        "groupby",
        "count",
        "time_groupby",
        "scatter",
        "kpi",
        "table",
    }

    VALID_AGGREGATIONS = {
        "sum",
        "mean",
        "avg",
        "count",
        "max",
        "min",
        "median",
        "none",
    }

    VALID_FILTER_OPERATORS = {
        "equals",
        "not_equals",
        "contains",
        "in",
    }

    def __init__(self, spark: SparkSession) -> None:
        if not isinstance(spark, SparkSession):
            raise TypeError("SparkTools requires a SparkSession")
        self.spark = spark

    def unique_values(self, df, columns=None, limit: int = 30) -> dict:
        if self._is_empty(df):
            return {}

        temp_df = self._normalize_dataframe_columns(self._to_dataframe(df))
        resolved_columns = self._resolve_columns(temp_df, columns)

        if not resolved_columns:
            resolved_columns = [
                field.name
                for field in temp_df.schema.fields
                if not isinstance(field.dataType, NumericType)
            ]

        result: dict[str, list[Any]] = {}

        for column in resolved_columns:
            rows = (
                temp_df
                .select(F.trim(F.col(column).cast("string")).alias(column))
                .where(F.col(column).isNotNull() & (F.col(column) != ""))
                .dropDuplicates([column])
                .limit(limit)
                .collect()
            )
            result[column] = [row[column] for row in rows]

        return result

    def filter_dataframe(self, df, filters: list[dict]) -> DataFrame:
        filtered_df = self._normalize_dataframe_columns(self._to_dataframe(df))
        if not filters:
            return filtered_df

        for filter_spec in filters:
            if not isinstance(filter_spec, dict):
                continue

            column = self._find_column(filtered_df, filter_spec.get("column"))
            if not column:
                continue

            operator = str(filter_spec.get("operator") or "equals").strip().lower()
            if operator not in self.VALID_FILTER_OPERATORS:
                operator = "equals"

            values = self._as_list(filter_spec.get("value"))
            if not values:
                continue

            clean_values = [str(value).strip() for value in values]
            series = F.trim(F.coalesce(F.col(column).cast("string"), F.lit("")))

            if operator in {"equals", "in"}:
                filtered_df = filtered_df.filter(series.isin(clean_values))
            elif operator == "not_equals":
                filtered_df = filtered_df.filter(~series.isin(clean_values))
            elif operator == "contains":
                pattern = "|".join(re.escape(value) for value in clean_values)
                filtered_df = filtered_df.filter(series.rlike(f"(?i){pattern}"))

        return filtered_df

    def execute(self, df, plan: dict) -> list[dict]:
        if not isinstance(plan, dict):
            return []

        temp_df = self._normalize_dataframe_columns(self._to_dataframe(df))
        if self._is_empty(temp_df):
            return []

        temp_df = self.filter_dataframe(temp_df, plan.get("filters") or [])
        if self._is_empty(temp_df):
            return []

        operation = plan.get("operation") or "groupby"
        if operation not in self.VALID_OPERATIONS:
            operation = "groupby"

        aggregation = self._first_value(plan.get("aggregation", ["sum"]))
        if aggregation == "avg":
            aggregation = "mean"
        if aggregation not in self.VALID_AGGREGATIONS:
            aggregation = "sum"

        if operation == "count" or aggregation == "count":
            return self._count(temp_df, plan)
        if operation == "time_groupby":
            return self._time_groupby(temp_df, plan, aggregation)
        if operation == "scatter":
            return self._scatter(temp_df, plan)
        if operation == "kpi":
            return self._kpi(temp_df, plan, aggregation)
        if operation == "table":
            return self._table(temp_df, plan)

        return self._groupby(temp_df, plan, aggregation)

    def execute_many(self, df, plans: list[dict]) -> list[dict]:
        results = []

        for index, plan in enumerate(plans or []):
            try:
                metrics = self.execute(df=df, plan=plan)
                results.append({
                    "id": f"chart_{index + 1}",
                    "title": plan.get("title", f"Grafico {index + 1}"),
                    "chart_type": plan.get("chart_type", "bar") if metrics else "none",
                    "operation": plan.get("operation"),
                    "x": plan.get("x"),
                    "y": plan.get("y"),
                    "metric": plan.get("metric"),
                    "group_by": plan.get("group_by"),
                    "aggregation": plan.get("aggregation"),
                    "reason": plan.get("reason", "") if metrics else "Nao foi possivel gerar dados para este grafico.",
                    "data": metrics,
                })
            except Exception as error:
                results.append({
                    "id": f"chart_{index + 1}",
                    "title": plan.get("title", f"Grafico {index + 1}"),
                    "chart_type": "none",
                    "operation": plan.get("operation"),
                    "x": plan.get("x"),
                    "y": plan.get("y"),
                    "metric": plan.get("metric"),
                    "group_by": plan.get("group_by"),
                    "aggregation": plan.get("aggregation"),
                    "reason": str(error),
                    "data": [],
                })

        return results

    def _to_dataframe(self, df) -> DataFrame:
        if isinstance(df, DataFrame):
            return df
        if df is None:
            return self.spark.createDataFrame([], schema="value string")
        if isinstance(df, list):
            if not df:
                return self.spark.createDataFrame([], schema="value string")
            return self.spark.createDataFrame(df)
        if hasattr(df, "to_dict"):
            try:
                records = df.to_dict(orient="records")
                if not records:
                    return self.spark.createDataFrame([], schema="value string")
                return self.spark.createDataFrame(records)
            except TypeError:
                pass
        raise TypeError("Unsupported dataframe type for SparkTools")

    def _is_empty(self, df) -> bool:
        if df is None:
            return True
        if isinstance(df, list):
            return not df
        if isinstance(df, DataFrame):
            return df.limit(1).count() == 0

        empty = getattr(df, "empty", None)
        if isinstance(empty, bool):
            return empty

        return False

    def _normalize_dataframe_columns(self, df: DataFrame) -> DataFrame:
        normalized = df
        for column in df.columns:
            stripped = str(column).strip()
            if stripped != column:
                normalized = normalized.withColumnRenamed(column, stripped)
        return normalized

    def _normalize_name(self, value) -> str:
        return str(value).strip().lower().replace("_", " ")

    def _as_list(self, value) -> list:
        if value is None:
            return []
        if isinstance(value, list):
            return [
                item for item in value
                if item is not None and str(item).strip()
            ]
        return [value] if str(value).strip() else []

    def _first_value(self, value):
        values = self._as_list(value)
        return str(values[0]).strip().lower() if values else "none"

    def _find_column(self, df: DataFrame, column) -> str | None:
        if not column:
            return None

        target = self._normalize_name(column)
        for real_column in df.columns:
            if self._normalize_name(real_column) == target:
                return real_column
        return None

    def _resolve_columns(self, df: DataFrame, columns) -> list[str]:
        resolved = []
        for column in self._as_list(columns):
            real_column = self._find_column(df, column)
            if real_column and real_column not in resolved:
                resolved.append(real_column)
        return resolved

    def _resolve_group_by(self, df: DataFrame, plan: dict) -> list[str]:
        group_by = self._resolve_columns(df, plan.get("group_by"))
        if group_by:
            return group_by

        x = self._find_column(df, plan.get("x"))
        return [x] if x else []

    def _resolve_metric(self, df: DataFrame, plan: dict) -> list[str]:
        metric = self._resolve_columns(df, plan.get("metric"))
        if metric:
            return metric

        y = self._find_column(df, plan.get("y"))
        return [y] if y else []

    def _to_numeric(self, df: DataFrame, columns: list[str]) -> DataFrame:
        temp_df = df
        for column in columns:
            temp_df = temp_df.withColumn(column, F.col(column).cast("double"))
        return temp_df.dropna(subset=columns)

    def _limit_value(self, plan: dict, default: int, maximum: int) -> int:
        limit = plan.get("limit", default)
        try:
            limit = int(limit)
        except Exception:
            limit = default
        return max(1, min(limit, maximum))

    def _sort_and_limit(
        self,
        df: DataFrame,
        y_column: str | None,
        plan: dict,
        default_limit: int = 20,
        maximum: int = 100,
    ) -> DataFrame:
        sort = plan.get("sort", "desc")
        if y_column and y_column in df.columns and sort in {"asc", "desc"}:
            df = df.orderBy(
                F.col(y_column).asc_nulls_last()
                if sort == "asc"
                else F.col(y_column).desc_nulls_last()
            )

        return df.limit(self._limit_value(plan, default_limit, maximum))

    def _aggregate_exprs(self, metric: list[str], aggregation: str):
        if aggregation == "mean":
            return [F.avg(column).alias(column) for column in metric]
        if aggregation == "max":
            return [F.max(column).alias(column) for column in metric]
        if aggregation == "min":
            return [F.min(column).alias(column) for column in metric]
        if aggregation == "median":
            return [F.percentile_approx(column, 0.5).alias(column) for column in metric]
        return [F.sum(column).alias(column) for column in metric]

    def _collect_dicts(self, df: DataFrame) -> list[dict]:
        return [row.asDict(recursive=True) for row in df.collect()]

    def _count(self, df: DataFrame, plan: dict) -> list[dict]:
        group_by = self._resolve_group_by(df, plan)
        if not group_by:
            raise ValueError("group_by nao encontrado para contagem.")

        result = df.groupBy(*group_by).agg(F.count(F.lit(1)).alias("Quantidade"))
        result = self._sort_and_limit(result, "Quantidade", plan, 20)
        return self._collect_dicts(result)

    def _groupby(self, df: DataFrame, plan: dict, aggregation: str) -> list[dict]:
        group_by = self._resolve_group_by(df, plan)
        if not group_by:
            raise ValueError("group_by nao encontrado para groupby.")

        metric = self._resolve_metric(df, plan)
        if not metric:
            raise ValueError("metric nao encontrada para groupby.")

        if aggregation in {"none", "count"}:
            aggregation = "sum"

        temp_df = self._to_numeric(df, metric)
        if self._is_empty(temp_df):
            return []

        result = temp_df.groupBy(*group_by).agg(*self._aggregate_exprs(metric, aggregation))
        sort_column = metric[0] if metric else None
        result = self._sort_and_limit(result, sort_column, plan, 20)
        return self._collect_dicts(result)

    def _time_groupby(self, df: DataFrame, plan: dict, aggregation: str) -> list[dict]:
        time_column = (
            self._find_column(df, plan.get("time_column"))
            or self._find_column(df, plan.get("x"))
        )
        if not time_column:
            raise ValueError("time_column nao encontrada para time_groupby.")

        time_freq = plan.get("time_freq", "M")
        if time_freq not in {"D", "W", "M", "Q", "Y"}:
            time_freq = "M"

        temp_df = df.withColumn(
            "__time_column",
            F.coalesce(
                F.col(time_column).cast("timestamp"),
                F.to_timestamp(F.col(time_column).cast("string")),
                F.to_date(F.col(time_column).cast("string")).cast("timestamp"),
            ),
        ).dropna(subset=["__time_column"])

        if self._is_empty(temp_df):
            return []

        if time_freq == "D":
            period = F.date_format("__time_column", "yyyy-MM-dd")
        elif time_freq == "W":
            period = F.date_format(F.date_trunc("week", "__time_column"), "yyyy-MM-dd")
        elif time_freq == "Q":
            period = F.concat(
                F.year("__time_column").cast("string"),
                F.lit("-Q"),
                F.quarter("__time_column").cast("string"),
            )
        elif time_freq == "Y":
            period = F.date_format("__time_column", "yyyy")
        else:
            period = F.date_format("__time_column", "yyyy-MM")

        temp_df = temp_df.withColumn("Periodo", period)

        group_columns = ["Periodo"]
        extra_group_by = self._resolve_columns(temp_df, plan.get("group_by"))
        group_columns.extend([
            column for column in extra_group_by
            if column not in {time_column, "Periodo"}
        ])

        if aggregation == "count":
            result = temp_df.groupBy(*group_columns).agg(F.count(F.lit(1)).alias("Quantidade"))
        else:
            metric = self._resolve_metric(temp_df, plan)
            if not metric:
                raise ValueError("metric nao encontrada para time_groupby.")

            if aggregation == "none":
                aggregation = "sum"

            temp_df = self._to_numeric(temp_df, metric)
            if self._is_empty(temp_df):
                return []

            result = temp_df.groupBy(*group_columns).agg(
                *self._aggregate_exprs(metric, aggregation)
            )

        result = result.orderBy(F.col("Periodo").asc()).limit(100)

        if len(group_columns) > 1:
            result = result.withColumn(
                "label",
                F.concat_ws(
                    " | ",
                    *[
                        F.coalesce(F.col(column).cast("string"), F.lit(""))
                        for column in group_columns
                    ],
                ),
            )
        else:
            result = result.withColumn("label", F.col("Periodo").cast("string"))

        return self._collect_dicts(result)

    def _scatter(self, df: DataFrame, plan: dict) -> list[dict]:
        x = self._find_column(df, plan.get("x"))
        y = self._find_column(df, plan.get("y"))
        if not x or not y:
            raise ValueError("x ou y nao encontrado para scatter.")

        temp_df = self._to_numeric(df, [x, y])
        if self._is_empty(temp_df):
            return []

        return self._collect_dicts(
            temp_df.select(x, y).limit(self._limit_value(plan, 100, 500))
        )

    def _kpi(self, df: DataFrame, plan: dict, aggregation: str) -> list[dict]:
        metric = self._resolve_metric(df, plan)
        if not metric:
            raise ValueError("metric nao encontrada para kpi.")

        column = metric[0]
        temp_df = self._to_numeric(df, [column])
        if self._is_empty(temp_df):
            return []

        if aggregation == "mean":
            expression = F.avg(column)
        elif aggregation == "max":
            expression = F.max(column)
        elif aggregation == "min":
            expression = F.min(column)
        elif aggregation == "median":
            expression = F.percentile_approx(column, 0.5)
        elif aggregation == "count":
            expression = F.count(column)
        else:
            expression = F.sum(column)

        value = temp_df.select(expression.alias("value")).first()["value"]
        return [{"label": plan.get("title", column), column: value}]

    def _table(self, df: DataFrame, plan: dict) -> list[dict]:
        return self._collect_dicts(
            df.limit(self._limit_value(plan, 50, 200))
        )
