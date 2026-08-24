# Databricks notebook source
# COMMAND ----------
# Thin orchestration notebook for Phase 7 Silver transformation.
# Expects repository `src/` package on the Python path.

# COMMAND ----------
import sys
from pathlib import Path

repo_root = Path.cwd()
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# COMMAND ----------
from silver.run_silver import run_silver_transformation
from common.spark_session import create_spark_session

spark = create_spark_session("silver-transformation-notebook")
result = run_silver_transformation(spark)

# COMMAND ----------
for entity_result in result.entity_results:
    print(
        f"{entity_result.table_name}: {entity_result.silver_row_count} rows "
        f"({entity_result.bronze_table_name} -> {entity_result.delta_path})"
    )

print(f"dq_metrics -> {result.dq_metrics_path}")
print(f"dq_metrics_by_rule -> {result.dq_metrics_by_rule_path}")
