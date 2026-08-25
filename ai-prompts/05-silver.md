# Phase 7 — Silver Layer — Cursor Prompt History

## Prompt 1 — Implement Silver transformation and DQ

### What I asked Cursor

```
Bronze is done — bronze_customers (10,015), bronze_orders (100,035),
bronze_products (500) under data/delta/medallion_eval/bronze/. Phase 7 is Silver.

Read data-model.md, data-quality-strategy.md, design-notes.md.
Implement under src/silver/ with separate modules per DQ concern — don't stuff
everything into one transform.

Keep validation logic in separate files so we can review each DQ rule.

Silver must:
1. Read Bronze with no row loss
2. Conformance (conformance.py): trim strings; cast quantity, unit_price,
   list_price, dates, is_active; compute line_revenue = quantity * unit_price
   on orders
3. DQ flags in separate files: completeness.py, uniqueness.py,
   referential_integrity.py, validity.py
4. is_valid_record + optional dq_failure_reasons (approved issue_code values only)
5. Write silver_customers, silver_orders, silver_products — row counts = Bronze
6. Write dq_metrics and dq_metrics_by_rule to medallion_eval.dq

Execution order: Products → Customers → Orders → Metrics
(orders RI needs silver customer/product ID sets)

Seven DQ rules / expected failed_record_count:
  CUST_EMAIL_MISSING          50
  CUST_ID_DUPLICATE           30
  ORD_CUST_ID_MISSING        100
  ORD_PROD_ID_MISSING        100
  ORD_ID_DUPLICATE            70
  ORD_CUST_ID_INVALID        200
  ORD_PROD_ID_INVALID        150

Completeness flags:
  is_email_complete (customers.email)
  is_customer_id_complete, is_product_id_complete (orders)

Uniqueness flags:
  is_customer_id_unique, is_order_id_unique
  When duplicates exist, flag ALL rows sharing the key — no winner, no dedup.

RI flags:
  is_customer_id_valid_ref, is_product_id_valid_ref
  Check ID exists in Silver entity table; referenced row doesn't need
  is_valid_record = true.
  Missing FK values must NOT double-count as RI failures (disjoint from
  completeness — keeps per-rule counts aligned with injection manifest).

is_valid_record:
  customers: is_email_complete AND is_customer_id_unique
  orders: all five order flags ANDed
  products: always true

Add tests/test_silver.py, extend tests/conftest.py.
Thin notebook notebooks/03_silver_transform.py.
Run pytest -v. No Gold yet. Don't change Bronze or data generation.
```

### What we built

| Module | Role |
|---|---|
| `schemas.py` | Output schemas, column lists, `ISSUE_CODES` |
| `conformance.py` | Trim, cast, `line_revenue` |
| `completeness.py` | `is_email_complete`, `is_customer_id_complete`, `is_product_id_complete` |
| `uniqueness.py` | `is_customer_id_unique`, `is_order_id_unique` |
| `referential_integrity.py` | `is_customer_id_valid_ref`, `is_product_id_valid_ref` |
| `validity.py` | `is_valid_record`, `dq_failure_reasons` |
| `metrics.py` | `dq_metrics`, `dq_metrics_by_rule` |
| `transform.py` | Entity pipeline orchestration |
| `run_silver.py` | Entry point |

**Inputs / outputs:**

| Bronze table | Rows | Silver output |
|---|---|---|
| `bronze_customers` | 10,015 | `silver_customers` |
| `bronze_orders` | 100,035 | `silver_orders` |
| `bronze_products` | 500 | `silver_products` |

Bronze metadata carried through: `_ingest_batch_id`, `_ingest_timestamp`, `_source_file`, `_source_row_number`, `_bronze_record_id`.

**`dq_metrics`** — 3 rows/run: `metric_run_id`, `metric_timestamp`, `dataset`, `total_records`, `valid_records`, `invalid_records`, `valid_record_pct`

**`dq_metrics_by_rule`** — 7 rows/run: `metric_run_id`, `dataset`, `rule_code`, `rule_category`, `failed_record_count`, `expected_failed_count`

**Results at Silver completion:** 39 passed (~105s): data gen 10, Bronze 12, Silver 17. `array_compact()` in `dq_failure_reasons` for PySpark 3.5.

---

## Prompt 2 — Databricks follow-up (Unity Catalog)

### What I asked Cursor

```
Local Silver is in place and pytest is green. Bronze already runs on Databricks
Free Edition (workspace.bronze.bronze_*). Adapt the same Silver transformation
for Databricks — extend the execution_mode pattern from Bronze. Don't change DQ
rules or row-count expectations.

Keep the local path working for pytest.

Local (keep for pytest):
- Read Bronze: data/delta/medallion_eval/bronze/*
- Write Silver: data/delta/medallion_eval/silver/*
- Write DQ: data/delta/medallion_eval/dq/*

Databricks:
- Read Bronze: workspace.bronze.bronze_customers, bronze_orders, bronze_products
  via spark.table()
- Write Silver: workspace.silver.silver_* via saveAsTable()
- Write DQ: workspace.dq.dq_metrics, workspace.dq.dq_metrics_by_rule via saveAsTable()

Extend SilverSettings in src/common/config.py.
Update src/silver/transform.py and src/silver/metrics.py for mode-aware I/O.

Fix notebooks/03_silver_transform.py — it was calling load_silver_settings()
before importing it. Put src/ on path first, then import, then:

  settings = load_silver_settings(execution_mode=EXECUTION_MODE_DATABRICKS)
  result = run_silver_transformation(spark, settings=settings)

This is a follow-up to the local Silver implementation — build on what's
already there. Don't change Silver business logic. Don't touch Gold.
Keep pytest -v at 57 passed, 1 skipped.
```

### What changed

- `SilverSettings.execution_mode`, `is_local`, `is_databricks`, storage label helpers
- `transform.py` — mode-aware read/write for Bronze/Silver/DQ
- `metrics.py` — `saveAsTable()` for DQ in Databricks mode
- `run_silver.py` — optional `settings`
- `notebooks/03_silver_transform.py` — import order + explicit Databricks settings
- `tests/conftest.py` — `EXECUTION_MODE_LOCAL`

```
MEDALLION_EXECUTION_MODE=databricks
DATABRICKS_CATALOG=workspace
BRONZE_SCHEMA=bronze
SILVER_SCHEMA=silver
DQ_SCHEMA=dq
```

Full-suite baseline after Gold tests: **57 passed, 1 skipped**.

---

## Quick reference

| Item | Local | Databricks |
|---|---|---|
| Catalog | `medallion_eval` | `workspace` |
| Silver schema | `silver` | `silver` |
| DQ schema | `dq` | `dq` |
| Manifest | `data/manifests/dq_injection_manifest.csv` | same |

Silver finds and measures DQ problems — never deletes or hides them. Gold excludes invalid rows later.
