"""Referential-integrity data-quality flags."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from silver.completeness import _is_present


def apply_order_referential_integrity(
    orders_df: DataFrame,
    customers_df: DataFrame,
    products_df: DataFrame,
) -> DataFrame:
    """Validate order FKs against Silver reference ID sets (existence only).

    RI is evaluated only when the FK value is present. Missing values are
    handled by completeness flags so per-rule failure counts stay disjoint.
    """
    customer_ids = customers_df.select(F.col("customer_id").alias("_ref_customer_id")).distinct()
    product_ids = products_df.select(F.col("product_id").alias("_ref_product_id")).distinct()

    with_customer_ref = (
        orders_df.join(
            customer_ids,
            orders_df["customer_id"] == customer_ids["_ref_customer_id"],
            how="left",
        )
        .withColumn(
            "is_customer_id_valid_ref",
            ~_is_present("customer_id") | F.col("_ref_customer_id").isNotNull(),
        )
        .drop("_ref_customer_id")
    )

    return (
        with_customer_ref.join(
            product_ids,
            with_customer_ref["product_id"] == product_ids["_ref_product_id"],
            how="left",
        )
        .withColumn(
            "is_product_id_valid_ref",
            ~_is_present("product_id") | F.col("_ref_product_id").isNotNull(),
        )
        .drop("_ref_product_id")
    )
