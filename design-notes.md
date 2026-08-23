# Design Notes — Databricks Medallion Pipeline

**Phase:** 4 — Solution Design  
**Status:** Approved design baseline for implementation  
**Inputs:** `cursor-workflow/*`, `requirements-analysis.md`, approved design decisions

---

## 1. Purpose

This document captures the technical design for the GenAI evaluation project: an end-to-end e-commerce sales pipeline using Databricks Medallion Architecture (CSV → Bronze → Silver → Gold → Databricks SQL Dashboard).

Detailed schemas live in `data-model.md`. Data-quality rules, issue injection, and flagging live in `data-quality-strategy.md`.

---

## 2. Approved Design Decisions

The following decisions are confirmed and govern all implementation phases:

| # | Decision |
|---|---|
| 1 | Generate exactly **10,000** base customers, **100,000** base orders, and **500** products. |
| 2 | Duplicate injection may increase final CSV row counts. **35** additional order rows are acceptable; final `orders.csv` may contain **100,035** rows. Base vs final counts must be documented. |
| 3 | Use catalog **`medallion_eval`** as the configurable default. Do not hard-code assumptions that require Unity Catalog to exist. |
| 4 | **`lifetime_value_actual` = `total_revenue`** for this evaluation dataset. |
| 5 | Customer segmentation thresholds: **No Purchase** = 0; **Low Value** = >0 and <500; **Mid Value** = >=500 and <2000; **High Value** = >=2000. |
| 6 | **Exclude invalid orders** from Gold revenue calculations; **preserve all rows in Silver**. |
| 7 | Flag **all rows** sharing a duplicated identifier as invalid; do not select a winner. |
| 8 | Referential integrity checks whether the referenced ID **exists in the corresponding Silver entity table**. |
| 9 | Bronze preserves raw business values; **no cleaning, deduplication, or repair**. |
| 10 | Use **pytest and local Spark** for automated testing where practical; Databricks for workspace validation. |
| 11 | Do **not** commit large generated CSV files to Git. Gitignore generated data; retain DQ manifest and documentation for traceability. |
| 12 | Keep **`signup_channel`** as a customer attribute for segmentation context documentation. |

---

## 3. Overall Architecture

### 3.1 Data flow

```
data/raw/*.csv
    → Bronze Delta (raw preserve + metadata)
    → Silver Delta (conform + validate + flags + metrics)
    → Gold Delta (business aggregates from valid data)
    → Databricks SQL Dashboard
```

### 3.2 Layer responsibilities

| Layer | Responsibility | Spec basis |
|---|---|---|
| Source CSV | Raw e-commerce data with intentional DQ issues | Required |
| Bronze | Ingest, preserve, metadata, traceability | Required |
| Silver | Validation, conformance, quality flags, metrics | Required |
| Gold | Business-level aggregations | Required |
| Dashboard | Three required SQL visualizations | Required |

### 3.3 Orchestration (proposed)

| Aspect | Design |
|---|---|
| Core logic | Reusable Python modules under `src/` |
| Databricks execution | Thin notebooks under `notebooks/` that call `src/` |
| Job orchestration | Manual or notebook-driven run sequence for evaluation |
| Storage format | Delta tables |
| Catalog default | `medallion_eval` (configurable; works with Unity Catalog or Hive metastore) |

**Catalog portability:** Configuration supplies catalog and schema names. Implementation must not assume Unity Catalog is enabled. Table references should resolve through configurable catalog/schema paths.

### 3.4 Catalog, schema, and table naming

| Object | Default name | Configurable |
|---|---|---|
| Catalog | `medallion_eval` | Yes |
| Bronze schema | `bronze` | Yes |
| Silver schema | `silver` | Yes |
| Gold schema | `gold` | Yes |
| DQ schema | `dq` | Yes |

**Bronze tables:** `bronze_customers`, `bronze_orders`, `bronze_products`  
**Silver tables:** `silver_customers`, `silver_orders`, `silver_products`  
**Gold tables:** `gold_sales_by_product`, `gold_revenue_by_customer`, `gold_customer_segmentation`  
**DQ tables:** `dq_metrics`, `dq_metrics_by_rule`

---

## 4. Data Generation Strategy

### 4.1 Scale

| Dataset | Base row count | Final row count (after injection) | Row-count change |
|---|---|---|---|
| customers | 10,000 | 10,015 | +15 appended duplicate rows |
| orders | 100,000 | 100,035 | +35 appended duplicate rows (approved) |
| products | 500 | 500 | No row-count injection |

**Base count** = rows in the initial clean generation pass.  
**Final count** = rows written to CSV after all injections (including appended duplicates).  
Bronze row counts must equal final CSV row counts.

See `data-quality-strategy.md` for the full 700-issue injection plan and per-rule expected failure counts.

### 4.2 Generation approach

1. Generate clean base datasets with deterministic seed (`42`).
2. Establish valid FK relationships for the majority of orders.
3. Inject intentional DQ issues per `data/manifests/dq_injection_manifest.csv`.
4. Write CSVs to `data/raw/` (gitignored).
5. Validate generation before Bronze ingest.

### 4.3 Traceability

- `data/manifests/dq_injection_manifest.csv` is the source of truth for injected issues.
- Manifest is committed to Git; raw CSVs are not.

### 4.4 Git policy for data

| Asset | Git policy |
|---|---|
| `data/raw/*.csv` | Gitignored (large generated files) |
| `data/manifests/dq_injection_manifest.csv` | Committed |
| Generation documentation | Committed |

---

## 5. Bronze Layer Design

| Requirement | Design |
|---|---|
| Read CSV | Explicit schema; preserve raw business values |
| Preserve all records | No filtering, deduplication, or repair |
| Delta storage | One table per dataset |
| Metadata | `_ingest_batch_id`, `_ingest_timestamp`, `_source_file`, `_source_row_number`, `_bronze_record_id` |
| Cleaning | None |

Bronze may read business columns as strings to avoid silent type coercion. Type casting and trimming occur in Silver only.

---

## 6. Silver Layer Design

| Requirement | Design |
|---|---|
| Validate Bronze | Separate modules per rule category |
| Conform | Trim strings, cast types, compute `line_revenue` |
| Preserve rows | Same row count as Bronze per entity |
| Quality flags | Per-rule booleans + `is_valid_record` |
| Incremental checks | completeness → uniqueness → referential integrity |

See `data-quality-strategy.md` for flag definitions and metrics.

---

## 7. Gold Layer Design

### 7.1 Input filter policy

| Input | Gold treatment |
|---|---|
| Orders with any failed order-level DQ flag | **Excluded** from revenue aggregations |
| Invalid orders | **Preserved in Silver** for audit |
| Customers with invalid email or duplicate ID | Excluded from customer-level Gold metrics |
| Customers with zero valid orders | Included with zero revenue in `gold_revenue_by_customer` |

### 7.2 Business formulas

| Metric | Formula |
|---|---|
| `line_revenue` | `quantity * unit_price` (computed in Silver) |
| `total_revenue` | `SUM(line_revenue)` over valid orders |
| `total_orders` | `COUNT(DISTINCT order_id)` over valid orders |
| `average_order_value` | `total_revenue / total_orders`; null if `total_orders = 0` |
| `lifetime_value_actual` | **Equal to `total_revenue`** |

### 7.3 Customer segmentation

Derived at Gold build time from valid-order revenue per customer:

| Segment | Rule (`total_revenue`) |
|---|---|
| No Purchase | = 0 |
| Low Value | > 0 and < 500 |
| Mid Value | >= 500 and < 2000 |
| High Value | >= 2000 |

`signup_channel` is retained on the customer record as contextual attribute (e.g. web, mobile, referral) but segmentation is revenue-based, not channel-based.

### 7.4 Gold outputs

| Table | Purpose |
|---|---|
| `gold_sales_by_product` | Product-level sales aggregates |
| `gold_revenue_by_customer` | Customer-level revenue and LTV |
| `gold_customer_segmentation` | Segment-level rollups |

Gold tables are materialized Delta tables, rebuilt per pipeline run (`overwrite`).

---

## 8. Databricks SQL Dashboard Design

| # | Visualization | Gold source | Chart type |
|---|---|---|---|
| 1 | Top 10 Products by Revenue | `gold_sales_by_product` | Horizontal bar chart |
| 2 | Customer Revenue Distribution | `gold_revenue_by_customer` | Histogram of `total_revenue` |
| 3 | Customer Segmentation | `gold_customer_segmentation` | Bar chart (`customer_segment` vs `total_revenue`) |

**Query assets:** `resources/dashboard/queries/*.sql`  
**Setup guide:** `resources/dashboard/dashboard_config.md`

---

## 9. Project Organization

```
configs/config.yaml           # catalog, paths, thresholds (to be populated in later phase)
data/raw/                     # generated CSVs (gitignored)
data/manifests/               # DQ injection manifest (committed)
notebooks/                    # thin Databricks orchestration notebooks
resources/dashboard/          # SQL queries and dashboard docs
src/
  common/                     # config, schemas, spark session helpers
  data_generation/
  bronze/
  silver/                     # completeness, uniqueness, referential_integrity
  gold/
tests/                        # pytest + local Spark
```

---

## 10. Configuration Approach

Configuration will be externalized in `configs/config.yaml` (future phase). Non-secret settings include:

- Catalog and schema names (default `medallion_eval`)
- Raw data and manifest paths
- Generation seed and base row counts
- Segmentation thresholds
- Expected DQ failure counts per rule

Secrets (Databricks tokens, passwords) must use environment variables or Databricks secret scopes — never committed to Git.

Environment overrides (e.g. `DATABRICKS_CATALOG`, `MEDALLION_RAW_PATH`) allow workspace-specific deployment without code changes.

---

## 11. Testing Strategy

| Level | Tooling | Scope |
|---|---|---|
| Unit / integration | pytest + local SparkSession | Data generation, Bronze, Silver flags, Gold calculations |
| Workspace validation | Databricks notebooks / manual runs | End-to-end pipeline and dashboard |

Tests assert manifest-aligned DQ counts and Gold calculation correctness on fixtures and full generated data.

---

## 12. Git Development Strategy

| Practice | Approach |
|---|---|
| Branching | `cursor/phase-<n>-<description>` feature branches |
| Commits | Meaningful milestones: design, data generation, Bronze, Silver, Gold, tests, dashboard, docs |
| Secrets | Never committed |
| Generated CSVs | Gitignored; manifest committed |

---

## 13. Related Documents

| Document | Contents |
|---|---|
| `data-model.md` | Schemas, tables, columns, relationships |
| `data-quality-strategy.md` | DQ rules, injection plan, flags, metrics, testing alignment |
| `requirements-analysis.md` | Requirements baseline (Phase 3) |
