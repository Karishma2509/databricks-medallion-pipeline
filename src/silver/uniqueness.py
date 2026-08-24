"""Uniqueness data-quality flags."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def _is_key_unique(df: DataFrame, key_column: str, flag_column: str) -> DataFrame:
    """Flag all rows sharing a duplicated key as non-unique."""
    key_counts = df.groupBy(key_column).agg(F.count("*").alias("_key_count"))
    return (
        df.join(key_counts, on=key_column, how="left")
        .withColumn(flag_column, F.col("_key_count") == 1)
        .drop("_key_count")
    )


def apply_customer_uniqueness(df: DataFrame) -> DataFrame:
    """Add is_customer_id_unique; all rows sharing a key receive false."""
    return _is_key_unique(df, "customer_id", "is_customer_id_unique")


def apply_order_uniqueness(df: DataFrame) -> DataFrame:
    """Add is_order_id_unique; all rows sharing a key receive false."""
    return _is_key_unique(df, "order_id", "is_order_id_unique")
