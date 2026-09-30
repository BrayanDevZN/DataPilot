"""Choose and preserve the dataframe engine for deterministic data tools."""

import polars as pl
from pyspark.sql import DataFrame, SparkSession

from .polars_tool import PolarsTools
from .spark_tools import SparkTools


class DataToolsManager:
    def __init__(
        self,
        data,
        *,
        spark_threshold: int = 100_000,
        spark: SparkSession | None = None,
    ) -> None:
        self.spark = spark or (
            SparkSession.builder
            .appName("DataPilot")
            .getOrCreate()
        )
        self.spark_threshold = spark_threshold
        self.spark_tools = SparkTools(self.spark)
        self.polars_tools = PolarsTools()

        if isinstance(data, DataFrame):
            self.engine = "spark"
            self.data = data
            self.row_count = data.count()
            self._tool = self.spark_tools
            return

        if isinstance(data, pl.LazyFrame):
            self.engine = "polars"
            self.data = data
            self.row_count = (
                data.select(pl.len().alias("__rows"))
                .collect()
                .item()
            )
            self._tool = self.polars_tools
            return

        if isinstance(data, pl.DataFrame):
            self.engine = "polars"
            self.data = data.lazy()
            self.row_count = data.height
            self._tool = self.polars_tools
            return

        if isinstance(data, list):
            self.row_count = len(data)

            if self.row_count >= self.spark_threshold:
                self.engine = "spark"
                self.data = self._records_to_spark(data)
                self._tool = self.spark_tools
            else:
                self.engine = "polars"
                self.data = pl.from_dicts(
                    data,
                    infer_schema_length=None,
                ).lazy()
                self._tool = self.polars_tools
            return

        if hasattr(data, "to_dict"):
            try:
                records = data.to_dict(orient="records")
            except TypeError:
                records = None

            if records is not None:
                self.row_count = len(records)
                if self.row_count >= self.spark_threshold:
                    self.engine = "spark"
                    self.data = self._records_to_spark(records)
                    self._tool = self.spark_tools
                else:
                    self.engine = "polars"
                    self.data = pl.from_dicts(
                        records,
                        infer_schema_length=None,
                    ).lazy()
                    self._tool = self.polars_tools
                return

        raise TypeError("Unsupported data type for DataToolsManager")

    def get_tool(self) -> SparkTools | PolarsTools:
        return self._tool

    def get_data(self) -> DataFrame | pl.LazyFrame:
        return self.data

    def _records_to_spark(self, records: list[dict]) -> DataFrame:
        if not records:
            return self.spark.createDataFrame(
                [],
                schema="value string",
            )
        return self.spark.createDataFrame(records)
