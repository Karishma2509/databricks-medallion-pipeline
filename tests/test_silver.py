import json
import sys
from pathlib import Path

import pytest
from pyspark.sql import functions as F

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from bronze.ingest import read_bronze_table  # noqa: E402
from bronze.schemas import METADATA_COLUMNS  # noqa: E402
from data_generation.config import (  # noqa: E402
    FINAL_CUSTOMER_COUNT,
    FINAL_ORDER_COUNT,
    FINAL_PRODUCT_COUNT,
)
from silver.schemas import ISSUE_CODES  # noqa: E402
from silver.transform import read_dq_table, read_silver_table  # noqa: E402


@pytest.fixture
def expected_issue_counts() -> dict[str, int]:
    fixture_path = PROJECT_ROOT / "tests" / "fixtures" / "manifest_expected_counts.json"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_all_three_silver_tables_exist(silver_results):
    assert len(silver_results.entity_results) == 3
    datasets = {result.dataset for result in silver_results.entity_results}
    assert datasets == {"customers", "orders", "products"}


def test_silver_row_counts_match_bronze(silver_results):
    expected = {
        "customers": FINAL_CUSTOMER_COUNT,
        "orders": FINAL_ORDER_COUNT,
        "products": FINAL_PRODUCT_COUNT,
    }

    for result in silver_results.entity_results:
        assert result.silver_row_count == expected[result.dataset]
        assert result.silver_row_count == result.bronze_row_count


def test_silver_bronze_row_parity(spark, bronze_settings, silver_settings, silver_results):
    expected = {
        "customers": FINAL_CUSTOMER_COUNT,
        "orders": FINAL_ORDER_COUNT,
        "products": FINAL_PRODUCT_COUNT,
    }

    for result in silver_results.entity_results:
        bronze_df = read_bronze_table(spark, bronze_settings, result.bronze_table_name)
        silver_df = read_silver_table(spark, silver_settings, result.table_name)
        assert bronze_df.count() == silver_df.count() == expected[result.dataset]


def test_silver_conformance_string_trim(spark, silver_settings, silver_results):
    customers = read_silver_table(spark, silver_settings, "silver_customers")
    orders = read_silver_table(spark, silver_settings, "silver_orders")
    products = read_silver_table(spark, silver_settings, "silver_products")

    for column in ["customer_id", "customer_name", "email", "country", "signup_channel"]:
        trimmed_mismatch = customers.filter(F.col(column) != F.trim(F.col(column))).count()
        assert trimmed_mismatch == 0

    for column in ["order_id", "customer_id", "product_id"]:
        trimmed_mismatch = orders.filter(F.col(column) != F.trim(F.col(column))).count()
        assert trimmed_mismatch == 0

    for column in ["product_id", "product_name", "category"]:
        trimmed_mismatch = products.filter(F.col(column) != F.trim(F.col(column))).count()
        assert trimmed_mismatch == 0


def test_silver_conformance_types_and_line_revenue(spark, silver_settings, silver_results):
    orders = read_silver_table(spark, silver_settings, "silver_orders")
    customers = read_silver_table(spark, silver_settings, "silver_customers")
    products = read_silver_table(spark, silver_settings, "silver_products")

    assert dict(orders.dtypes)["quantity"] == "int"
    assert dict(orders.dtypes)["unit_price"] == "decimal(10,2)"
    assert dict(orders.dtypes)["line_revenue"] == "decimal(10,2)"
    assert dict(customers.dtypes)["registration_date"] == "date"
    assert dict(orders.dtypes)["order_date"] == "date"
    assert dict(products.dtypes)["list_price"] == "decimal(10,2)"
    assert dict(products.dtypes)["is_active"] == "boolean"

    revenue_mismatch = orders.filter(
        F.col("line_revenue") != (F.col("quantity") * F.col("unit_price")).cast("decimal(10,2)")
    ).count()
    assert revenue_mismatch == 0


def test_silver_completeness_counts(spark, silver_settings, silver_results):
    customers = read_silver_table(spark, silver_settings, "silver_customers")
    orders = read_silver_table(spark, silver_settings, "silver_orders")

    assert customers.filter(~F.col("is_email_complete")).count() == 50
    assert orders.filter(~F.col("is_customer_id_complete")).count() == 100
    assert orders.filter(~F.col("is_product_id_complete")).count() == 100


def test_silver_uniqueness_counts(spark, silver_settings, silver_results):
    customers = read_silver_table(spark, silver_settings, "silver_customers")
    orders = read_silver_table(spark, silver_settings, "silver_orders")

    assert customers.filter(~F.col("is_customer_id_unique")).count() == 30
    assert orders.filter(~F.col("is_order_id_unique")).count() == 70


def test_silver_uniqueness_flags_all_duplicate_rows(spark, silver_settings, silver_results):
    customers = read_silver_table(spark, silver_settings, "silver_customers")
    orders = read_silver_table(spark, silver_settings, "silver_orders")

    dup_customer_keys = (
        customers.groupBy("customer_id")
        .count()
        .filter(F.col("count") > 1)
        .select("customer_id")
    )
    dup_customer_rows = customers.join(dup_customer_keys, on="customer_id", how="inner")
    assert dup_customer_rows.filter(F.col("is_customer_id_unique")).count() == 0
    assert dup_customer_rows.count() == 30

    dup_order_keys = (
        orders.groupBy("order_id").count().filter(F.col("count") > 1).select("order_id")
    )
    dup_order_rows = orders.join(dup_order_keys, on="order_id", how="inner")
    assert dup_order_rows.filter(F.col("is_order_id_unique")).count() == 0
    assert dup_order_rows.count() == 70


def test_silver_referential_integrity_counts(spark, silver_settings, silver_results):
    orders = read_silver_table(spark, silver_settings, "silver_orders")

    assert orders.filter(~F.col("is_customer_id_valid_ref")).count() == 200
    assert orders.filter(~F.col("is_product_id_valid_ref")).count() == 150


def test_silver_ri_checks_existence_only(spark, silver_settings, silver_results):
    """RI must not require referenced rows to be valid."""
    customers = read_silver_table(spark, silver_settings, "silver_customers")
    orders = read_silver_table(spark, silver_settings, "silver_orders")

    invalid_customers = customers.filter(~F.col("is_valid_record")).select("customer_id")
    orders_with_invalid_customer_ref = orders.join(
        invalid_customers,
        orders["customer_id"] == invalid_customers["customer_id"],
        how="inner",
    )
    assert orders_with_invalid_customer_ref.filter(F.col("is_customer_id_valid_ref")).count() > 0


def test_silver_validity_logic(spark, silver_settings, silver_results):
    customers = read_silver_table(spark, silver_settings, "silver_customers")
    orders = read_silver_table(spark, silver_settings, "silver_orders")
    products = read_silver_table(spark, silver_settings, "silver_products")

    customer_validity_mismatch = customers.filter(
        F.col("is_valid_record")
        != (F.col("is_email_complete") & F.col("is_customer_id_unique"))
    ).count()
    assert customer_validity_mismatch == 0

    order_validity_mismatch = orders.filter(
        F.col("is_valid_record")
        != (
            F.col("is_customer_id_complete")
            & F.col("is_product_id_complete")
            & F.col("is_order_id_unique")
            & F.col("is_customer_id_valid_ref")
            & F.col("is_product_id_valid_ref")
        )
    ).count()
    assert order_validity_mismatch == 0

    assert products.filter(~F.col("is_valid_record")).count() == 0


def test_silver_invalid_records_retained(spark, silver_settings, silver_results):
    customers = read_silver_table(spark, silver_settings, "silver_customers")
    orders = read_silver_table(spark, silver_settings, "silver_orders")

    assert customers.filter(~F.col("is_valid_record")).count() > 0
    assert orders.filter(~F.col("is_valid_record")).count() > 0
    assert customers.count() == FINAL_CUSTOMER_COUNT
    assert orders.count() == FINAL_ORDER_COUNT


def test_silver_duplicate_records_retained(spark, silver_settings, silver_results):
    customers = read_silver_table(spark, silver_settings, "silver_customers")
    orders = read_silver_table(spark, silver_settings, "silver_orders")

    duplicate_customer_ids = (
        customers.groupBy("customer_id").count().filter(F.col("count") > 1).count()
    )
    duplicate_order_ids = orders.groupBy("order_id").count().filter(F.col("count") > 1).count()

    assert duplicate_customer_ids == 15
    assert duplicate_order_ids == 35


def test_silver_dq_failure_reasons(spark, silver_settings, silver_results):
    customers = read_silver_table(spark, silver_settings, "silver_customers")
    orders = read_silver_table(spark, silver_settings, "silver_orders")

    email_missing = customers.filter(
        F.array_contains(F.col("dq_failure_reasons"), "CUST_EMAIL_MISSING")
    ).count()
    assert email_missing == 50

    cust_dup = customers.filter(
        F.array_contains(F.col("dq_failure_reasons"), "CUST_ID_DUPLICATE")
    ).count()
    assert cust_dup == 30

    ord_cust_missing = orders.filter(
        F.array_contains(F.col("dq_failure_reasons"), "ORD_CUST_ID_MISSING")
    ).count()
    assert ord_cust_missing == 100

    ord_prod_missing = orders.filter(
        F.array_contains(F.col("dq_failure_reasons"), "ORD_PROD_ID_MISSING")
    ).count()
    assert ord_prod_missing == 100

    ord_dup = orders.filter(
        F.array_contains(F.col("dq_failure_reasons"), "ORD_ID_DUPLICATE")
    ).count()
    assert ord_dup == 70

    ord_cust_invalid = orders.filter(
        F.array_contains(F.col("dq_failure_reasons"), "ORD_CUST_ID_INVALID")
    ).count()
    assert ord_cust_invalid == 200

    ord_prod_invalid = orders.filter(
        F.array_contains(F.col("dq_failure_reasons"), "ORD_PROD_ID_INVALID")
    ).count()
    assert ord_prod_invalid == 150


def test_silver_dq_metrics(spark, silver_settings, silver_results):
    dq_metrics = read_dq_table(spark, silver_settings, "dq_metrics")

    assert dq_metrics.count() == 3

    totals = {
        row["dataset"]: row
        for row in dq_metrics.collect()
    }
    assert totals["customers"]["total_records"] == FINAL_CUSTOMER_COUNT
    assert totals["orders"]["total_records"] == FINAL_ORDER_COUNT
    assert totals["products"]["total_records"] == FINAL_PRODUCT_COUNT

    for dataset in ("customers", "orders", "products"):
        row = totals[dataset]
        assert row["valid_records"] + row["invalid_records"] == row["total_records"]
        assert abs(row["valid_record_pct"] - (row["valid_records"] / row["total_records"])) < 1e-6


def test_silver_dq_metrics_by_rule(spark, silver_settings, silver_results, expected_issue_counts):
    dq_metrics_by_rule = read_dq_table(spark, silver_settings, "dq_metrics_by_rule")

    assert dq_metrics_by_rule.count() == 7

    for row in dq_metrics_by_rule.collect():
        rule_code = row["rule_code"]
        assert row["failed_record_count"] == expected_issue_counts[rule_code]
        assert row["expected_failed_count"] == ISSUE_CODES[rule_code]["expected_failed_count"]

    total_failed = sum(row["failed_record_count"] for row in dq_metrics_by_rule.collect())
    assert total_failed == 700


def test_silver_metadata_columns_preserved(spark, silver_settings, silver_results):
    for table_name in ("silver_customers", "silver_orders", "silver_products"):
        silver_df = read_silver_table(spark, silver_settings, table_name)
        for column in METADATA_COLUMNS:
            assert column in silver_df.columns

        null_metadata = silver_df.filter(
            F.col("_ingest_batch_id").isNull()
            | F.col("_ingest_timestamp").isNull()
            | F.col("_source_file").isNull()
            | F.col("_source_row_number").isNull()
            | F.col("_bronze_record_id").isNull()
        )
        assert null_metadata.count() == 0
