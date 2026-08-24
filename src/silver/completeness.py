"""Completeness data-quality flags."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def _is_present(column_name: str):
    """True when the column is not null and not blank after trim."""
    return F.col(column_name).isNotNull() & (F.trim(F.col(column_name)) != "")


def apply_customer_completeness(df: DataFrame) -> DataFrame:
    """Add is_email_complete to customer records."""
    return df.withColumn("is_email_complete", _is_present("email"))


def apply_order_completeness(df: DataFrame) -> DataFrame:
    """Add customer_id and product_id completeness flags to order records."""
    return df.withColumn("is_customer_id_complete", _is_present("customer_id")).withColumn(
        "is_product_id_complete", _is_present("product_id")
    )
