import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.config import load_bronze_settings  # noqa: E402
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
