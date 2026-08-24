"""Gold transformation entry point."""

from __future__ import annotations

from pyspark.sql import SparkSession

from common.config import load_gold_settings
from common.spark_session import create_spark_session
from gold.transform import transform_all_gold_tables


def run_gold_transformation(spark: SparkSession | None = None):
    """Run Gold transformation for all business aggregate tables."""
    settings = load_gold_settings()
    session = spark or create_spark_session("gold-transformation")
    result = transform_all_gold_tables(session, settings)

    for table_result in result.table_results:
        print(
            f"{table_result.table_name}: {table_result.row_count} rows "
            f"-> {table_result.delta_path}"
        )

    return result


def main() -> None:
    run_gold_transformation()


if __name__ == "__main__":
    main()
