"""Shared project configuration helpers."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_DELTA_BASE_DIR = PROJECT_ROOT / "data" / "delta"


@dataclass(frozen=True)
class BronzeSettings:
    catalog: str
    schema: str
    raw_data_dir: Path
    delta_base_dir: Path
    ingest_batch_id: str
    ingest_timestamp: datetime

    @property
    def bronze_schema_path(self) -> Path:
        return self.delta_base_dir / self.catalog / self.schema

    def table_path(self, table_name: str) -> Path:
        return self.bronze_schema_path / table_name

    def qualified_table_name(self, table_name: str) -> str:
        return f"{self.catalog}.{self.schema}.{table_name}"


def load_bronze_settings(
    raw_data_dir: Path | None = None,
    delta_base_dir: Path | None = None,
    catalog: str | None = None,
    schema: str | None = None,
    ingest_batch_id: str | None = None,
    ingest_timestamp: datetime | None = None,
) -> BronzeSettings:
    """Load Bronze settings from arguments with design-document defaults."""
    return BronzeSettings(
        catalog=catalog or os.getenv("DATABRICKS_CATALOG", "medallion_eval"),
        schema=schema or os.getenv("BRONZE_SCHEMA", "bronze"),
        raw_data_dir=raw_data_dir or Path(os.getenv("MEDALLION_RAW_PATH", DEFAULT_RAW_DATA_DIR)),
        delta_base_dir=delta_base_dir
        or Path(os.getenv("MEDALLION_DELTA_PATH", DEFAULT_DELTA_BASE_DIR)),
        ingest_batch_id=ingest_batch_id or os.getenv("INGEST_BATCH_ID", str(uuid.uuid4())),
        ingest_timestamp=ingest_timestamp or datetime.now(timezone.utc),
    )
