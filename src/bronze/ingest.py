"""Bronze CSV to Delta ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from common.config import BronzeSettings
from bronze.schemas import BRONZE_TABLES, METADATA_COLUMNS


@dataclass(frozen=True)
class BronzeIngestResult:
    dataset: str
    table_name: str
    source_path: Path
    delta_path: Path
    storage_label: str
    source_row_count: int
    bronze_row_count: int


def read_source_csv(
    spark: SparkSession,
    csv_path: str | Path,
    schema: Any,
) -> DataFrame:
    """Read a CSV file with explicit string schema and source fidelity options."""
    return (
        spark.read.option("header", "true")
        .option("mode", "PERMISSIVE")
        .option("emptyValue", "")
        .option("nullValue", "")
        .schema(schema)
        .csv(str(csv_path))
    )


def add_bronze_metadata(
    df: DataFrame,
    source_file: str,
    ingest_batch_id: str,
    ingest_timestamp,
) -> DataFrame:
    """Add approved Bronze metadata columns without altering business values."""
    ordered = df.withColumn("_row_order", F.monotonically_increasing_id())
    window = Window.orderBy("_row_order")

    return (
        ordered.withColumn("_source_row_number", F.row_number().over(window).cast("string"))
        .withColumn("_ingest_batch_id", F.lit(ingest_batch_id))
        .withColumn("_ingest_timestamp", F.lit(ingest_timestamp))
        .withColumn("_source_file", F.lit(source_file))
        .withColumn(
            "_bronze_record_id",
            F.concat(F.col("_source_file"), F.lit("#"), F.col("_source_row_number")),
        )
        .drop("_row_order")
    )


def _write_bronze_table(
    spark: SparkSession,
    bronze_df: DataFrame,
    settings: BronzeSettings,
    table_name: str,
) -> str:
    """Persist Bronze output using path-based or Unity Catalog storage."""
    if settings.is_local:
        delta_path = settings.table_path(table_name)
        delta_path.parent.mkdir(parents=True, exist_ok=True)
        bronze_df.write.format("delta").mode("overwrite").save(str(delta_path))
        return str(delta_path)

    qualified_name = settings.qualified_table_name(table_name)
    bronze_df.write.format("delta").mode("overwrite").saveAsTable(qualified_name)
    return qualified_name


def _read_bronze_row_count(
    spark: SparkSession,
    settings: BronzeSettings,
    table_name: str,
) -> int:
    """Count Bronze rows from the configured storage target."""
    if settings.is_local:
        delta_path = settings.table_path(table_name)
        return spark.read.format("delta").load(str(delta_path)).count()

    return spark.table(settings.qualified_table_name(table_name)).count()


def ingest_dataset(
    spark: SparkSession,
    dataset_key: str,
    settings: BronzeSettings,
) -> BronzeIngestResult:
    """Ingest one source CSV into a Bronze Delta table."""
    definition = BRONZE_TABLES[dataset_key]
    source_file = definition["source_file"]
    table_name = definition["table_name"]
    source_uri = settings.source_csv_uri(source_file)
    source_path = Path(source_uri)

    if settings.is_local and not source_path.exists():
        raise FileNotFoundError(f"Source CSV not found: {source_path}")

    source_df = read_source_csv(spark, source_uri, definition["csv_schema"])
    source_row_count = source_df.count()

    bronze_df = add_bronze_metadata(
        source_df,
        source_file=source_file,
        ingest_batch_id=settings.ingest_batch_id,
        ingest_timestamp=settings.ingest_timestamp,
    )

    column_order = definition["business_columns"] + METADATA_COLUMNS
    bronze_df = bronze_df.select(*column_order)

    storage_label = _write_bronze_table(spark, bronze_df, settings, table_name)
    delta_path = settings.table_path(table_name)

    bronze_row_count = _read_bronze_row_count(spark, settings, table_name)
    if bronze_row_count != source_row_count:
        raise ValueError(
            f"Bronze row count mismatch for {table_name}: "
            f"source={source_row_count}, bronze={bronze_row_count}"
        )

    return BronzeIngestResult(
        dataset=dataset_key,
        table_name=table_name,
        source_path=source_path,
        delta_path=delta_path,
        storage_label=storage_label,
        source_row_count=source_row_count,
        bronze_row_count=bronze_row_count,
    )


def ingest_all_bronze_tables(
    spark: SparkSession,
    settings: BronzeSettings,
) -> list[BronzeIngestResult]:
    """Ingest customers, orders, and products into Bronze Delta tables."""
    results: list[BronzeIngestResult] = []
    for dataset_key in ("customers", "orders", "products"):
        results.append(ingest_dataset(spark, dataset_key, settings))
    return results


def read_bronze_table(spark: SparkSession, settings: BronzeSettings, table_name: str) -> DataFrame:
    """Read a Bronze Delta table from the configured storage target."""
    if settings.is_databricks:
        return spark.table(settings.qualified_table_name(table_name))

    delta_path = settings.table_path(table_name)
    return spark.read.format("delta").load(str(delta_path))
