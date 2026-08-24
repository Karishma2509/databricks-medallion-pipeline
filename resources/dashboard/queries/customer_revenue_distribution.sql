-- Customer Revenue Distribution
-- Visualization: histogram of total_revenue
-- Source: gold_revenue_by_customer (Gold layer only)
--
-- Configuration (replace if your workspace uses different names):
--   catalog      = medallion_eval  (env: DATABRICKS_CATALOG)
--   gold_schema  = gold            (env: GOLD_SCHEMA)
--
-- Histogram bin boundaries are NOT defined in SQL.
-- Configure bins in the Databricks SQL dashboard visualization UI
-- when creating the histogram widget (Phase 9 UI configuration item).
--
-- Business logic (customer revenue, segmentation thresholds) is computed in Gold.
-- This query returns one row per valid customer with pre-aggregated total_revenue.

SELECT
    total_revenue
FROM medallion_eval.gold.gold_revenue_by_customer;
