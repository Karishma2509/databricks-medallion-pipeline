"""Build gold_customer_segmentation from gold_revenue_by_customer."""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from gold.schemas import CUSTOMER_SEGMENTATION_COLUMNS, CUSTOMER_SEGMENTS, DECIMAL_12_2


def build_customer_segmentation(
    spark: SparkSession,
    revenue_by_customer: DataFrame,
) -> DataFrame:
    """Aggregate customer Gold by segment; always emit four segment rows."""
    segment_rollups = revenue_by_customer.groupBy("customer_segment").agg(
        F.count("customer_id").alias("customer_count"),
        F.avg("total_revenue").alias("average_revenue"),
        F.sum("total_revenue").alias("total_revenue"),
    )

    segment_dimension = spark.createDataFrame(
        [(segment,) for segment in CUSTOMER_SEGMENTS],
        ["customer_segment"],
    )

    return (
        segment_dimension.join(segment_rollups, on="customer_segment", how="left")
        .withColumn("customer_count", F.coalesce(F.col("customer_count"), F.lit(0)))
        .withColumn(
            "average_revenue",
            F.coalesce(F.col("average_revenue"), F.lit(0)).cast(DECIMAL_12_2),
        )
        .withColumn(
            "total_revenue",
            F.coalesce(F.col("total_revenue"), F.lit(0)).cast(DECIMAL_12_2),
        )
        .select(*CUSTOMER_SEGMENTATION_COLUMNS)
    )
