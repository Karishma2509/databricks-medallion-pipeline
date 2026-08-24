# Databricks notebook source
# COMMAND ----------
# Thin orchestration notebook for Phase 8 Gold transformation.
# Expects repository `src/` package on the Python path.

# COMMAND ----------
import sys
from pathlib import Path

repo_root = Path.cwd()
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# COMMAND ----------
from gold.run_gold import run_gold_transformation
from common.spark_session import create_spark_session

spark = create_spark_session("gold-transformation-notebook")
result = run_gold_transformation(spark)

# COMMAND ----------
for table_result in result.table_results:
    print(
        f"{table_result.table_name}: {table_result.row_count} rows "
        f"-> {table_result.delta_path}"
    )
