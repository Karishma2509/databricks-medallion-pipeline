# Data Quality Strategy — Databricks Medallion Pipeline

**Phase:** 4 — Solution Design  
**Status:** Approved design baseline  
**Related:** `design-notes.md`, `data-model.md`

---

## 1. Purpose

This document defines:

- Required data-quality rules (from project specification)
- Intentional issue injection plan (~700 problematic records)
- Silver-layer flagging approach
- Quality metrics and testing alignment
- Gold-layer treatment of failed records

**Core principle:** Never hide data-quality problems by deleting bad records. Issues must be identified, flagged, measurable, and documented.

---

## 2. Required Quality Rules (Specification)

| Category | Entity | Field / Check | Spec requirement |
|---|---|---|---|
| Completeness | customers | `email` | Required |
| Completeness | orders | `customer_id` | Required |
| Completeness | orders | `product_id` | Required |
| Uniqueness | customers | `customer_id` | Required |
| Uniqueness | orders | `order_id` | Required |
| Referential integrity | orders | `customer_id` → `customers.customer_id` | Required |
| Referential integrity | orders | `product_id` → `products.product_id` | Required |

Products have no required DQ rules beyond serving as an RI reference target.

---

## 3. Intentional Data-Quality Issue Injection

### 3.1 Objectives

- Inject approximately **700 issue instances** detectable by Silver-layer rules.
- Maintain a **traceability manifest** committed to Git.
- Keep generated CSV files gitignored.

### 3.2 Base vs final row counts

| Dataset | Base rows | Injected duplicate rows | Other injections (replace/null/orphan) | Final CSV rows |
|---|---|---|---|---|
| customers | 10,000 | +15 | Completeness/uniqueness modify existing rows in place | **10,015** |
| orders | 100,000 | +35 | Completeness/RI modify existing rows in place | **100,035** |
| products | 500 | 0 | None | **500** |

**Clarification:**

- **Base count:** Rows generated in the initial clean pass.
- **Duplicate injection:** Additional rows appended with duplicated keys (increases file row count).
- **In-place injection:** Missing values, orphan FKs applied to existing rows (does not change row count).

### 3.3 Issue distribution (700 total issue instances)

Each row below represents one **detectable failure instance** on a specific record. The manifest tracks every injection.

| # | Dataset | Rule category | Issue | Injected instances | `issue_code` | Affects row count? |
|---|---|---|---|---|---|---|
| 1 | customers | Completeness | Missing `email` (null or blank) | 50 | `CUST_EMAIL_MISSING` | In-place |
| 2 | customers | Uniqueness | Duplicate `customer_id` (all rows sharing key flagged) | 30 | `CUST_ID_DUPLICATE` | +15 appended rows |
| 3 | orders | Completeness | Missing `customer_id` | 100 | `ORD_CUST_ID_MISSING` | In-place |
| 4 | orders | Completeness | Missing `product_id` | 100 | `ORD_PROD_ID_MISSING` | In-place |
| 5 | orders | Uniqueness | Duplicate `order_id` (all rows sharing key flagged) | 70 | `ORD_ID_DUPLICATE` | +35 appended rows |
| 6 | orders | Referential integrity | Invalid `customer_id` (orphan) | 200 | `ORD_CUST_ID_INVALID` | In-place |
| 7 | orders | Referential integrity | Invalid `product_id` (orphan) | 150 | `ORD_PROD_ID_INVALID` | In-place |
| | | | **Total** | **700** | | |

### 3.4 Uniqueness injection detail

| Entity | Duplicate pairs | Appended rows | Rows flagged `is_*_unique = false` |
|---|---|---|---|
| `customer_id` | 15 | 15 | 30 (both original and duplicate) |
| `order_id` | 35 | 35 | 70 (both original and duplicate) |

**Approved rule:** Flag **all rows** sharing a duplicated identifier as invalid. Do not select a winner.

### 3.5 Overlap policy

- Keep issue cohorts **mutually exclusive** per manifest row where possible.
- Do not inject overlapping failures on the same record in the initial manifest (simplifies per-rule test assertions).
- Overlap across rules on the same row may be introduced in a future iteration only if needed; not part of the initial 700.

### 3.6 Traceability manifest

**File:** `data/manifests/dq_injection_manifest.csv` (committed to Git)

| Column | Description |
|---|---|
| `manifest_id` | Unique issue identifier |
| `dataset` | `customers`, `orders`, or `products` |
| `business_key` | `customer_id` or `order_id` |
| `source_row_number` | 1-based row number in final CSV |
| `issue_code` | Stable code from table above |
| `rule_category` | `completeness`, `uniqueness`, `referential_integrity` |
| `field_name` | Affected column |
| `notes` | Human-readable description |

**Generation validation** must confirm:

- Final row counts match documented base + appended duplicates.
- Per-rule failure counts match manifest totals.
- Every manifest entry is locatable by `business_key` and/or `source_row_number`.

---

## 4. Layer-Specific DQ Responsibilities

### 4.1 Bronze

| Responsibility | Policy |
|---|---|
| Preserve raw values | Yes — no trimming, casting fixes, dedup, or repair |
| Detect DQ issues | No — detection is Silver responsibility |
| Remove bad rows | **Prohibited** |

### 4.2 Silver

| Responsibility | Policy |
|---|---|
| Validate per required rules | Yes — incremental, separate modules per category |
| Conform types | Yes — trim, cast, compute `line_revenue` |
| Flag failures | Yes — per-rule booleans + `is_valid_record` |
| Delete bad rows | **Prohibited** |
| Produce metrics | Yes — `dq_metrics`, `dq_metrics_by_rule` |

### 4.3 Gold

| Responsibility | Policy |
|---|---|
| Use invalid orders in revenue | **No** — exclude `is_valid_record = false` orders |
| Preserve invalid orders | Yes — they remain in Silver for audit |
| Use invalid customers | **No** — exclude `is_valid_record = false` customers from customer Gold |

---

## 5. Silver Quality Flag Definitions

### 5.1 Completeness rules

| Flag | Entity | Condition for `true` |
|---|---|---|
| `is_email_complete` | customers | `email` is not null and `trim(email) != ''` |
| `is_customer_id_complete` | orders | `customer_id` is not null and `trim(customer_id) != ''` |
| `is_product_id_complete` | orders | `product_id` is not null and `trim(product_id) != ''` |

Null and blank (after trim) are both treated as missing.

### 5.2 Uniqueness rules

| Flag | Entity | Condition for `true` |
|---|---|---|
| `is_customer_id_unique` | customers | `customer_id` appears exactly once in `silver_customers` |
| `is_order_id_unique` | orders | `order_id` appears exactly once in `silver_orders` |

When duplicates exist, **all** rows sharing the key receive `false`.

### 5.3 Referential integrity rules

| Flag | Entity | Condition for `true` |
|---|---|---|
| `is_customer_id_valid_ref` | orders | `customer_id` exists in `silver_customers.customer_id` |
| `is_product_id_valid_ref` | orders | `product_id` exists in `silver_products.product_id` |

**Approved rule:** Check existence in the corresponding Silver entity table. Do not require the referenced row to pass its own validity flags.

**Evaluation order note:** RI checks run after Silver customer/product tables are populated. Orphan IDs injected into orders must not exist in the reference table.

### 5.4 Overall validity

| Entity | `is_valid_record` formula |
|---|---|
| customers | `is_email_complete AND is_customer_id_unique` |
| orders | `is_customer_id_complete AND is_product_id_complete AND is_order_id_unique AND is_customer_id_valid_ref AND is_product_id_valid_ref` |
| products | always `true` |

### 5.5 Optional diagnostic column

| Column | Purpose |
|---|---|
| `dq_failure_reasons` | Array of `issue_code` values for failed rules on that row |

---

## 6. Quality Metrics

### 6.1 Run-level metrics (`dq_metrics`)

Captured after each Silver pipeline run:

| Metric | Definition |
|---|---|
| `total_records` | Row count per Silver entity table |
| `valid_records` | Count where `is_valid_record = true` |
| `invalid_records` | Count where `is_valid_record = false` |
| `valid_record_pct` | `valid_records / total_records` |

### 6.2 Rule-level metrics (`dq_metrics_by_rule`)

| Metric | Definition |
|---|---|
| `failed_record_count` | Rows where the specific rule flag is `false` |
| `expected_failed_count` | Value from injection manifest / config |

### 6.3 Expected failure counts (from injection plan)

| `issue_code` | `expected_failed_count` |
|---|---|
| `CUST_EMAIL_MISSING` | 50 |
| `CUST_ID_DUPLICATE` | 30 |
| `ORD_CUST_ID_MISSING` | 100 |
| `ORD_PROD_ID_MISSING` | 100 |
| `ORD_ID_DUPLICATE` | 70 |
| `ORD_CUST_ID_INVALID` | 200 |
| `ORD_PROD_ID_INVALID` | 150 |
| **Total** | **700** |

Tests must assert `failed_record_count = expected_failed_count` for each rule after full pipeline run on generated data.

---

## 7. Gold Treatment of Failed Records

### 7.1 Orders

| Order state | Silver | Gold revenue aggregations |
|---|---|---|
| `is_valid_record = true` | Preserved | **Included** |
| `is_valid_record = false` | Preserved | **Excluded** |

Invalid orders must not contribute to `total_revenue`, `total_orders`, `average_order_value`, or product/customer rollups.

### 7.2 Customers

| Customer state | Silver | Gold customer metrics |
|---|---|---|
| `is_valid_record = true` | Preserved | **Included** (zero revenue allowed) |
| `is_valid_record = false` | Preserved | **Excluded** from `gold_revenue_by_customer` and segment counts |

### 7.3 Segmentation impact

Segments are computed only from valid customers based on revenue from valid orders. A customer with invalid email but valid orders will not appear in Gold (customer invalid). An invalid order will not contribute to any customer's revenue.

---

## 8. Testing Strategy Alignment

### 8.1 Test tooling

| Approach | Use |
|---|---|
| pytest + local SparkSession | Automated unit and integration tests |
| Databricks workspace | End-to-end validation and dashboard verification |

### 8.2 Required test coverage

| Test area | Assertion |
|---|---|
| Missing required values | Per-rule counts match manifest (50 / 100 / 100) |
| Duplicate identifiers | 30 customer rows and 70 order rows flagged non-unique |
| Invalid customer references | 200 orders flagged `is_customer_id_valid_ref = false` |
| Invalid product references | 150 orders flagged `is_product_id_valid_ref = false` |
| Gold calculations | Known fixture totals; AOV = revenue / orders |
| `lifetime_value_actual` | Equals `total_revenue` on fixture data |
| Invalid order exclusion | Injected bad orders do not affect Gold totals |
| Bronze row parity | Bronze row count = final CSV row count |
| Manifest traceability | Every manifest row locatable in source/Silver |

### 8.3 Test fixtures

| Fixture | Purpose |
|---|---|
| `tests/fixtures/minimal_*.csv` | Small datasets covering each rule |
| `tests/fixtures/manifest_expected_counts.json` | Per-rule expected failures |
| `tests/fixtures/gold_expected.json` | Expected Gold aggregates on minimal set |

### 8.4 Incremental Silver implementation

Implement and test checks in this order (per cursor-rules):

1. Completeness
2. Uniqueness
3. Referential integrity
4. Quality metrics

Each category must be a separate, reviewable module — not one opaque transformation.

---

## 9. Git and Data Traceability

| Asset | Git policy | Purpose |
|---|---|---|
| `data/raw/*.csv` | **Gitignored** | Large generated files |
| `data/manifests/dq_injection_manifest.csv` | **Committed** | Traceability and test expectations |
| `data-quality-strategy.md` | **Committed** | Rule definitions and injection plan |
| Generation validation output | Committed as test artifact or logged in docs | Confirms counts |

---

## 10. Implementation Checklist (Phase 5+)

- [ ] Generate base datasets: 10,000 / 100,000 / 500
- [ ] Inject 700 issues per manifest
- [ ] Produce final CSVs: 10,015 / 100,035 / 500 rows
- [ ] Write and commit `dq_injection_manifest.csv`
- [ ] Validate generation counts before Bronze
- [ ] Implement Silver flags per Section 5
- [ ] Implement `dq_metrics` tables per Section 6
- [ ] Verify Gold excludes invalid orders per Section 7
- [ ] Run pytest suite per Section 8
