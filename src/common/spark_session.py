"""Spark session helpers for local and Databricks execution."""

from __future__ import annotations

from delta import pip_utils
from pyspark.sql import SparkSession

from common.windows_hadoop import configure_windows_hadoop

DELTA_SPARK_EXTENSIONS = "io.delta.sql.DeltaSparkSessionExtension"
DELTA_SPARK_CATALOG = "org.apache.spark.sql.delta.catalog.DeltaCatalog"


def _build_spark_session_builder(app_name: str) -> SparkSession.Builder:
    """Build a Spark session builder with project defaults and Delta settings."""
    hadoop_home = configure_windows_hadoop()

    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.driver.memory", "2g")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.sql.extensions", DELTA_SPARK_EXTENSIONS)
        .config("spark.sql.catalog.spark_catalog", DELTA_SPARK_CATALOG)
    )

    if hadoop_home is not None:
        builder = builder.config("spark.hadoop.hadoop.home.dir", str(hadoop_home.resolve()))

    return pip_utils.configure_spark_with_delta_pip(builder)


def create_spark_session(app_name: str = "medallion-pipeline") -> SparkSession:
    """Create a Spark session with Delta Lake support."""
    active_session = SparkSession.getActiveSession()
    if active_session is not None:
        active_session.stop()

    return _build_spark_session_builder(app_name).getOrCreate()
