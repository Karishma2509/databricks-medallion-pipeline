"""Gold output schemas, column lists, and segmentation constants."""

from __future__ import annotations

from pyspark.sql.types import DecimalType, LongType, StringType, StructField, StructType

DECIMAL_12_2 = DecimalType(12, 2)

SEGMENT_NO_PURCHASE = "No Purchase"
SEGMENT_LOW_VALUE = "Low Value"
SEGMENT_MID_VALUE = "Mid Value"
SEGMENT_HIGH_VALUE = "High Value"

CUSTOMER_SEGMENTS = [
    SEGMENT_NO_PURCHASE,
    SEGMENT_LOW_VALUE,
    SEGMENT_MID_VALUE,
    SEGMENT_HIGH_VALUE,
]

SEGMENT_LOW_MAX = 500
SEGMENT_MID_MAX = 2000

SALES_BY_PRODUCT_COLUMNS = [
    "product_id",
    "product_name",
    "category",
    "total_orders",
    "total_revenue",
    "average_order_value",
]

REVENUE_BY_CUSTOMER_COLUMNS = [
    "customer_id",
    "customer_name",
    "customer_segment",
    "total_orders",
    "total_revenue",
    "average_order_value",
    "lifetime_value_actual",
]

CUSTOMER_SEGMENTATION_COLUMNS = [
    "customer_segment",
    "customer_count",
    "average_revenue",
    "total_revenue",
]

GOLD_TABLES = {
    "sales_by_product": {
        "table_name": "gold_sales_by_product",
        "columns": SALES_BY_PRODUCT_COLUMNS,
    },
    "revenue_by_customer": {
        "table_name": "gold_revenue_by_customer",
        "columns": REVENUE_BY_CUSTOMER_COLUMNS,
    },
    "customer_segmentation": {
        "table_name": "gold_customer_segmentation",
        "columns": CUSTOMER_SEGMENTATION_COLUMNS,
    },
}

SALES_BY_PRODUCT_SCHEMA = StructType(
    [
        StructField("product_id", StringType(), False),
        StructField("product_name", StringType(), True),
        StructField("category", StringType(), True),
        StructField("total_orders", LongType(), False),
        StructField("total_revenue", DECIMAL_12_2, False),
        StructField("average_order_value", DECIMAL_12_2, True),
    ]
)

REVENUE_BY_CUSTOMER_SCHEMA = StructType(
    [
        StructField("customer_id", StringType(), False),
        StructField("customer_name", StringType(), True),
        StructField("customer_segment", StringType(), False),
        StructField("total_orders", LongType(), False),
        StructField("total_revenue", DECIMAL_12_2, False),
        StructField("average_order_value", DECIMAL_12_2, True),
        StructField("lifetime_value_actual", DECIMAL_12_2, False),
    ]
)

CUSTOMER_SEGMENTATION_SCHEMA = StructType(
    [
        StructField("customer_segment", StringType(), False),
        StructField("customer_count", LongType(), False),
        StructField("average_revenue", DECIMAL_12_2, True),
        StructField("total_revenue", DECIMAL_12_2, False),
    ]
)
