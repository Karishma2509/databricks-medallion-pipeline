"""DQ metrics table generation."""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from common.config import SilverSettings
from silver.schemas import ISSUE_CODES


def build_dq_metrics(
    spark: SparkSession,
    settings: SilverSettings,
    silver_customers: DataFrame,
    silver_orders: DataFrame,
    silver_products: DataFrame,
) -> DataFrame:
    """Build run-level dq_metrics (one row per entity)."""
    datasets = [
        ("customers", silver_customers),
        ("orders", silver_orders),
        ("products", silver_products),
    ]

    rows = []
    for dataset_name, dataset_df in datasets:
        total_records = dataset_df.count()
        valid_records = dataset_df.filter(F.col("is_valid_record")).count()
        invalid_records = total_records - valid_records
        valid_record_pct = (
            float(valid_records) / float(total_records) if total_records else 0.0
        )
        rows.append(
            (
                settings.metric_run_id,
                settings.metric_timestamp,
                dataset_name,
                total_records,
                valid_records,
                invalid_records,
                valid_record_pct,
            )
        )

    return spark.createDataFrame(
        rows,
        schema=[
            "metric_run_id",
            "metric_timestamp",
            "dataset",
            "total_records",
            "valid_records",
            "invalid_records",
            "valid_record_pct",
        ],
    )


def build_dq_metrics_by_rule(
    spark: SparkSession,
    settings: SilverSettings,
    silver_customers: DataFrame,
    silver_orders: DataFrame,
) -> DataFrame:
    """Build rule-level dq_metrics_by_rule (one row per approved rule)."""
    dataset_frames = {
        "customers": silver_customers,
        "orders": silver_orders,
    }

    rows = []
    for rule_code, definition in ISSUE_CODES.items():
        dataset_df = dataset_frames[definition["dataset"]]
        flag_column = definition["flag_column"]
        failed_record_count = dataset_df.filter(~F.col(flag_column)).count()
        rows.append(
            (
                settings.metric_run_id,
                definition["dataset"],
                rule_code,
                definition["rule_category"],
                failed_record_count,
                definition["expected_failed_count"],
            )
        )

    return spark.createDataFrame(
        rows,
        schema=[
            "metric_run_id",
            "dataset",
            "rule_code",
            "rule_category",
            "failed_record_count",
            "expected_failed_count",
        ],
    )


def write_dq_metrics(
    spark: SparkSession,
    settings: SilverSettings,
    silver_customers: DataFrame,
    silver_orders: DataFrame,
    silver_products: DataFrame,
) -> tuple[DataFrame, DataFrame]:
    """Generate and persist dq_metrics and dq_metrics_by_rule."""
    dq_metrics = build_dq_metrics(
        spark, settings, silver_customers, silver_orders, silver_products
    )
    dq_metrics_by_rule = build_dq_metrics_by_rule(
        spark, settings, silver_customers, silver_orders
    )

    metrics_path = settings.dq_table_path("dq_metrics")
    metrics_by_rule_path = settings.dq_table_path("dq_metrics_by_rule")

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    dq_metrics.write.format("delta").mode("overwrite").save(str(metrics_path))
    dq_metrics_by_rule.write.format("delta").mode("overwrite").save(str(metrics_by_rule_path))

    return dq_metrics, dq_metrics_by_rule
