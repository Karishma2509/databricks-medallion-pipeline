"""Bronze ingestion entry point."""

from __future__ import annotations

from pyspark.sql import SparkSession

from bronze.ingest import ingest_all_bronze_tables
from common.config import load_bronze_settings
from common.spark_session import create_spark_session


def run_bronze_ingestion(spark: SparkSession | None = None) -> list:
    """Run Bronze ingestion for all source datasets."""
    settings = load_bronze_settings()
    session = spark or create_spark_session("bronze-ingestion")
    results = ingest_all_bronze_tables(session, settings)

    for result in results:
        print(
            f"{result.table_name}: {result.bronze_row_count} rows "
            f"({result.source_path.name} -> {result.delta_path})"
        )

    return results


def main() -> None:
    run_bronze_ingestion()


if __name__ == "__main__":
    main()
