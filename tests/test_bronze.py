import csv
import sys
from collections import Counter
from pathlib import Path

import pytest
from pyspark.sql import functions as F

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from bronze.ingest import read_bronze_table, read_source_csv  # noqa: E402
from bronze.schemas import (  # noqa: E402
    BRONZE_TABLES,
    CUSTOMER_BUSINESS_COLUMNS,
    METADATA_COLUMNS,
    ORDER_BUSINESS_COLUMNS,
    PRODUCT_BUSINESS_COLUMNS,
)
from data_generation.config import (  # noqa: E402
    FINAL_CUSTOMER_COUNT,
    FINAL_ORDER_COUNT,
    FINAL_PRODUCT_COUNT,
)


def _count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def test_all_three_datasets_ingested(bronze_results):
    assert len(bronze_results) == 3
    datasets = {result.dataset for result in bronze_results}
    assert datasets == {"customers", "orders", "products"}


def test_bronze_row_counts_match_source(bronze_results, bronze_settings):
    expected = {
        "customers": FINAL_CUSTOMER_COUNT,
        "orders": FINAL_ORDER_COUNT,
        "products": FINAL_PRODUCT_COUNT,
    }

    for result in bronze_results:
        assert result.bronze_row_count == expected[result.dataset]
        source_count = _count_csv_rows(result.source_path)
        assert result.source_row_count == source_count
        assert result.bronze_row_count == source_count


def test_bronze_schemas_contain_business_columns(spark, bronze_settings, bronze_results):
    expected_columns = {
        "bronze_customers": CUSTOMER_BUSINESS_COLUMNS,
        "bronze_orders": ORDER_BUSINESS_COLUMNS,
        "bronze_products": PRODUCT_BUSINESS_COLUMNS,
    }

    for result in bronze_results:
        bronze_df = read_bronze_table(spark, bronze_settings, result.table_name)
        for column in expected_columns[result.table_name]:
            assert column in bronze_df.columns


def test_bronze_metadata_columns_exist(spark, bronze_settings, bronze_results):
    for result in bronze_results:
        bronze_df = read_bronze_table(spark, bronze_settings, result.table_name)
        for column in METADATA_COLUMNS:
            assert column in bronze_df.columns


def test_bronze_metadata_populated(spark, bronze_settings, bronze_results):
    for result in bronze_results:
        bronze_df = read_bronze_table(spark, bronze_settings, result.table_name)
        null_metadata = bronze_df.filter(
            F.col("_ingest_batch_id").isNull()
            | F.col("_ingest_timestamp").isNull()
            | F.col("_source_file").isNull()
            | F.col("_source_row_number").isNull()
            | F.col("_bronze_record_id").isNull()
        )
        assert null_metadata.count() == 0

        assert (
            bronze_df.filter(F.col("_ingest_batch_id") != bronze_settings.ingest_batch_id).count()
            == 0
        )
        assert (
            bronze_df.filter(
                F.col("_source_file") != BRONZE_TABLES[result.dataset]["source_file"]
            ).count()
            == 0
        )


def test_duplicate_customer_ids_preserved(spark, bronze_settings):
    bronze_df = read_bronze_table(spark, bronze_settings, "bronze_customers")
    counts = bronze_df.groupBy("customer_id").count()
    duplicate_ids = counts.filter(F.col("count") > 1)
    assert duplicate_ids.count() == 15


def test_duplicate_order_ids_preserved(spark, bronze_settings):
    bronze_df = read_bronze_table(spark, bronze_settings, "bronze_orders")
    counts = bronze_df.groupBy("order_id").count()
    duplicate_ids = counts.filter(F.col("count") > 1)
    assert duplicate_ids.count() == 35


def test_missing_values_preserved(spark, bronze_settings):
    customers = read_bronze_table(spark, bronze_settings, "bronze_customers")
    orders = read_bronze_table(spark, bronze_settings, "bronze_orders")

    blank_emails = customers.filter(
        F.col("email").isNull() | (F.trim(F.col("email")) == "")
    ).count()
    blank_customer_ids = orders.filter(
        F.col("customer_id").isNull() | (F.trim(F.col("customer_id")) == "")
    ).count()
    blank_product_ids = orders.filter(
        F.col("product_id").isNull() | (F.trim(F.col("product_id")) == "")
    ).count()

    assert blank_emails == 50
    assert blank_customer_ids == 100
    assert blank_product_ids == 100


def test_invalid_references_preserved(spark, bronze_settings):
    orders = read_bronze_table(spark, bronze_settings, "bronze_orders")

    invalid_customer_refs = orders.filter(
        F.col("customer_id").startswith("CUST-INVALID-")
    ).count()
    invalid_product_refs = orders.filter(
        F.col("product_id").startswith("PROD-INVALID-")
    ).count()

    assert invalid_customer_refs == 200
    assert invalid_product_refs == 150


def test_no_bronze_filtering_or_deduplication(bronze_results):
    for result in bronze_results:
        assert result.bronze_row_count == result.source_row_count


def test_bronze_record_id_format(spark, bronze_settings):
    customers = read_bronze_table(spark, bronze_settings, "bronze_customers")
    sample = customers.select("_bronze_record_id", "_source_file", "_source_row_number").limit(1).collect()[0]
    assert sample["_bronze_record_id"] == f"{sample['_source_file']}#{sample['_source_row_number']}"


def test_source_csv_fidelity_for_sample_row(spark, bronze_settings):
    """Selected business values in Bronze should match the source CSV row."""
    source_path = bronze_settings.raw_data_dir / "customers.csv"
    source_df = read_source_csv(spark, source_path, BRONZE_TABLES["customers"]["csv_schema"])
    bronze_df = read_bronze_table(spark, bronze_settings, "bronze_customers")

    source_row = source_df.limit(1).collect()[0]
    bronze_row = bronze_df.filter(F.col("_source_row_number") == "1").collect()[0]

    for column in CUSTOMER_BUSINESS_COLUMNS:
        source_value = source_row[column]
        bronze_value = bronze_row[column]
        assert (source_value or "") == (bronze_value or "")
