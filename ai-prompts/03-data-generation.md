# Data Generation Phase — Cursor Prompt History

## Prompt 1 — Phase 5 Data Generation Implementation

### Prompt Sent to Cursor

We are now starting Phase 5 — Data Generation.

This is an incremental implementation task. Do NOT implement later phases.

Before making any changes, inspect these existing project documents:

- cursor-workflow/project-context.md
- cursor-workflow/spec.md
- cursor-workflow/cursor-rules-or-instructions.md
- cursor-workflow/task-breakdown.md
- requirements-analysis.md
- design-notes.md
- data-model.md
- data-quality-strategy.md
- ai-prompts/03-data-generation.md

Treat the approved Phase 4 design documents as the source of truth.

**Phase 5 scope — data generation only:**

- Implement data generation under `src/data_generation/`
- Generate deterministic base datasets using seed `42` (10,000 customers, 100,000 orders, 500 products)
- Inject exactly 700 approved DQ issue instances per `data-quality-strategy.md`
- Create `data/manifests/dq_injection_manifest.csv` with full traceability
- Write final CSVs to `data/raw/` with approved final row counts (customers: 10,015; orders: 100,035; products: 500)
- Create Phase 5 validation tests under `tests/`
- Do NOT implement Bronze, Silver, Gold, dashboard, or Databricks workflows
- Do NOT commit changes

### Cursor Response — Implementation Plan

Before implementing, Cursor:

1. Read the approved Phase 4 design documents (`design-notes.md`, `data-model.md`, `data-quality-strategy.md`) and related workflow files.
2. Confirmed no contradictions or blocking ambiguities between the Phase 4 design and the Phase 5 requirements.
3. Proposed an incremental implementation plan:

| Step | Component |
|---|---|
| 1 | `generators.py` — deterministic base products, customers, and orders |
| 2 | `inject_dq_issues.py` — controlled DQ injection on disjoint index cohorts |
| 3 | `io.py` + `run_generator.py` — write CSVs and manifest |
| 4 | `tests/test_data_generation.py` — Phase 5 validation tests |
| 5 | Run generator and pytest to validate outputs |

---

## Phase 5 Objective

Implement deterministic source CSV data generation for the Databricks Medallion Pipeline evaluation project, including:

- Clean base datasets at approved scale
- Controlled injection of exactly 700 intentional data-quality issues
- A traceability manifest linking every injected issue to the generated CSV rows
- Automated validation tests confirming determinism, schemas, row counts, and issue distribution

This phase produces the raw source files consumed by Bronze ingestion in Phase 6.

---

## Implementation Approach

Cursor implemented a modular Python package under `src/data_generation/`:

| Module | Responsibility |
|---|---|
| `config.py` | Seed, row counts, column schemas, issue definitions |
| `generators.py` | Deterministic base generation for products, customers, orders |
| `inject_dq_issues.py` | Disjoint-cohort DQ injection and manifest entry creation |
| `io.py` | CSV and manifest read/write helpers |
| `run_generator.py` | End-to-end pipeline orchestration and internal validation |

**Key design choices applied during implementation:**

- **Determinism:** `random.Random` with fixed seeds (`42`, `43`, `44`) per entity type.
- **ID formats:** `CUST-{5-digit}`, `ORD-{7-digit}`, `PROD-{3-digit}` per `data-model.md`.
- **Revenue fields:** `quantity` and `unit_price` generated on orders; `line_revenue` deferred to Silver.
- **Disjoint cohorts:** Each DQ rule targets a non-overlapping index range to simplify per-rule test assertions.
- **Duplicate injection:** Original rows retained; duplicate copies appended at end of dataset (15 customer pairs, 35 order pairs).
- **Missing values:** Injected as blank strings in CSV.
- **Orphan FKs:** `CUST-INVALID-{nnn}` and `PROD-INVALID-{nnn}` IDs that do not exist in reference tables.
- **Git policy:** `data/raw/*.csv` gitignored; manifest committed for traceability.
- **Execution:** Run via `PYTHONPATH=src python -m data_generation.run_generator`.

---

## Files Created / Modified

### Created — `src/data_generation/`

| File | Purpose |
|---|---|
| `__init__.py` | Package marker |
| `config.py` | Constants, schemas, issue definitions |
| `generators.py` | Base dataset generators |
| `inject_dq_issues.py` | DQ injection and manifest entries |
| `io.py` | CSV/manifest I/O |
| `run_generator.py` | Pipeline entry point |

### Created — tests and supporting files

| File | Purpose |
|---|---|
| `tests/test_data_generation.py` | 10 Phase 5 validation tests |
| `tests/fixtures/manifest_expected_counts.json` | Expected per-rule issue counts |
| `requirements-dev.txt` | pytest dependency |

### Modified

| File | Change |
|---|---|
| `.gitignore` | Added `data/raw/*.csv` and Python artifact patterns |

### Generated outputs

| File | Git policy | Row count |
|---|---|---|
| `data/raw/customers.csv` | Gitignored | 10,015 |
| `data/raw/orders.csv` | Gitignored | 100,035 |
| `data/raw/products.csv` | Gitignored | 500 |
| `data/manifests/dq_injection_manifest.csv` | Committed (traceability) | 700 issue entries |

**Not modified:** Bronze, Silver, Gold, notebooks, configs, README, Phase 4 design docs, other `ai-prompts/` files.

---

## Approved DQ Issue Distribution (700 Total)

| Issue Code | Rule Category | Dataset | Count |
|---|---|---|---|
| `CUST_EMAIL_MISSING` | completeness | customers | 50 |
| `CUST_ID_DUPLICATE` | uniqueness | customers | 30 |
| `ORD_CUST_ID_MISSING` | completeness | orders | 100 |
| `ORD_PROD_ID_MISSING` | completeness | orders | 100 |
| `ORD_ID_DUPLICATE` | uniqueness | orders | 70 |
| `ORD_CUST_ID_INVALID` | referential_integrity | orders | 200 |
| `ORD_PROD_ID_INVALID` | referential_integrity | orders | 150 |
| **Total** | | | **700** |

**Uniqueness detail:**

| Entity | Duplicate pairs | Appended rows | Rows flagged |
|---|---|---|---|
| `customer_id` | 15 | 15 | 30 |
| `order_id` | 35 | 35 | 70 |

---

## Final Generated Row Counts

| Dataset | Base Rows | Final Rows | Change |
|---|---|---|---|
| customers | 10,000 | **10,015** | +15 appended duplicate rows |
| orders | 100,000 | **100,035** | +35 appended duplicate rows |
| products | 500 | **500** | none |

---

## Validation Performed

1. **Internal pipeline validation** in `run_generator.py` — asserts final row counts, manifest size (700), and per-issue-code counts before writing outputs.
2. **Generator execution** — `python -m data_generation.run_generator` produced all CSVs and manifest.
3. **Automated pytest suite** — 10 tests covering:

| Test | Assertion |
|---|---|
| `test_deterministic_generation` | Identical output on repeated runs |
| `test_final_row_counts` | 10,015 / 100,035 / 500 |
| `test_csv_schemas` | Approved column lists per entity |
| `test_base_id_uniqueness_before_injection` | Unique IDs in clean baseline |
| `test_clean_baseline_references_exist` | Valid FKs before injection |
| `test_manifest_has_exactly_700_entries` | Manifest row count |
| `test_manifest_issue_code_counts` | Per-code counts match approved distribution |
| `test_manifest_traceability_to_csv` | Every manifest entry maps to a CSV row |
| `test_injected_issue_types_present` | All issue types detectable in generated data |
| `test_disjoint_issue_cohorts` | No overlapping issue categories on same row |

---

## Test Result

```
10 passed in 9.83s
```

---

## Important Implementation Decisions and Observations

1. **Phase 4 docs used as source of truth** — No design documents were rewritten; no contradictions were found.
2. **Disjoint index cohorts** — Simplifies per-rule counting and aligns with the approved overlap policy in `data-quality-strategy.md`.
3. **Manifest resequencing** — Customer and order manifest entries are combined and assigned sequential `DQ-0001` through `DQ-0700` IDs.
4. **Blank-string missing values** — Completeness failures use empty strings (not omitted columns) to preserve CSV schema.
5. **Orphan ID patterns** — `CUST-INVALID-*` and `PROD-INVALID-*` are guaranteed not to collide with valid generated IDs.
6. **No PySpark in Phase 5** — Generation uses stdlib `csv` and `random`; Spark testing deferred to later phases.
7. **Module execution requires `PYTHONPATH=src`** — Config file not yet populated (deferred to a later phase).
8. **Datasets not regenerated during this documentation step** — Existing validated outputs retained.

---

## Out of Scope (Later Phases)

The following were **NOT** implemented in Phase 5 because they belong to later phases:

- Bronze ingestion
- Silver transformations and DQ checks
- Gold aggregations
- Databricks SQL dashboard
- Databricks Workflows
- `configs/config.yaml` population
- Notebook orchestration

Phase 6 (Bronze) is the next implementation step after review and commit of the Phase 5 milestone.
