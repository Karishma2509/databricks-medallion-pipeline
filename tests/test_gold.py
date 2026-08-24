import sys
from pathlib import Path

import pytest
from pyspark.sql import functions as F

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from data_generation.config import FINAL_PRODUCT_COUNT  # noqa: E402
from gold.schemas import (  # noqa: E402
    CUSTOMER_SEGMENTATION_COLUMNS,
    CUSTOMER_SEGMENTS,
    REVENUE_BY_CUSTOMER_COLUMNS,
    SALES_BY_PRODUCT_COLUMNS,
)
from gold.transform import read_gold_table, read_silver_table  # noqa: E402


def _read_silver(spark, gold_settings, table_name):
    return read_silver_table(spark, gold_settings, table_name)


def test_all_three_gold_tables_exist(gold_results):
    assert len(gold_results.table_results) == 3
    table_names = {result.table_name for result in gold_results.table_results}
    assert table_names == {
        "gold_sales_by_product",
        "gold_revenue_by_customer",
        "gold_customer_segmentation",
    }


def test_gold_sales_by_product_schema(spark, gold_settings, gold_results):
    df = read_gold_table(spark, gold_settings, "gold_sales_by_product")
    assert df.columns == SALES_BY_PRODUCT_COLUMNS
    assert dict(df.dtypes)["total_orders"] == "bigint"
    assert dict(df.dtypes)["total_revenue"] == "decimal(12,2)"
    assert dict(df.dtypes)["average_order_value"] == "decimal(12,2)"


def test_gold_revenue_by_customer_schema(spark, gold_settings, gold_results):
    df = read_gold_table(spark, gold_settings, "gold_revenue_by_customer")
    assert df.columns == REVENUE_BY_CUSTOMER_COLUMNS
    assert dict(df.dtypes)["total_orders"] == "bigint"
    assert dict(df.dtypes)["total_revenue"] == "decimal(12,2)"
    assert dict(df.dtypes)["lifetime_value_actual"] == "decimal(12,2)"


def test_gold_customer_segmentation_schema(spark, gold_settings, gold_results):
    df = read_gold_table(spark, gold_settings, "gold_customer_segmentation")
    assert df.columns == CUSTOMER_SEGMENTATION_COLUMNS
    assert df.count() == 4


def test_gold_sales_by_product_row_count(spark, gold_settings, gold_results):
    products = _read_silver(spark, gold_settings, "silver_products")
    gold_products = read_gold_table(spark, gold_settings, "gold_sales_by_product")

    assert products.count() == FINAL_PRODUCT_COUNT == 500
    assert gold_products.count() == 500
    assert gold_products.select("product_id").distinct().count() == 500


def test_gold_sales_by_product_covers_all_silver_products(spark, gold_settings, gold_results):
    products = _read_silver(spark, gold_settings, "silver_products")
    gold_products = read_gold_table(spark, gold_settings, "gold_sales_by_product")

    product_ids = products.select("product_id")
    missing = product_ids.join(gold_products, on="product_id", how="left_anti")
    assert missing.count() == 0

    extra = gold_products.select("product_id").join(product_ids, on="product_id", how="left_anti")
    assert extra.count() == 0


def test_gold_zero_order_products_have_zero_metrics(spark, gold_settings, gold_results):
    orders = _read_silver(spark, gold_settings, "silver_orders")
    products = _read_silver(spark, gold_settings, "silver_products")
    gold_products = read_gold_table(spark, gold_settings, "gold_sales_by_product")

    valid_order_products = (
        orders.filter(F.col("is_valid_record"))
        .select("product_id")
        .distinct()
    )
    zero_order_products = products.join(valid_order_products, on="product_id", how="left_anti")

    if zero_order_products.count() == 0:
        pytest.skip("All products have at least one valid order in generated data")

    zero_order_gold = gold_products.join(
        zero_order_products.select("product_id"),
        on="product_id",
        how="inner",
    )
    assert zero_order_gold.filter(F.col("total_orders") != 0).count() == 0
    assert zero_order_gold.filter(F.col("total_revenue") != 0).count() == 0
    assert zero_order_gold.filter(F.col("average_order_value").isNotNull()).count() == 0


def test_gold_product_attributes_match_silver(spark, gold_settings, gold_results):
    products = _read_silver(spark, gold_settings, "silver_products")
    gold_products = read_gold_table(spark, gold_settings, "gold_sales_by_product")

    joined = products.alias("silver").join(
        gold_products.alias("gold"),
        on="product_id",
        how="inner",
    )
    mismatch = joined.filter(
        (F.col("silver.product_name") != F.col("gold.product_name"))
        | (F.col("silver.category") != F.col("gold.category"))
    )
    assert mismatch.count() == 0


def test_gold_product_revenue_reconciles_to_valid_orders(spark, gold_settings, gold_results):
    orders = _read_silver(spark, gold_settings, "silver_orders")
    gold_products = read_gold_table(spark, gold_settings, "gold_sales_by_product")

    expected = (
        orders.filter(F.col("is_valid_record"))
        .groupBy("product_id")
        .agg(
            F.countDistinct("order_id").alias("expected_orders"),
            F.sum("line_revenue").alias("expected_revenue"),
        )
    )
    actual = gold_products.select(
        "product_id",
        F.col("total_orders").alias("actual_orders"),
        F.col("total_revenue").alias("actual_revenue"),
    )
    comparison = expected.join(actual, on="product_id", how="full_outer").filter(
        (F.col("expected_orders") != F.col("actual_orders"))
        | (F.col("expected_revenue") != F.col("actual_revenue"))
    )
    assert comparison.count() == 0


def test_gold_invalid_orders_excluded_from_product_revenue(spark, gold_settings, gold_results):
    orders = _read_silver(spark, gold_settings, "silver_orders")
    gold_products = read_gold_table(spark, gold_settings, "gold_sales_by_product")

    invalid_revenue = (
        orders.filter(~F.col("is_valid_record"))
        .agg(F.sum("line_revenue").alias("invalid_revenue"))
        .collect()[0]["invalid_revenue"]
    )
    valid_revenue = (
        orders.filter(F.col("is_valid_record"))
        .agg(F.sum("line_revenue").alias("valid_revenue"))
        .collect()[0]["valid_revenue"]
    )
    gold_total = gold_products.agg(F.sum("total_revenue")).collect()[0]["sum(total_revenue)"]

    assert invalid_revenue is not None and invalid_revenue > 0
    assert gold_total == valid_revenue


def test_gold_revenue_by_customer_only_valid_customers(spark, gold_settings, gold_results):
    customers = _read_silver(spark, gold_settings, "silver_customers")
    gold_customers = read_gold_table(spark, gold_settings, "gold_revenue_by_customer")

    invalid_customer_ids = customers.filter(~F.col("is_valid_record")).select("customer_id")
    leaked = gold_customers.join(invalid_customer_ids, on="customer_id", how="inner")
    assert leaked.count() == 0

    valid_customer_count = customers.filter(F.col("is_valid_record")).count()
    assert gold_customers.count() == valid_customer_count


def test_gold_customer_revenue_reconciles_to_valid_orders(spark, gold_settings, gold_results):
    orders = _read_silver(spark, gold_settings, "silver_orders")
    gold_customers = read_gold_table(spark, gold_settings, "gold_revenue_by_customer")

    expected = (
        orders.filter(F.col("is_valid_record"))
        .groupBy("customer_id")
        .agg(
            F.countDistinct("order_id").alias("expected_orders"),
            F.sum("line_revenue").alias("expected_revenue"),
        )
    )
    actual = gold_customers.select(
        "customer_id",
        F.col("total_orders").alias("actual_orders"),
        F.col("total_revenue").alias("actual_revenue"),
    )
    comparison = expected.join(actual, on="customer_id", how="full_outer").filter(
        (F.col("expected_orders") != F.col("actual_orders"))
        | (F.col("expected_revenue") != F.col("actual_revenue"))
    )
    assert comparison.count() == 0


def test_gold_lifetime_value_equals_total_revenue(spark, gold_settings, gold_results):
    gold_customers = read_gold_table(spark, gold_settings, "gold_revenue_by_customer")
    mismatch = gold_customers.filter(
        F.col("lifetime_value_actual") != F.col("total_revenue")
    )
    assert mismatch.count() == 0


def test_gold_average_order_value_calculation(spark, gold_settings, gold_results):
    gold_products = read_gold_table(spark, gold_settings, "gold_sales_by_product")
    gold_customers = read_gold_table(spark, gold_settings, "gold_revenue_by_customer")

    for df in (gold_products, gold_customers):
        with_orders = df.filter(F.col("total_orders") > 0)
        mismatch = with_orders.filter(
            F.col("average_order_value")
            != (F.col("total_revenue") / F.col("total_orders")).cast("decimal(12,2)")
        )
        assert mismatch.count() == 0

        without_orders = df.filter(F.col("total_orders") == 0)
        assert without_orders.filter(F.col("average_order_value").isNotNull()).count() == 0


def test_gold_zero_order_valid_customers_included(spark, gold_settings, gold_results):
    customers = _read_silver(spark, gold_settings, "silver_customers")
    orders = _read_silver(spark, gold_settings, "silver_orders")
    gold_customers = read_gold_table(spark, gold_settings, "gold_revenue_by_customer")

    valid_customers = customers.filter(F.col("is_valid_record"))
    customers_with_valid_orders = (
        orders.filter(F.col("is_valid_record")).select("customer_id").distinct()
    )
    zero_order_valid = valid_customers.join(
        customers_with_valid_orders, on="customer_id", how="left_anti"
    )

    if zero_order_valid.count() == 0:
        pytest.skip("No valid customers with zero valid orders in generated data")

    zero_order_gold = gold_customers.join(
        zero_order_valid.select("customer_id"), on="customer_id", how="inner"
    )
    assert zero_order_gold.filter(F.col("total_orders") != 0).count() == 0
    assert zero_order_gold.filter(F.col("total_revenue") != 0).count() == 0
    assert zero_order_gold.filter(F.col("customer_segment") != "No Purchase").count() == 0


def test_gold_customer_segmentation_labels(spark, gold_settings, gold_results):
    segmentation = read_gold_table(spark, gold_settings, "gold_customer_segmentation")
    labels = {row["customer_segment"] for row in segmentation.collect()}
    assert labels == set(CUSTOMER_SEGMENTS)


def test_gold_customer_segmentation_reconciles_to_customer_gold(spark, gold_settings, gold_results):
    gold_customers = read_gold_table(spark, gold_settings, "gold_revenue_by_customer")
    segmentation = read_gold_table(spark, gold_settings, "gold_customer_segmentation")

    expected = gold_customers.groupBy("customer_segment").agg(
        F.count("customer_id").alias("expected_customer_count"),
        F.avg("total_revenue").alias("expected_average_revenue"),
        F.sum("total_revenue").alias("expected_total_revenue"),
    )
    actual = segmentation.select(
        "customer_segment",
        F.col("customer_count").alias("actual_customer_count"),
        F.col("average_revenue").alias("actual_average_revenue"),
        F.col("total_revenue").alias("actual_total_revenue"),
    )
    comparison = expected.join(actual, on="customer_segment", how="full_outer").filter(
        (F.col("expected_customer_count") != F.col("actual_customer_count"))
        | (F.abs(F.col("expected_average_revenue") - F.col("actual_average_revenue")) > 0.01)
        | (F.col("expected_total_revenue") != F.col("actual_total_revenue"))
    )
    assert comparison.count() == 0


def test_gold_customer_segment_thresholds(spark, gold_settings, gold_results):
    gold_customers = read_gold_table(spark, gold_settings, "gold_revenue_by_customer")

    no_purchase = gold_customers.filter(F.col("customer_segment") == "No Purchase")
    assert no_purchase.filter(F.col("total_revenue") != 0).count() == 0

    low_value = gold_customers.filter(F.col("customer_segment") == "Low Value")
    assert low_value.filter((F.col("total_revenue") <= 0) | (F.col("total_revenue") >= 500)).count() == 0

    mid_value = gold_customers.filter(F.col("customer_segment") == "Mid Value")
    assert mid_value.filter(
        (F.col("total_revenue") < 500) | (F.col("total_revenue") >= 2000)
    ).count() == 0

    high_value = gold_customers.filter(F.col("customer_segment") == "High Value")
    assert high_value.filter(F.col("total_revenue") < 2000).count() == 0


def test_gold_tables_exclude_silver_metadata(spark, gold_settings, gold_results):
    metadata_columns = [
        "_ingest_batch_id",
        "_ingest_timestamp",
        "_source_file",
        "_source_row_number",
        "_bronze_record_id",
        "is_valid_record",
        "dq_failure_reasons",
    ]
    for table_name in (
        "gold_sales_by_product",
        "gold_revenue_by_customer",
        "gold_customer_segmentation",
    ):
        df = read_gold_table(spark, gold_settings, table_name)
        for column in metadata_columns:
            assert column not in df.columns
