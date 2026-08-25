# Data Generation Phase — Cursor Prompt History

## Prompt 1 — Phase 5 Data Generation

### What I asked Cursor

```
Design docs are signed off (design-notes.md, data-model.md,
data-quality-strategy.md). Phase 5 is generating the CSVs Bronze will ingest.
Data generation only — leave Bronze, Silver, Gold, and dashboard alone.

Read the workflow docs and design files first.

Implement under src/data_generation/:
- Deterministic base data, seed 42: 10,000 customers, 100,000 orders, 500 products
- Inject exactly 700 DQ issues per data-quality-strategy.md
- Write data/manifests/dq_injection_manifest.csv with row-level traceability
- Final CSVs in data/raw/: customers 10,015, orders 100,035, products 500
- Tests in tests/test_data_generation.py

Row counts and issue distribution need to match the design — Silver tests will
depend on them. Run generator + pytest before we're done. Don't commit yet.
```

### What we built

| Step | Component |
|---|---|
| 1 | `generators.py` — base products, customers, orders |
| 2 | `inject_dq_issues.py` — disjoint cohort injection + manifest rows |
| 3 | `io.py` + `run_generator.py` — write outputs |
| 4 | `tests/test_data_generation.py` |
| 5 | `pytest` |

Deterministic CSVs that Bronze will ingest: clean base scale, 700 traceable DQ issues, manifest linking each issue to a CSV row.

---

## Package layout (`src/data_generation/`)

| Module | Responsibility |
|---|---|
| `config.py` | Seed, row counts, schemas, issue definitions |
| `generators.py` | Base generation |
| `inject_dq_issues.py` | DQ injection + manifest |
| `io.py` | CSV/manifest I/O |
| `run_generator.py` | Orchestration + internal validation |

**Decisions:**

- Seeds: `42`, `43`, `44` per entity via `random.Random`
- IDs: `CUST-{5-digit}`, `ORD-{7-digit}`, `PROD-{3-digit}`
- `line_revenue` not in CSV — Silver computes it
- Disjoint index cohorts per DQ rule (easier test assertions)
- Duplicates: copies appended at end (15 customer pairs, 35 order pairs)
- Missing values: blank strings
- Orphan FKs: `CUST-INVALID-{nnn}`, `PROD-INVALID-{nnn}`
- `data/raw/*.csv` gitignored; manifest committed
- Run: `PYTHONPATH=src python -m data_generation.run_generator`

---

## Files created / modified

| File | Purpose |
|---|---|
| `src/data_generation/*` | Generator package |
| `tests/test_data_generation.py` | 10 validation tests |
| `tests/fixtures/manifest_expected_counts.json` | Per-rule expected counts |
| `requirements-dev.txt` | pytest |
| `.gitignore` | `data/raw/*.csv`, Python artifacts |

**Outputs:**

| File | Git | Rows |
|---|---|---|
| `data/raw/customers.csv` | Ignored | 10,015 |
| `data/raw/orders.csv` | Ignored | 100,035 |
| `data/raw/products.csv` | Ignored | 500 |
| `data/manifests/dq_injection_manifest.csv` | Committed | 700 entries |

---

## DQ distribution (700 total)

| Issue Code | Category | Dataset | Count |
|---|---|---|---|
| `CUST_EMAIL_MISSING` | completeness | customers | 50 |
| `CUST_ID_DUPLICATE` | uniqueness | customers | 30 |
| `ORD_CUST_ID_MISSING` | completeness | orders | 100 |
| `ORD_PROD_ID_MISSING` | completeness | orders | 100 |
| `ORD_ID_DUPLICATE` | uniqueness | orders | 70 |
| `ORD_CUST_ID_INVALID` | referential_integrity | orders | 200 |
| `ORD_PROD_ID_INVALID` | referential_integrity | orders | 150 |

Uniqueness: 15 customer duplicate pairs (+15 rows, 30 flagged); 35 order pairs (+35 rows, 70 flagged).

---

## Validation

`run_generator.py` asserts counts and manifest before write.

**pytest (10 tests):** determinism, final row counts, schemas, baseline ID uniqueness, clean FKs, manifest size, per-code counts, traceability to CSV, issue types present, disjoint cohorts.

```
10 passed in 9.83s
```

Manifest IDs `DQ-0001` … `DQ-0700`. No PySpark in Phase 5 — stdlib `csv` + `random`. Needs `PYTHONPATH=src`.

**Out of scope:** Bronze, Silver, Gold, dashboard, `configs/config.yaml`, notebooks. Phase 6 (Bronze) is next.
