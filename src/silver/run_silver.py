"""Silver transformation entry point."""

from __future__ import annotations

from pyspark.sql import SparkSession

from common.config import SilverSettings, load_silver_settings
from common.spark_session import create_spark_session
from silver.transform import transform_all_silver_tables


def run_silver_transformation(
    spark: SparkSession | None = None,
    settings: SilverSettings | None = None,
):
    """Run Silver transformation for all entities and DQ metrics."""
    resolved_settings = settings or load_silver_settings()
    session = spark or create_spark_session("silver-transformation")
    result = transform_all_silver_tables(session, resolved_settings)

    for entity_result in result.entity_results:
        print(
            f"{entity_result.table_name}: {entity_result.silver_row_count} rows "
            f"({entity_result.bronze_table_name} -> {entity_result.storage_label})"
        )

    print(f"dq_metrics -> {result.dq_metrics_label}")
    print(f"dq_metrics_by_rule -> {result.dq_metrics_by_rule_label}")

    return result


def main() -> None:
    run_silver_transformation()


if __name__ == "__main__":
    main()
