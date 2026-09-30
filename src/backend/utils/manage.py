"""Choose the dataframe engine based on dataset size.

Data always enters through Spark first so the row count is measured consistently.
Small datasets are converted to Polars LazyFrame; large datasets stay in Spark.
"""

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

        self.spark_data = self._to_spark(data)
        self.row_count = self.spark_data.count()

        if self.row_count >= self.spark_threshold:
            self.engine = "spark"
            self.data = self.spark_data
            self._tool = self.spark_tools
        else:
            self.engine = "polars"
            self.data = self._to_polars_lazy(self.spark_data)
            self._tool = self.polars_tools

    def get_tool(self) -> SparkTools | PolarsTools:
        return self._tool

    def get_data(self) -> DataFrame | pl.LazyFrame:
        return self.data

    def _to_spark(self, data) -> DataFrame:
        if isinstance(data, DataFrame):
            return data

        if isinstance(data, pl.LazyFrame):
            data = data.collect()

        if isinstance(data, pl.DataFrame):
            records = data.to_dicts()
            if not records:
                return self.spark.createDataFrame([], schema="value string")
            return self.spark.createDataFrame(records)

        if isinstance(data, list):
            if not data:
                return self.spark.createDataFrame([], schema="value string")
            return self.spark.createDataFrame(data)

        if hasattr(data, "to_dict"):
            try:
                records = data.to_dict(orient="records")
                if not records:
                    return self.spark.createDataFrame([], schema="value string")
                return self.spark.createDataFrame(records)
            except TypeError:
                pass

        raise TypeError("Unsupported data type for DataToolsManager")

    def _to_polars_lazy(self, data: DataFrame) -> pl.LazyFrame:
        records = [row.asDict(recursive=True) for row in data.collect()]
        return pl.from_dicts(records, infer_schema_length=None).lazy()
