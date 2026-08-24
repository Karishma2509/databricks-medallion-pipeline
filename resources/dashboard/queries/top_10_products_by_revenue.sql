-- Top 10 Products by Revenue
-- Visualization: horizontal bar chart (product_name vs total_revenue)
-- Source: gold_sales_by_product (Gold layer only)
--
-- Configuration (replace if your workspace uses different names):
--   catalog      = medallion_eval  (env: DATABRICKS_CATALOG)
--   gold_schema  = gold            (env: GOLD_SCHEMA)
--
-- Business logic (ranking, revenue aggregation) is computed in Gold.
-- This query selects pre-aggregated Gold columns only.

SELECT
    product_name,
    total_revenue
FROM medallion_eval.gold.gold_sales_by_product
ORDER BY total_revenue DESC
LIMIT 10;
