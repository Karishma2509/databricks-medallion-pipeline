"""Silver validity filters for Gold aggregations."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def filter_valid_orders(orders_df: DataFrame) -> DataFrame:
    """Return only orders where Silver is_valid_record is true."""
    return orders_df.filter(F.col("is_valid_record"))


def filter_valid_customers(customers_df: DataFrame) -> DataFrame:
    """Return only customers where Silver is_valid_record is true."""
    return customers_df.filter(F.col("is_valid_record"))
