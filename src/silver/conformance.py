"""Silver conformance transformations: trim, cast, and derived measures."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from silver.schemas import DECIMAL_10_2


def _trim_string_columns(df: DataFrame, string_columns: list[str]) -> DataFrame:
    for column in string_columns:
        df = df.withColumn(column, F.trim(F.col(column)))
    return df


def conform_customers(df: DataFrame, string_columns: list[str]) -> DataFrame:
    """Trim strings and cast registration_date to date."""
    conformed = _trim_string_columns(df, string_columns)
    return conformed.withColumn(
        "registration_date",
        F.to_date(F.col("registration_date")),
    )


def conform_products(df: DataFrame, string_columns: list[str]) -> DataFrame:
    """Trim strings and cast list_price and is_active."""
    conformed = _trim_string_columns(df, string_columns)
    return (
        conformed.withColumn("list_price", F.col("list_price").cast(DECIMAL_10_2))
        .withColumn(
            "is_active",
            F.when(F.lower(F.col("is_active")) == "true", F.lit(True))
            .when(F.lower(F.col("is_active")) == "false", F.lit(False))
            .otherwise(F.col("is_active").cast("boolean")),
        )
    )


def conform_orders(df: DataFrame, string_columns: list[str]) -> DataFrame:
    """Trim strings, cast types, and compute line_revenue."""
    conformed = _trim_string_columns(df, string_columns)
    return (
        conformed.withColumn("order_date", F.to_date(F.col("order_date")))
        .withColumn("quantity", F.col("quantity").cast("int"))
        .withColumn("unit_price", F.col("unit_price").cast(DECIMAL_10_2))
        .withColumn(
            "line_revenue",
            (F.col("quantity") * F.col("unit_price")).cast(DECIMAL_10_2),
        )
    )
