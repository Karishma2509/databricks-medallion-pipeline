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


@dataclass(frozen=True)
class SilverSettings:
    catalog: str
    bronze_schema: str
    silver_schema: str
    dq_schema: str
    delta_base_dir: Path
    metric_run_id: str
    metric_timestamp: datetime

    def bronze_table_path(self, table_name: str) -> Path:
        return self.delta_base_dir / self.catalog / self.bronze_schema / table_name

    def silver_table_path(self, table_name: str) -> Path:
        return self.delta_base_dir / self.catalog / self.silver_schema / table_name

    def dq_table_path(self, table_name: str) -> Path:
        return self.delta_base_dir / self.catalog / self.dq_schema / table_name

    def qualified_bronze_table_name(self, table_name: str) -> str:
        return f"{self.catalog}.{self.bronze_schema}.{table_name}"

    def qualified_silver_table_name(self, table_name: str) -> str:
        return f"{self.catalog}.{self.silver_schema}.{table_name}"

    def qualified_dq_table_name(self, table_name: str) -> str:
        return f"{self.catalog}.{self.dq_schema}.{table_name}"


def load_silver_settings(
    delta_base_dir: Path | None = None,
    catalog: str | None = None,
    bronze_schema: str | None = None,
    silver_schema: str | None = None,
    dq_schema: str | None = None,
    metric_run_id: str | None = None,
    metric_timestamp: datetime | None = None,
) -> SilverSettings:
    """Load Silver settings from arguments with design-document defaults."""
    return SilverSettings(
        catalog=catalog or os.getenv("DATABRICKS_CATALOG", "medallion_eval"),
        bronze_schema=bronze_schema or os.getenv("BRONZE_SCHEMA", "bronze"),
        silver_schema=silver_schema or os.getenv("SILVER_SCHEMA", "silver"),
        dq_schema=dq_schema or os.getenv("DQ_SCHEMA", "dq"),
        delta_base_dir=delta_base_dir
        or Path(os.getenv("MEDALLION_DELTA_PATH", DEFAULT_DELTA_BASE_DIR)),
        metric_run_id=metric_run_id or os.getenv("METRIC_RUN_ID", str(uuid.uuid4())),
        metric_timestamp=metric_timestamp or datetime.now(timezone.utc),
    )


@dataclass(frozen=True)
class GoldSettings:
    catalog: str
    silver_schema: str
    gold_schema: str
    delta_base_dir: Path
    segment_low_max: int
    segment_mid_max: int

    def silver_table_path(self, table_name: str) -> Path:
        return self.delta_base_dir / self.catalog / self.silver_schema / table_name

    def gold_table_path(self, table_name: str) -> Path:
        return self.delta_base_dir / self.catalog / self.gold_schema / table_name

    def qualified_silver_table_name(self, table_name: str) -> str:
        return f"{self.catalog}.{self.silver_schema}.{table_name}"

    def qualified_gold_table_name(self, table_name: str) -> str:
        return f"{self.catalog}.{self.gold_schema}.{table_name}"


def load_gold_settings(
    delta_base_dir: Path | None = None,
    catalog: str | None = None,
    silver_schema: str | None = None,
    gold_schema: str | None = None,
    segment_low_max: int | None = None,
    segment_mid_max: int | None = None,
) -> GoldSettings:
    """Load Gold settings from arguments with design-document defaults."""
    return GoldSettings(
        catalog=catalog or os.getenv("DATABRICKS_CATALOG", "medallion_eval"),
        silver_schema=silver_schema or os.getenv("SILVER_SCHEMA", "silver"),
        gold_schema=gold_schema or os.getenv("GOLD_SCHEMA", "gold"),
        delta_base_dir=delta_base_dir
        or Path(os.getenv("MEDALLION_DELTA_PATH", DEFAULT_DELTA_BASE_DIR)),
        segment_low_max=segment_low_max
        or int(os.getenv("SEGMENT_LOW_MAX", "500")),
        segment_mid_max=segment_mid_max
        or int(os.getenv("SEGMENT_MID_MAX", "2000")),
    )
