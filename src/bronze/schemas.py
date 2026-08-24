"""Explicit Bronze CSV schemas (all business columns as strings)."""

from __future__ import annotations

from pyspark.sql.types import (
    StringType,
    StructField,
    StructType,
    TimestampType,
)

CUSTOMER_BUSINESS_COLUMNS = [
    "customer_id",
    "customer_name",
    "email",
    "registration_date",
    "country",
    "signup_channel",
]

ORDER_BUSINESS_COLUMNS = [
    "order_id",
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "unit_price",
]

PRODUCT_BUSINESS_COLUMNS = [
    "product_id",
    "product_name",
    "category",
    "list_price",
    "is_active",
]

METADATA_COLUMNS = [
    "_ingest_batch_id",
    "_ingest_timestamp",
    "_source_file",
    "_source_row_number",
    "_bronze_record_id",
]


def _string_fields(columns: list[str]) -> list[StructField]:
    return [StructField(column, StringType(), True) for column in columns]


CUSTOMER_CSV_SCHEMA = StructType(_string_fields(CUSTOMER_BUSINESS_COLUMNS))
ORDER_CSV_SCHEMA = StructType(_string_fields(ORDER_BUSINESS_COLUMNS))
PRODUCT_CSV_SCHEMA = StructType(_string_fields(PRODUCT_BUSINESS_COLUMNS))

CUSTOMER_BRONZE_SCHEMA = StructType(
    _string_fields(CUSTOMER_BUSINESS_COLUMNS)
    + [
        StructField("_ingest_batch_id", StringType(), False),
        StructField("_ingest_timestamp", TimestampType(), False),
        StructField("_source_file", StringType(), False),
        StructField("_source_row_number", StringType(), False),
        StructField("_bronze_record_id", StringType(), False),
    ]
)

ORDER_BRONZE_SCHEMA = StructType(
    _string_fields(ORDER_BUSINESS_COLUMNS)
    + [
        StructField("_ingest_batch_id", StringType(), False),
        StructField("_ingest_timestamp", TimestampType(), False),
        StructField("_source_file", StringType(), False),
        StructField("_source_row_number", StringType(), False),
        StructField("_bronze_record_id", StringType(), False),
    ]
)

PRODUCT_BRONZE_SCHEMA = StructType(
    _string_fields(PRODUCT_BUSINESS_COLUMNS)
    + [
        StructField("_ingest_batch_id", StringType(), False),
        StructField("_ingest_timestamp", TimestampType(), False),
        StructField("_source_file", StringType(), False),
        StructField("_source_row_number", StringType(), False),
        StructField("_bronze_record_id", StringType(), False),
    ]
)

BRONZE_TABLES = {
    "customers": {
        "source_file": "customers.csv",
        "table_name": "bronze_customers",
        "csv_schema": CUSTOMER_CSV_SCHEMA,
        "bronze_schema": CUSTOMER_BRONZE_SCHEMA,
        "business_columns": CUSTOMER_BUSINESS_COLUMNS,
    },
    "orders": {
        "source_file": "orders.csv",
        "table_name": "bronze_orders",
        "csv_schema": ORDER_CSV_SCHEMA,
        "bronze_schema": ORDER_BRONZE_SCHEMA,
        "business_columns": ORDER_BUSINESS_COLUMNS,
    },
    "products": {
        "source_file": "products.csv",
        "table_name": "bronze_products",
        "csv_schema": PRODUCT_CSV_SCHEMA,
        "bronze_schema": PRODUCT_BRONZE_SCHEMA,
        "business_columns": PRODUCT_BUSINESS_COLUMNS,
    },
}
