"""Build gold_revenue_by_customer from valid customers and valid orders."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from common.config import GoldSettings
from gold.schemas import (
    DECIMAL_12_2,
    REVENUE_BY_CUSTOMER_COLUMNS,
    SEGMENT_HIGH_VALUE,
    SEGMENT_LOW_VALUE,
    SEGMENT_MID_VALUE,
    SEGMENT_NO_PURCHASE,
)


def _customer_order_aggregates(valid_orders: DataFrame) -> DataFrame:
    return valid_orders.groupBy("customer_id").agg(
        F.countDistinct("order_id").alias("total_orders"),
        F.sum("line_revenue").alias("total_revenue"),
    )


def assign_customer_segment(total_revenue_col: str, settings: GoldSettings) -> F.Column:
    """Map total_revenue to approved segment labels."""
    revenue = F.col(total_revenue_col)
    return (
        F.when(revenue == 0, F.lit(SEGMENT_NO_PURCHASE))
        .when(
            (revenue > 0) & (revenue < settings.segment_low_max),
            F.lit(SEGMENT_LOW_VALUE),
        )
        .when(
            (revenue >= settings.segment_low_max) & (revenue < settings.segment_mid_max),
            F.lit(SEGMENT_MID_VALUE),
        )
        .when(revenue >= settings.segment_mid_max, F.lit(SEGMENT_HIGH_VALUE))
    )


def build_revenue_by_customer(
    valid_customers: DataFrame,
    valid_orders: DataFrame,
    settings: GoldSettings,
) -> DataFrame:
    """Valid customers with order metrics, segment, and lifetime_value_actual."""
    customer_metrics = _customer_order_aggregates(valid_orders)

    return (
        valid_customers.select("customer_id", "customer_name")
        .join(customer_metrics, on="customer_id", how="left")
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
        .withColumn("customer_segment", assign_customer_segment("total_revenue", settings))
        .withColumn("lifetime_value_actual", F.col("total_revenue"))
        .select(*REVENUE_BY_CUSTOMER_COLUMNS)
    )
