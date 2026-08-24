"""Build gold_sales_by_product from Silver products and valid orders."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from gold.schemas import DECIMAL_12_2, SALES_BY_PRODUCT_COLUMNS


def _product_order_aggregates(valid_orders: DataFrame) -> DataFrame:
    return valid_orders.groupBy("product_id").agg(
        F.countDistinct("order_id").alias("total_orders"),
        F.sum("line_revenue").alias("total_revenue"),
    )


def build_sales_by_product(
    silver_products: DataFrame,
    valid_orders: DataFrame,
) -> DataFrame:
    """All Silver products with left-joined valid-order metrics (§10.3)."""
    product_metrics = _product_order_aggregates(valid_orders)

    return (
        silver_products.select("product_id", "product_name", "category")
        .join(product_metrics, on="product_id", how="left")
        .withColumn("total_orders", F.coalesce(F.col("total_orders"), F.lit(0)))
        .withColumn(
            "total_revenue",
            F.coalesce(F.col("total_revenue"), F.lit(0)).cast(DECIMAL_12_2),
        )
        .withColumn(
            "average_order_value",
            F.when(
                F.col("total_orders") > 0,
                (F.col("total_revenue") / F.col("total_orders")).cast(DECIMAL_12_2),
            ),
        )
        .select(*SALES_BY_PRODUCT_COLUMNS)
    )
