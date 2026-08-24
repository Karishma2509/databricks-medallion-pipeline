"""Overall validity flags and dq_failure_reasons assembly."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def _failure_reasons_array(*conditions: tuple[str, str]) -> F.Column:
    """Build an array of issue codes for failed rules."""
    entries = [
        F.when(~F.col(flag_column), F.lit(issue_code)) for issue_code, flag_column in conditions
    ]
    return F.array_compact(F.array(*entries))


def apply_customer_validity(df: DataFrame) -> DataFrame:
    """Compute is_valid_record and dq_failure_reasons for customers."""
    return (
        df.withColumn(
            "is_valid_record",
            F.col("is_email_complete") & F.col("is_customer_id_unique"),
        )
        .withColumn(
            "dq_failure_reasons",
            _failure_reasons_array(
                ("CUST_EMAIL_MISSING", "is_email_complete"),
                ("CUST_ID_DUPLICATE", "is_customer_id_unique"),
            ),
        )
    )


def apply_order_validity(df: DataFrame) -> DataFrame:
    """Compute is_valid_record and dq_failure_reasons for orders."""
    return (
        df.withColumn(
            "is_valid_record",
            F.col("is_customer_id_complete")
            & F.col("is_product_id_complete")
            & F.col("is_order_id_unique")
            & F.col("is_customer_id_valid_ref")
            & F.col("is_product_id_valid_ref"),
        )
        .withColumn(
            "dq_failure_reasons",
            _failure_reasons_array(
                ("ORD_CUST_ID_MISSING", "is_customer_id_complete"),
                ("ORD_PROD_ID_MISSING", "is_product_id_complete"),
                ("ORD_ID_DUPLICATE", "is_order_id_unique"),
                ("ORD_CUST_ID_INVALID", "is_customer_id_valid_ref"),
                ("ORD_PROD_ID_INVALID", "is_product_id_valid_ref"),
            ),
        )
    )


def apply_product_validity(df: DataFrame) -> DataFrame:
    """Products have no DQ rules; is_valid_record is always true."""
    return df.withColumn("is_valid_record", F.lit(True))
