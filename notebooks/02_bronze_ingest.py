# Databricks notebook source
# COMMAND ----------
# Thin orchestration notebook for Phase 6 Bronze ingestion.
# Expects repository `src/` package on the Python path.

# COMMAND ----------
import sys
from pathlib import Path

repo_root = Path.cwd()
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# COMMAND ----------
from bronze.run_bronze import run_bronze_ingestion
from common.spark_session import create_spark_session

spark = create_spark_session("bronze-ingestion-notebook")
results = run_bronze_ingestion(spark)

# COMMAND ----------
for result in results:
    print(
        f"{result.table_name}: {result.bronze_row_count} rows "
        f"({result.source_path.name} -> {result.delta_path})"
    )
