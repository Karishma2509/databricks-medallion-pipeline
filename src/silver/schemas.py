"""Silver output schemas, column lists, and DQ rule definitions."""

from __future__ import annotations

from pyspark.sql.types import (
    ArrayType,
    BooleanType,
    DateType,
    DecimalType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from bronze.schemas import (
    CUSTOMER_BUSINESS_COLUMNS,
    METADATA_COLUMNS,
    ORDER_BUSINESS_COLUMNS,
    PRODUCT_BUSINESS_COLUMNS,
)

DECIMAL_10_2 = DecimalType(10, 2)

CUSTOMER_STRING_COLUMNS = CUSTOMER_BUSINESS_COLUMNS
ORDER_STRING_COLUMNS = [
    "order_id",
    "customer_id",
    "product_id",
]
PRODUCT_STRING_COLUMNS = [
    "product_id",
    "product_name",
    "category",
]

CUSTOMER_DQ_COLUMNS = [
    "is_email_complete",
    "is_customer_id_unique",
    "is_valid_record",
    "dq_failure_reasons",
]

ORDER_DQ_COLUMNS = [
    "is_customer_id_complete",
    "is_product_id_complete",
    "is_order_id_unique",
    "is_customer_id_valid_ref",
    "is_product_id_valid_ref",
    "is_valid_record",
    "dq_failure_reasons",
]

PRODUCT_DQ_COLUMNS = ["is_valid_record"]

SILVER_TABLES = {
    "customers": {
        "bronze_table_name": "bronze_customers",
        "table_name": "silver_customers",
        "string_columns": CUSTOMER_STRING_COLUMNS,
        "business_columns": CUSTOMER_BUSINESS_COLUMNS,
        "dq_columns": CUSTOMER_DQ_COLUMNS,
    },
    "orders": {
        "bronze_table_name": "bronze_orders",
        "table_name": "silver_orders",
        "string_columns": ORDER_STRING_COLUMNS,
        "business_columns": ORDER_BUSINESS_COLUMNS + ["line_revenue"],
        "dq_columns": ORDER_DQ_COLUMNS,
    },
    "products": {
        "bronze_table_name": "bronze_products",
        "table_name": "silver_products",
        "string_columns": PRODUCT_STRING_COLUMNS,
        "business_columns": PRODUCT_BUSINESS_COLUMNS,
        "dq_columns": PRODUCT_DQ_COLUMNS,
    },
}

ISSUE_CODES = {
    "CUST_EMAIL_MISSING": {
        "dataset": "customers",
        "rule_category": "completeness",
        "flag_column": "is_email_complete",
        "expected_failed_count": 50,
    },
    "CUST_ID_DUPLICATE": {
        "dataset": "customers",
        "rule_category": "uniqueness",
        "flag_column": "is_customer_id_unique",
        "expected_failed_count": 30,
    },
    "ORD_CUST_ID_MISSING": {
        "dataset": "orders",
        "rule_category": "completeness",
        "flag_column": "is_customer_id_complete",
        "expected_failed_count": 100,
    },
    "ORD_PROD_ID_MISSING": {
        "dataset": "orders",
        "rule_category": "completeness",
        "flag_column": "is_product_id_complete",
        "expected_failed_count": 100,
    },
    "ORD_ID_DUPLICATE": {
        "dataset": "orders",
        "rule_category": "uniqueness",
        "flag_column": "is_order_id_unique",
        "expected_failed_count": 70,
    },
    "ORD_CUST_ID_INVALID": {
        "dataset": "orders",
        "rule_category": "referential_integrity",
        "flag_column": "is_customer_id_valid_ref",
        "expected_failed_count": 200,
    },
    "ORD_PROD_ID_INVALID": {
        "dataset": "orders",
        "rule_category": "referential_integrity",
        "flag_column": "is_product_id_valid_ref",
        "expected_failed_count": 150,
    },
}

DQ_METRICS_SCHEMA = StructType(
    [
        StructField("metric_run_id", StringType(), False),
        StructField("metric_timestamp", TimestampType(), False),
        StructField("dataset", StringType(), False),
        StructField("total_records", IntegerType(), False),
        StructField("valid_records", IntegerType(), False),
        StructField("invalid_records", IntegerType(), False),
        StructField("valid_record_pct", DecimalType(10, 6), False),
    ]
)

DQ_METRICS_BY_RULE_SCHEMA = StructType(
    [
        StructField("metric_run_id", StringType(), False),
        StructField("dataset", StringType(), False),
        StructField("rule_code", StringType(), False),
        StructField("rule_category", StringType(), False),
        StructField("failed_record_count", IntegerType(), False),
        StructField("expected_failed_count", IntegerType(), False),
    ]
)
