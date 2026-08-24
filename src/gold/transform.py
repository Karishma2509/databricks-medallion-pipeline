"""Gold pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

from common.config import GoldSettings
from gold.customer_segmentation import build_customer_segmentation
from gold.filters import filter_valid_customers, filter_valid_orders
from gold.revenue_by_customer import build_revenue_by_customer
from gold.sales_by_product import build_sales_by_product
from gold.schemas import GOLD_TABLES


@dataclass(frozen=True)
class GoldTransformResult:
    table_name: str
    delta_path: Path
    row_count: int


@dataclass(frozen=True)
class GoldPipelineResult:
    table_results: list[GoldTransformResult]


def read_silver_table(spark: SparkSession, settings: GoldSettings, table_name: str) -> DataFrame:
    """Read a Silver Delta table from the configured path."""
    delta_path = settings.silver_table_path(table_name)
    return spark.read.format("delta").load(str(delta_path))


def read_gold_table(spark: SparkSession, settings: GoldSettings, table_name: str) -> DataFrame:
    """Read a Gold Delta table from the configured path."""
    delta_path = settings.gold_table_path(table_name)
    return spark.read.format("delta").load(str(delta_path))


def _write_gold_table(
    df: DataFrame,
    settings: GoldSettings,
    table_name: str,
    column_order: list[str],
) -> GoldTransformResult:
    delta_path = settings.gold_table_path(table_name)
    delta_path.parent.mkdir(parents=True, exist_ok=True)

    output_df = df.select(*column_order)
    output_df.write.format("delta").mode("overwrite").save(str(delta_path))

    return GoldTransformResult(
        table_name=table_name,
        delta_path=delta_path,
        row_count=output_df.count(),
    )


def transform_all_gold_tables(
    spark: SparkSession,
    settings: GoldSettings,
    silver_customers: DataFrame | None = None,
    silver_orders: DataFrame | None = None,
    silver_products: DataFrame | None = None,
) -> GoldPipelineResult:
    """Run full Gold pipeline: read Silver -> aggregate -> write Gold tables."""
    customers = silver_customers or read_silver_table(spark, settings, "silver_customers")
    orders = silver_orders or read_silver_table(spark, settings, "silver_orders")
    products = silver_products or read_silver_table(spark, settings, "silver_products")

    valid_orders = filter_valid_orders(orders)
    valid_customers = filter_valid_customers(customers)

    sales_by_product_df = build_sales_by_product(products, valid_orders)
    revenue_by_customer_df = build_revenue_by_customer(
        valid_customers, valid_orders, settings
    )
    customer_segmentation_df = build_customer_segmentation(spark, revenue_by_customer_df)

    results = [
        _write_gold_table(
            sales_by_product_df,
            settings,
            GOLD_TABLES["sales_by_product"]["table_name"],
            GOLD_TABLES["sales_by_product"]["columns"],
        ),
        _write_gold_table(
            revenue_by_customer_df,
            settings,
            GOLD_TABLES["revenue_by_customer"]["table_name"],
            GOLD_TABLES["revenue_by_customer"]["columns"],
        ),
        _write_gold_table(
            customer_segmentation_df,
            settings,
            GOLD_TABLES["customer_segmentation"]["table_name"],
            GOLD_TABLES["customer_segmentation"]["columns"],
        ),
    ]

    return GoldPipelineResult(table_results=results)
