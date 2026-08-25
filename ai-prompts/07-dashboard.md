# Phase 9 — Dashboard — Cursor Prompt History

## Prompt 1 — Dashboard SQL assets and setup guide

### What I asked Cursor

```
Gold tables are populated locally (gold_sales_by_product, gold_revenue_by_customer,
gold_customer_segmentation). Phase 9 is the Databricks SQL Dashboard — presentation
only, no new Python pipeline code under src/.

Read design-notes.md, data-model.md, requirements-analysis.md (dashboard section).

Create SQL query files and a setup guide under resources/dashboard/.
Queries read Gold only — no Silver, Bronze, or dq_* tables.
Don't recompute line_revenue, segmentation thresholds, or DQ filters in SQL.

Three visualizations in one dashboard:

1. Top 10 Products by Revenue
   - gold_sales_by_product, horizontal bar
   - product_name vs total_revenue
   - ORDER BY total_revenue DESC LIMIT 10

2. Customer Revenue Distribution
   - gold_revenue_by_customer, histogram of total_revenue
   - bin boundaries not in design — document choice in setup guide

3. Customer Segmentation
   - gold_customer_segmentation, bar chart
   - customer_segment vs total_revenue

Default paths: medallion_eval.gold.*
Make catalog/schema substitutable (DATABRICKS_CATALOG, GOLD_SCHEMA) so SQL works
in workspace.gold on Databricks Free Edition.

Segment labels must match Gold exactly:
  No Purchase, Low Value, Mid Value, High Value

Deliverables:
  resources/dashboard/queries/top_10_products_by_revenue.sql
  resources/dashboard/queries/customer_revenue_distribution.sql
  resources/dashboard/queries/customer_segmentation.sql
  resources/dashboard/dashboard_config.md

No changes to src/bronze/, src/silver/, or src/gold/.
No secrets in Git. pytest must still pass (57 passed, 1 skipped at Phase 8).
```

### What was created

| File | Purpose |
|---|---|
| `resources/dashboard/queries/top_10_products_by_revenue.sql` | Widget 1 |
| `resources/dashboard/queries/customer_revenue_distribution.sql` | Widget 2 |
| `resources/dashboard/queries/customer_segmentation.sql` | Widget 3 |
| `resources/dashboard/dashboard_config.md` | Workspace setup + validation checklist |

No `src/` changes. KPIs are computed in Gold — dashboard displays them.

---

## Gold inputs (reference)

| Gold table | Default path | Rows (project data) |
|---|---|---|
| `gold_sales_by_product` | `medallion_eval.gold.gold_sales_by_product` | 500 |
| `gold_revenue_by_customer` | `medallion_eval.gold.gold_revenue_by_customer` | valid customers only |
| `gold_customer_segmentation` | `medallion_eval.gold.gold_customer_segmentation` | 4 |

**Top 10:** `product_name`, `total_revenue` from `gold_sales_by_product`

**Revenue distribution:** `total_revenue` from `gold_revenue_by_customer`

**Segmentation:** `customer_segment`, `total_revenue` (also `customer_count`, `average_revenue` in source)

```sql
SELECT product_name, total_revenue
FROM {catalog}.{gold_schema}.gold_sales_by_product
ORDER BY total_revenue DESC
LIMIT 10;

SELECT total_revenue
FROM {catalog}.{gold_schema}.gold_revenue_by_customer;

SELECT customer_segment, customer_count, average_revenue, total_revenue
FROM {catalog}.{gold_schema}.gold_customer_segmentation
ORDER BY customer_segment;
```

---

## Workspace validation (document in `dashboard_config.md`)

1. Gold tables exist at configured catalog/schema
2. Top 10 query returns ≤10 rows, sorted by revenue DESC
3. Revenue distribution returns one row per valid customer with `total_revenue`
4. Segmentation query returns 4 segment rows
5. Dashboard published with all three widgets (horizontal bar, histogram, bar)
6. No credentials in Git

**Run order:** data gen → `notebooks/02_bronze_ingest.py` → `notebooks/03_silver_transform.py` → `notebooks/04_gold_transform.py` → dashboard.

Publishing in Databricks SQL is manual — not covered by pytest. Document Lakeview vs legacy dashboard choice in `dashboard_config.md`.

**Out of scope:** pipeline code changes, extra widgets, Bronze/Silver/DQ viz, `signup_channel` analysis, automated dashboard tests in pytest.

| # | Acceptance criterion |
|---|---|
| 1 | Three SQL files under `resources/dashboard/queries/` |
| 2 | `dashboard_config.md` with setup and validation |
| 3 | Dashboard published in Databricks with all three visualizations |
| 4 | Top 10: `gold_sales_by_product`, ≤10 rows, horizontal bar |
| 5 | Distribution: `gold_revenue_by_customer`, histogram |
| 6 | Segmentation: `gold_customer_segmentation`, bar chart |
| 7 | Queries reference Gold only |
| 8 | No secrets committed |
| 9 | pytest still 57 passed, 1 skipped |

Dashboard consumes Gold aggregates. DQ problems stay visible in Silver; Gold already excludes invalid records from displayed KPIs.
