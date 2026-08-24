-- Customer Segmentation
-- Visualization: bar chart (customer_segment vs total_revenue)
-- Source: gold_customer_segmentation (Gold layer only)
--
-- Configuration (replace if your workspace uses different names):
--   catalog      = medallion_eval  (env: DATABRICKS_CATALOG)
--   gold_schema  = gold            (env: GOLD_SCHEMA)
--
-- Segment ordering is not specified in the approved design.
-- Optional: sort segments in the dashboard UI if a custom display order is desired.
--
-- customer_count and average_revenue are available in Gold but are not required
-- for the approved bar chart mapping (customer_segment vs total_revenue).
--
-- Business logic (segment assignment, rollups) is computed in Gold.

SELECT
    customer_segment,
    total_revenue
FROM medallion_eval.gold.gold_customer_segmentation;
