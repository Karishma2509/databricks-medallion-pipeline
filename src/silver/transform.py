"""Silver entity transformation orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

from bronze.schemas import METADATA_COLUMNS
from common.config import SilverSettings
from silver.completeness import apply_customer_completeness, apply_order_completeness
from silver.conformance import conform_customers, conform_orders, conform_products
from silver.metrics import write_dq_metrics
from silver.referential_integrity import apply_order_referential_integrity
from silver.schemas import SILVER_TABLES
from silver.uniqueness import apply_customer_uniqueness, apply_order_uniqueness
from silver.validity import (
    apply_customer_validity,
    apply_order_validity,
    apply_product_validity,
)


@dataclass(frozen=True)
class SilverTransformResult:
    dataset: str
    table_name: str
    bronze_table_name: str
    delta_path: Path
    storage_label: str
    bronze_row_count: int
    silver_row_count: int


def read_bronze_table(spark: SparkSession, settings: SilverSettings, table_name: str) -> DataFrame:
    """Read a Bronze Delta table from the configured storage target."""
    if settings.is_databricks:
        return spark.table(settings.qualified_bronze_table_name(table_name))

    delta_path = settings.bronze_table_path(table_name)
    return spark.read.format("delta").load(str(delta_path))


def read_silver_table(spark: SparkSession, settings: SilverSettings, table_name: str) -> DataFrame:
    """Read a Silver Delta table from the configured storage target."""
    if settings.is_databricks:
        return spark.table(settings.qualified_silver_table_name(table_name))

    delta_path = settings.silver_table_path(table_name)
    return spark.read.format("delta").load(str(delta_path))


def read_dq_table(spark: SparkSession, settings: SilverSettings, table_name: str) -> DataFrame:
    """Read a DQ metrics Delta table from the configured storage target."""
    if settings.is_databricks:
        return spark.table(settings.qualified_dq_table_name(table_name))

    delta_path = settings.dq_table_path(table_name)
    return spark.read.format("delta").load(str(delta_path))


def _write_silver_table(
    df: DataFrame,
    settings: SilverSettings,
    table_name: str,
    column_order: list[str],
    bronze_row_count: int,
) -> SilverTransformResult:
    output_df = df.select(*column_order)

    if settings.is_local:
        delta_path = settings.silver_table_path(table_name)
        delta_path.parent.mkdir(parents=True, exist_ok=True)
        output_df.write.format("delta").mode("overwrite").save(str(delta_path))
        storage_label = str(delta_path)
    else:
        delta_path = settings.silver_table_path(table_name)
        qualified_name = settings.qualified_silver_table_name(table_name)
        output_df.write.format("delta").mode("overwrite").saveAsTable(qualified_name)
        storage_label = qualified_name

    silver_row_count = output_df.count()
    if silver_row_count != bronze_row_count:
        raise ValueError(
            f"Silver row count mismatch for {table_name}: "
            f"bronze={bronze_row_count}, silver={silver_row_count}"
        )

    dataset_key = table_name.replace("silver_", "")
    return SilverTransformResult(
        dataset=dataset_key,
        table_name=table_name,
        bronze_table_name=f"bronze_{dataset_key}",
        delta_path=delta_path,
        storage_label=storage_label,
        bronze_row_count=bronze_row_count,
        silver_row_count=silver_row_count,
    )


def transform_silver_products(
    spark: SparkSession,
    settings: SilverSettings,
    bronze_products: DataFrame | None = None,
) -> tuple[DataFrame, SilverTransformResult]:
    """Bronze products -> conformance -> validity -> silver_products."""
    definition = SILVER_TABLES["products"]
    bronze_df = bronze_products or read_bronze_table(
        spark, settings, definition["bronze_table_name"]
    )
    bronze_row_count = bronze_df.count()

    conformed = conform_products(bronze_df, definition["string_columns"])
    silver_df = apply_product_validity(conformed)

    column_order = (
        definition["business_columns"] + METADATA_COLUMNS + definition["dq_columns"]
    )
    result = _write_silver_table(
        silver_df,
        settings,
        definition["table_name"],
        column_order,
        bronze_row_count,
    )
    return silver_df, result


def transform_silver_customers(
    spark: SparkSession,
    settings: SilverSettings,
    bronze_customers: DataFrame | None = None,
) -> tuple[DataFrame, SilverTransformResult]:
    """Bronze customers -> conformance -> completeness -> uniqueness -> validity."""
    definition = SILVER_TABLES["customers"]
    bronze_df = bronze_customers or read_bronze_table(
        spark, settings, definition["bronze_table_name"]
    )
    bronze_row_count = bronze_df.count()

    conformed = conform_customers(bronze_df, definition["string_columns"])
    with_completeness = apply_customer_completeness(conformed)
    with_uniqueness = apply_customer_uniqueness(with_completeness)
    silver_df = apply_customer_validity(with_uniqueness)

    column_order = (
        definition["business_columns"] + METADATA_COLUMNS + definition["dq_columns"]
    )
    result = _write_silver_table(
        silver_df,
        settings,
        definition["table_name"],
        column_order,
        bronze_row_count,
    )
    return silver_df, result


def transform_silver_orders(
    spark: SparkSession,
    settings: SilverSettings,
    silver_customers: DataFrame,
    silver_products: DataFrame,
    bronze_orders: DataFrame | None = None,
) -> tuple[DataFrame, SilverTransformResult]:
    """Bronze orders -> conformance -> completeness -> uniqueness -> RI -> validity."""
    definition = SILVER_TABLES["orders"]
    bronze_df = bronze_orders or read_bronze_table(
        spark, settings, definition["bronze_table_name"]
    )
    bronze_row_count = bronze_df.count()

    conformed = conform_orders(bronze_df, definition["string_columns"])
    with_completeness = apply_order_completeness(conformed)
    with_uniqueness = apply_order_uniqueness(with_completeness)
    with_ri = apply_order_referential_integrity(
        with_uniqueness, silver_customers, silver_products
    )
    silver_df = apply_order_validity(with_ri)

    column_order = (
        definition["business_columns"] + METADATA_COLUMNS + definition["dq_columns"]
    )
    result = _write_silver_table(
        silver_df,
        settings,
        definition["table_name"],
        column_order,
        bronze_row_count,
    )
    return silver_df, result


@dataclass(frozen=True)
class SilverPipelineResult:
    entity_results: list[SilverTransformResult]
    dq_metrics_path: Path
    dq_metrics_by_rule_path: Path
    dq_metrics_label: str
    dq_metrics_by_rule_label: str


def transform_all_silver_tables(
    spark: SparkSession,
    settings: SilverSettings,
) -> SilverPipelineResult:
    """Run full Silver pipeline: products -> customers -> orders -> metrics."""
    silver_products, products_result = transform_silver_products(spark, settings)
    silver_customers, customers_result = transform_silver_customers(spark, settings)
    silver_orders, orders_result = transform_silver_orders(
        spark, settings, silver_customers, silver_products
    )

    _, dq_metrics_by_rule = write_dq_metrics(
        spark, settings, silver_customers, silver_orders, silver_products
    )

    return SilverPipelineResult(
        entity_results=[products_result, customers_result, orders_result],
        dq_metrics_path=settings.dq_table_path("dq_metrics"),
        dq_metrics_by_rule_path=settings.dq_table_path("dq_metrics_by_rule"),
        dq_metrics_label=settings.dq_storage_label("dq_metrics"),
        dq_metrics_by_rule_label=settings.dq_storage_label("dq_metrics_by_rule"),
    )
