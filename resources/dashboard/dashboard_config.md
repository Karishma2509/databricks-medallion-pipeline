# Databricks SQL Dashboard — Setup and Validation Guide

**Phase:** 9 — Dashboard (consumption layer)  
**Prerequisite:** Phase 8 Gold tables populated  
**Specification:** `ai-prompts/07-dashboard.md`

---

## 1. Overview

This dashboard consumes **Gold tables only**. All business logic (valid-record filtering, revenue aggregation, customer segmentation, `lifetime_value_actual`) is implemented in the Phase 8 Gold pipeline (`src/gold/`). Dashboard SQL must **not** recompute KPIs or reference Bronze/Silver tables.

**Required visualizations (one dashboard, three widgets):**

| # | Title | Chart type | SQL asset |
|---|---|---|---|
| 1 | Top 10 Products by Revenue | Horizontal bar | `queries/top_10_products_by_revenue.sql` |
| 2 | Customer Revenue Distribution | Histogram | `queries/customer_revenue_distribution.sql` |
| 3 | Customer Segmentation | Bar chart | `queries/customer_segmentation.sql` |

---

## 2. Catalog and Schema Configuration

| Setting | Default | Override |
|---|---|---|
| Catalog | `medallion_eval` | `DATABRICKS_CATALOG` or workspace-specific catalog |
| Gold schema | `gold` | `GOLD_SCHEMA` |

**Qualified table names (default):**

| Gold table | Default path |
|---|---|
| `gold_sales_by_product` | `medallion_eval.gold.gold_sales_by_product` |
| `gold_revenue_by_customer` | `medallion_eval.gold.gold_revenue_by_customer` |
| `gold_customer_segmentation` | `medallion_eval.gold.gold_customer_segmentation` |

If your workspace uses different catalog/schema names, update the `FROM` clauses in each SQL file before creating dashboard queries, or use Databricks SQL query parameters if your environment supports them.

**Unity Catalog:** Not required by the approved design. Tables may also resolve via Hive metastore paths depending on workspace configuration.

---

## 3. Gold Table Dependencies

Run the pipeline in order before validating the dashboard:

1. Phase 5 — generate CSVs (`data/raw/`)
2. Phase 6 — Bronze (`notebooks/02_bronze_ingest.py`)
3. Phase 7 — Silver (`notebooks/03_silver_transform.py`)
4. Phase 8 — Gold (`notebooks/04_gold_transform.py`)

**Expected row counts (project data):**

| Table | Rows |
|---|---|
| `gold_sales_by_product` | 500 |
| `gold_revenue_by_customer` | valid Silver customers only |
| `gold_customer_segmentation` | 4 |

---

## 4. SQL Asset Locations

| File | Purpose |
|---|---|
| `resources/dashboard/queries/top_10_products_by_revenue.sql` | Top 10 products by `total_revenue` DESC |
| `resources/dashboard/queries/customer_revenue_distribution.sql` | Per-customer `total_revenue` for histogram |
| `resources/dashboard/queries/customer_segmentation.sql` | Segment rollups for bar chart |

---

## 5. Query-to-Visualization Mapping

### 5.1 Top 10 Products by Revenue

| Property | Value |
|---|---|
| SQL file | `top_10_products_by_revenue.sql` |
| Gold source | `gold_sales_by_product` |
| Columns used | `product_name`, `total_revenue` |
| Chart type | **Horizontal bar chart** |
| X / value axis | `total_revenue` |
| Y / label axis | `product_name` |
| Row limit | ≤ 10 (`LIMIT 10` in SQL) |
| Sort | `total_revenue DESC` (in SQL) |

### 5.2 Customer Revenue Distribution

| Property | Value |
|---|---|
| SQL file | `customer_revenue_distribution.sql` |
| Gold source | `gold_revenue_by_customer` |
| Columns used | `total_revenue` |
| Chart type | **Histogram** |
| Measure | `total_revenue` (one value per valid customer row) |

**Manual UI configuration required:** Histogram **bin boundaries** are not specified in the approved design and cannot be set in the SQL asset. When adding the visualization in Databricks SQL, configure bin count or bin width in the histogram widget settings.

### 5.3 Customer Segmentation

| Property | Value |
|---|---|
| SQL file | `customer_segmentation.sql` |
| Gold source | `gold_customer_segmentation` |
| Columns used | `customer_segment`, `total_revenue` |
| Chart type | **Bar chart** |
| X / category axis | `customer_segment` |
| Y / value axis | `total_revenue` |

**Manual UI configuration (optional):** Segment display order is not specified in the approved design. The SQL returns rows in storage order; reorder in the UI if desired.

**Available but not required for the approved chart:** `customer_count`, `average_revenue` (present in Gold; add to tooltips or secondary series only if desired).

---

## 6. Dashboard Setup Instructions

### Step 1 — Verify Gold tables

In Databricks SQL editor:

```sql
SELECT COUNT(*) FROM medallion_eval.gold.gold_sales_by_product;
SELECT COUNT(*) FROM medallion_eval.gold.gold_revenue_by_customer;
SELECT COUNT(*) FROM medallion_eval.gold.gold_customer_segmentation;
```

Expect `500`, valid-customer count, and `4` respectively on project data.

### Step 2 — Create SQL queries

1. Open **SQL** in the Databricks workspace.
2. Create a new query for each file under `resources/dashboard/queries/`.
3. Paste SQL contents (adjust catalog/schema if needed).
4. Run each query to confirm success.
5. Save queries with descriptive names matching the visualization titles.

### Step 3 — Create the dashboard

1. Create a new **Dashboard** in Databricks SQL (Lakeview or legacy SQL dashboard per workspace capability — not specified in approved design).
2. Add visualization **1**: attach `top_10_products_by_revenue` query → **Horizontal bar chart** → `product_name` vs `total_revenue`.
3. Add visualization **2**: attach `customer_revenue_distribution` query → **Histogram** → `total_revenue` → configure bins in UI.
4. Add visualization **3**: attach `customer_segmentation` query → **Bar chart** → `customer_segment` vs `total_revenue`.
5. Title the dashboard (e.g. `Medallion E-Commerce Sales Dashboard`).
6. Publish or share per workspace policy.

### Step 4 — Optional filters

Dashboard filters/slicers beyond the three widgets are **not required** by the approved design.

---

## 7. Validation Checklist

| # | Check | Pass criteria |
|---|---|---|
| 1 | Gold tables exist | All three tables queryable at configured catalog/schema |
| 2 | Top 10 query | Returns ≤ 10 rows; ordered by `total_revenue` DESC |
| 3 | Revenue distribution query | Returns `total_revenue` per valid customer |
| 4 | Segmentation query | Returns 4 rows with approved segment labels |
| 5 | No Silver/Bronze references | SQL files reference `medallion_eval.gold.*` only |
| 6 | Dashboard renders | All three visualizations display without errors |
| 7 | Chart types | Horizontal bar, histogram, bar chart per spec |
| 8 | No secrets in Git | No tokens or passwords in repository files |

**Approved segment labels:** `No Purchase`, `Low Value`, `Mid Value`, `High Value`

---

## 8. Items Configured Manually in Databricks SQL

| Item | Where configured | Notes |
|---|---|---|
| Catalog/schema substitution | SQL `FROM` clauses or query parameters | Default `medallion_eval.gold` |
| Histogram bin boundaries | Dashboard visualization UI | Not in SQL; not specified in approved design |
| Segment display order | Dashboard visualization UI (optional) | Not specified in approved design |
| Dashboard publish/share permissions | Databricks workspace admin | Not specified in approved design |
| Lakeview vs legacy dashboard type | Workspace UI | Not specified in approved design |

---

## 9. Security and Git Policy

- **Do not commit** Databricks personal access tokens, passwords, or secret scope values to Git.
- Use Databricks workspace authentication and secret scopes for production access.
- Row-level security / table ACLs: **not specified in the approved design**.

---

## 10. Local Validation (Repository)

Phase 9 SQL assets are validated statically in the repository:

- Queries reference Gold tables only (`medallion_eval.gold.*`).
- No KPI recomputation, joins, or Silver/Bronze references.
- Top 10 query includes `ORDER BY total_revenue DESC` and `LIMIT 10`.

**Databricks workspace execution** is required to confirm query runtime success and dashboard rendering. That step is performed manually in the workspace when available.

**Automated pytest:** Existing pipeline tests (`pytest -v`) do not execute dashboard SQL; the 57 passed / 1 skipped baseline must remain unchanged after adding these assets.

---

## 11. Business Logic Remains in Gold

| Concern | Owner layer |
|---|---|
| Valid order/customer filtering | Silver (`is_valid_record`) + Gold exclusion policy |
| `total_revenue`, `total_orders`, `average_order_value` | Gold |
| `lifetime_value_actual` | Gold |
| Customer segmentation thresholds | Gold |
| Product inclusion (all 500 products) | Gold |
| Dashboard presentation | Phase 9 SQL + Databricks UI only |
