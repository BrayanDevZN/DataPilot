"""Deterministic Polars tools using LazyFrame execution for DataPilot AI agents."""

import re

import polars as pl


class PolarsTools:
    VALID_OPERATIONS = {"groupby", "count", "time_groupby", "scatter", "kpi", "table"}
    VALID_AGGREGATIONS = {"sum", "mean", "avg", "count", "max", "min", "median", "none"}
    VALID_FILTER_OPERATORS = {"equals", "not_equals", "contains", "in"}

    def unique_values(self, df, columns=None, limit: int = 30) -> dict:
        lazy_df = self._normalize_dataframe_columns(self._to_lazyframe(df))
        resolved_columns = self._resolve_columns(lazy_df, columns)

        if not resolved_columns:
            schema = lazy_df.collect_schema()
            resolved_columns = [
                name for name, dtype in schema.items()
                if not dtype.is_numeric()
            ]

        result = {}
        for column in resolved_columns:
            values = (
                lazy_df
                .select(
                    pl.col(column)
                    .drop_nulls()
                    .cast(pl.Utf8, strict=False)
                    .str.strip_chars()
                    .alias(column)
                )
                .filter(pl.col(column) != "")
                .unique(maintain_order=True)
                .limit(limit)
                .collect()
                .to_series()
                .to_list()
            )
            result[column] = values
        return result

    def filter_dataframe(self, df, filters: list[dict]) -> pl.LazyFrame:
        filtered_df = self._normalize_dataframe_columns(self._to_lazyframe(df))

        for filter_spec in filters or []:
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
            series = (
                pl.col(column)
                .cast(pl.Utf8, strict=False)
                .str.strip_chars()
                .fill_null("")
            )

            if operator in {"equals", "in"}:
                filtered_df = filtered_df.filter(series.is_in(clean_values))
            elif operator == "not_equals":
                filtered_df = filtered_df.filter(~series.is_in(clean_values))
            elif operator == "contains":
                pattern = "|".join(re.escape(value) for value in clean_values)
                filtered_df = filtered_df.filter(series.str.contains(f"(?i){pattern}"))

        return filtered_df

    def execute(self, df, plan: dict) -> list[dict]:
        if not isinstance(plan, dict):
            return []

        lazy_df = self.filter_dataframe(df, plan.get("filters") or [])
        operation = plan.get("operation") or "groupby"
        if operation not in self.VALID_OPERATIONS:
            operation = "groupby"

        aggregation = self._first_value(plan.get("aggregation", ["sum"]))
        if aggregation == "avg":
            aggregation = "mean"
        if aggregation not in self.VALID_AGGREGATIONS:
            aggregation = "sum"

        if operation == "count" or aggregation == "count":
            return self._count(lazy_df, plan)
        if operation == "time_groupby":
            return self._time_groupby(lazy_df, plan, aggregation)
        if operation == "scatter":
            return self._scatter(lazy_df, plan)
        if operation == "kpi":
            return self._kpi(lazy_df, plan, aggregation)
        if operation == "table":
            return self._table(lazy_df, plan)

        return self._groupby(lazy_df, plan, aggregation)

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

    def _to_lazyframe(self, df) -> pl.LazyFrame:
        if isinstance(df, pl.LazyFrame):
            return df
        if isinstance(df, pl.DataFrame):
            return df.lazy()
        if df is None:
            return pl.DataFrame().lazy()
        if isinstance(df, list):
            return pl.from_dicts(df, infer_schema_length=None).lazy()
        if hasattr(df, "to_dict"):
            try:
                records = df.to_dict(orient="records")
                return pl.from_dicts(records, infer_schema_length=None).lazy()
            except TypeError:
                pass
        return pl.DataFrame(df).lazy()

    def _normalize_dataframe_columns(self, df: pl.LazyFrame) -> pl.LazyFrame:
        names = df.collect_schema().names()
        rename_map = {name: str(name).strip() for name in names if str(name).strip() != name}
        return df.rename(rename_map) if rename_map else df

    def _columns(self, df: pl.LazyFrame) -> list[str]:
        return df.collect_schema().names()

    def _normalize_name(self, value) -> str:
        return str(value).strip().lower().replace("_", " ")

    def _as_list(self, value) -> list:
        if value is None:
            return []
        if isinstance(value, list):
            return [item for item in value if item is not None and str(item).strip()]
        return [value] if str(value).strip() else []

    def _first_value(self, value):
        values = self._as_list(value)
        return str(values[0]).strip().lower() if values else "none"

    def _find_column(self, df: pl.LazyFrame, column) -> str | None:
        if not column:
            return None
        target = self._normalize_name(column)
        for real_column in self._columns(df):
            if self._normalize_name(real_column) == target:
                return real_column
        return None

    def _resolve_columns(self, df: pl.LazyFrame, columns) -> list[str]:
        resolved = []
        for column in self._as_list(columns):
            real_column = self._find_column(df, column)
            if real_column and real_column not in resolved:
                resolved.append(real_column)
        return resolved

    def _resolve_group_by(self, df: pl.LazyFrame, plan: dict) -> list[str]:
        group_by = self._resolve_columns(df, plan.get("group_by"))
        if group_by:
            return group_by
        x = self._find_column(df, plan.get("x"))
        return [x] if x else []

    def _resolve_metric(self, df: pl.LazyFrame, plan: dict) -> list[str]:
        metric = self._resolve_columns(df, plan.get("metric"))
        if metric:
            return metric
        y = self._find_column(df, plan.get("y"))
        return [y] if y else []

    def _to_numeric(self, df: pl.LazyFrame, columns: list[str]) -> pl.LazyFrame:
        return (
            df.with_columns([
                pl.col(column).cast(pl.Float64, strict=False).alias(column)
                for column in columns
            ])
            .drop_nulls(subset=columns)
        )

    def _limit_value(self, plan: dict, default: int, maximum: int) -> int:
        limit = plan.get("limit", default)
        try:
            limit = int(limit)
        except Exception:
            limit = default
        return max(1, min(limit, maximum))

    def _sort_and_limit(
        self,
        df: pl.LazyFrame,
        y_column: str | None,
        plan: dict,
        default_limit: int = 20,
        maximum: int = 100,
    ) -> pl.LazyFrame:
        sort = plan.get("sort", "desc")
        if y_column and y_column in self._columns(df) and sort in {"asc", "desc"}:
            df = df.sort(y_column, descending=sort == "desc", nulls_last=True)
        return df.limit(self._limit_value(plan, default_limit, maximum))

    def _aggregate_exprs(self, metric: list[str], aggregation: str):
        if aggregation == "mean":
            return [pl.col(column).mean().alias(column) for column in metric]
        if aggregation == "max":
            return [pl.col(column).max().alias(column) for column in metric]
        if aggregation == "min":
            return [pl.col(column).min().alias(column) for column in metric]
        if aggregation == "median":
            return [pl.col(column).median().alias(column) for column in metric]
        return [pl.col(column).sum().alias(column) for column in metric]

    def _collect_dicts(self, df: pl.LazyFrame) -> list[dict]:
        return df.collect().to_dicts()

    def _count(self, df: pl.LazyFrame, plan: dict) -> list[dict]:
        group_by = self._resolve_group_by(df, plan)
        if not group_by:
            raise ValueError("group_by nao encontrado para contagem.")

        result = df.group_by(group_by, maintain_order=True).len(name="Quantidade")
        result = self._sort_and_limit(result, "Quantidade", plan, 20)
        return self._collect_dicts(result)

    def _groupby(self, df: pl.LazyFrame, plan: dict, aggregation: str) -> list[dict]:
        group_by = self._resolve_group_by(df, plan)
        if not group_by:
            raise ValueError("group_by nao encontrado para groupby.")

        metric = self._resolve_metric(df, plan)
        if not metric:
            raise ValueError("metric nao encontrada para groupby.")

        if aggregation in {"none", "count"}:
            aggregation = "sum"

        temp_df = self._to_numeric(df, metric)
        result = temp_df.group_by(group_by, maintain_order=True).agg(
            self._aggregate_exprs(metric, aggregation)
        )
        result = self._sort_and_limit(result, metric[0], plan, 20)
        return self._collect_dicts(result)

    def _datetime_expr(self, column: str) -> pl.Expr:
        text = pl.col(column).cast(pl.Utf8, strict=False)
        return pl.coalesce([
            pl.col(column).cast(pl.Datetime, strict=False),
            text.str.to_datetime(strict=False),
            text.str.to_date(strict=False).cast(pl.Datetime),
        ])

    def _period_expr(self, column: str, time_freq: str) -> pl.Expr:
        value = pl.col(column)
        if time_freq == "D":
            return value.dt.strftime("%Y-%m-%d")
        if time_freq == "W":
            return value.dt.truncate("1w").dt.strftime("%Y-%m-%d")
        if time_freq == "Q":
            return pl.concat_str([
                value.dt.year().cast(pl.Utf8),
                pl.lit("-Q"),
                value.dt.quarter().cast(pl.Utf8),
            ])
        if time_freq == "Y":
            return value.dt.strftime("%Y")
        return value.dt.strftime("%Y-%m")

    def _time_groupby(self, df: pl.LazyFrame, plan: dict, aggregation: str) -> list[dict]:
        time_column = self._find_column(df, plan.get("time_column")) or self._find_column(df, plan.get("x"))
        if not time_column:
            raise ValueError("time_column nao encontrada para time_groupby.")

        time_freq = plan.get("time_freq", "M")
        if time_freq not in {"D", "W", "M", "Q", "Y"}:
            time_freq = "M"

        temp_df = (
            df.with_columns(self._datetime_expr(time_column).alias("__time_column"))
            .drop_nulls(subset=["__time_column"])
            .with_columns(self._period_expr("__time_column", time_freq).alias("Periodo"))
        )

        group_columns = ["Periodo"]
        extra_group_by = self._resolve_columns(temp_df, plan.get("group_by"))
        group_columns.extend([
            column for column in extra_group_by
            if column not in {time_column, "Periodo"}
        ])

        if aggregation == "count":
            result = temp_df.group_by(group_columns, maintain_order=True).len(name="Quantidade")
        else:
            metric = self._resolve_metric(temp_df, plan)
            if not metric:
                raise ValueError("metric nao encontrada para time_groupby.")

            if aggregation == "none":
                aggregation = "sum"

            result = (
                self._to_numeric(temp_df, metric)
                .group_by(group_columns, maintain_order=True)
                .agg(self._aggregate_exprs(metric, aggregation))
            )

        result = result.sort("Periodo").limit(100)

        if len(group_columns) > 1:
            result = result.with_columns(
                pl.concat_str(
                    [
                        pl.col(column).cast(pl.Utf8, strict=False).fill_null("")
                        for column in group_columns
                    ],
                    separator=" | ",
                ).alias("label")
            )
        else:
            result = result.with_columns(pl.col("Periodo").cast(pl.Utf8).alias("label"))

        return self._collect_dicts(result)

    def _scatter(self, df: pl.LazyFrame, plan: dict) -> list[dict]:
        x = self._find_column(df, plan.get("x"))
        y = self._find_column(df, plan.get("y"))
        if not x or not y:
            raise ValueError("x ou y nao encontrado para scatter.")

        temp_df = self._to_numeric(df, [x, y]).select([x, y])
        return self._collect_dicts(
            temp_df.limit(self._limit_value(plan, 100, 500))
        )

    def _kpi(self, df: pl.LazyFrame, plan: dict, aggregation: str) -> list[dict]:
        metric = self._resolve_metric(df, plan)
        if not metric:
            raise ValueError("metric nao encontrada para kpi.")

        column = metric[0]
        temp_df = self._to_numeric(df, [column])

        if aggregation == "mean":
            expr = pl.col(column).mean()
        elif aggregation == "max":
            expr = pl.col(column).max()
        elif aggregation == "min":
            expr = pl.col(column).min()
        elif aggregation == "median":
            expr = pl.col(column).median()
        elif aggregation == "count":
            expr = pl.col(column).count()
        else:
            expr = pl.col(column).sum()

        value = temp_df.select(expr.alias("value")).collect().item()
        return [{"label": plan.get("title", column), column: value}]

    def _table(self, df: pl.LazyFrame, plan: dict) -> list[dict]:
        return self._collect_dicts(
            df.limit(self._limit_value(plan, 50, 200))
        )
