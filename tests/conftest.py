import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.config import load_bronze_settings, load_gold_settings, load_silver_settings  # noqa: E402
from common.spark_session import create_spark_session  # noqa: E402


@pytest.fixture(scope="session")
def spark():
    session = create_spark_session("bronze-tests")
    yield session
    session.stop()


@pytest.fixture(scope="session")
def _bronze_session_data(spark, tmp_path_factory):
    """Create one shared Bronze settings object and ingest once per test session."""
    from bronze.ingest import ingest_all_bronze_tables

    settings = load_bronze_settings(
        raw_data_dir=PROJECT_ROOT / "data" / "raw",
        delta_base_dir=tmp_path_factory.mktemp("bronze") / "delta",
        catalog="medallion_eval",
        schema="bronze",
        ingest_batch_id="test-batch-001",
        ingest_timestamp=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    results = ingest_all_bronze_tables(spark, settings)
    return settings, results


@pytest.fixture(scope="session")
def bronze_settings(_bronze_session_data):
    return _bronze_session_data[0]


@pytest.fixture(scope="session")
def bronze_results(_bronze_session_data):
    return _bronze_session_data[1]


@pytest.fixture(scope="session")
def silver_settings(_bronze_session_data):
    """Silver settings sharing the same Delta base directory as Bronze."""
    bronze_settings, _ = _bronze_session_data
    return load_silver_settings(
        delta_base_dir=bronze_settings.delta_base_dir,
        catalog=bronze_settings.catalog,
        bronze_schema=bronze_settings.schema,
        silver_schema="silver",
        dq_schema="dq",
        metric_run_id="test-metric-run-001",
        metric_timestamp=datetime(2025, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture(scope="session")
def silver_results(spark, silver_settings):
    """Run Silver transformation once per test session."""
    from silver.transform import transform_all_silver_tables

    return transform_all_silver_tables(spark, silver_settings)


@pytest.fixture(scope="session")
def gold_settings(silver_settings):
    """Gold settings sharing the same Delta base directory as Bronze/Silver."""
    return load_gold_settings(
        delta_base_dir=silver_settings.delta_base_dir,
        catalog=silver_settings.catalog,
        silver_schema=silver_settings.silver_schema,
        gold_schema="gold",
    )


@pytest.fixture(scope="session")
def gold_results(spark, gold_settings, silver_results):
    """Run Gold transformation once per test session."""
    from gold.transform import transform_all_gold_tables

    return transform_all_gold_tables(spark, gold_settings)
