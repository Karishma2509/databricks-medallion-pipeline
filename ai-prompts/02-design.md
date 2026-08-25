# Design Phase — Cursor Prompt History

## Prompt 1 — Solution Architecture and Design

### What I asked Cursor

```
Requirements analysis is in requirements-analysis.md. Next step is solution
design for this repo — still no code.

Read:
- cursor-workflow/project-context.md
- cursor-workflow/spec.md
- cursor-workflow/cursor-rules-or-instructions.md
- cursor-workflow/task-breakdown.md
- requirements-analysis.md

Check the repo layout (src/bronze, src/silver, src/gold, notebooks, etc.).
The design should fit that structure and close the open items from requirements
analysis.

Cover architecture, source CSV schemas, data generation strategy, the ~700
intentional DQ issues, Bronze/Silver/Gold designs, DQ flagging and metrics,
testing strategy, dashboard mapping, folder layout, configuration, and Git
strategy.

Don't treat unspecified items as confirmed. Tag each decision:
  A = required by spec
  B = our proposed choice
  C = assumption needing confirmation

Still open from requirements analysis:
- complete source schemas
- revenue calculation and lifetime_value_actual
- customer segmentation logic
- split of ~700 problematic records
- Silver flag design
- Gold treatment of failed-quality records
- catalog/schema/table naming
- orchestration approach
- dashboard chart types

Recommend answers for each. The 700 DQ issues need a concrete, testable
distribution across customers/orders/products.

Silver: preserve bad records, make quality measurable, no silent deletes.
Gold: say whether DQ-failed records feed aggregations or not.
Segmentation: deterministic rules only — no ML.

Output the design proposal first. Don't modify project files. No PySpark. No CSVs.

End with "Design Decisions Requiring Candidate Review" — sign-off items only.
```

### What Cursor produced

Phase 4 docs were written to the three design files. Summary below.

## Files changed

| File | Action |
|---|---|
| `design-notes.md` | Created (was empty) |
| `data-model.md` | Created (was empty) |
| `data-quality-strategy.md` | Created (was empty) |

Nothing else was touched in the design-only pass.

---

## What went into each file

### `design-notes.md`

- Project purpose and links to companion docs
- **Approved design decisions** table (12 confirmed)
- **Architecture** — CSV → Bronze → Silver → Gold → dashboard; `src/` modules + thin notebooks
- **Catalog/schema** — default `medallion_eval`, configurable
- **Data generation** — base vs final counts (10,000→10,015 customers, 100,000→100,035 orders, 500 products)
- **Bronze/Silver/Gold** summaries
- **Gold formulas** — `lifetime_value_actual = total_revenue`, segmentation thresholds
- **Dashboard** — three visualizations → Gold tables and chart types
- Configuration, testing, Git approach

### `data-model.md`

- Source CSV schemas (customers, orders, products including `signup_channel`)
- Base vs final row counts
- `line_revenue = quantity * unit_price` (computed in Silver)
- Segmentation: No Purchase / Low Value / Mid Value / High Value
- Bronze metadata columns (`_ingest_batch_id`, `_source_file`, `_bronze_record_id`, etc.)
- Silver flags, `is_valid_record`, `dq_failure_reasons`
- Gold output columns
- `dq_metrics`, `dq_metrics_by_rule`
- Dashboard data mapping

### `data-quality-strategy.md`

700-issue injection plan:

| Issue code | Count |
|---|---|
| `CUST_EMAIL_MISSING` | 50 |
| `CUST_ID_DUPLICATE` | 30 (15 pairs, +15 rows) |
| `ORD_CUST_ID_MISSING` | 100 |
| `ORD_PROD_ID_MISSING` | 100 |
| `ORD_ID_DUPLICATE` | 70 (35 pairs, +35 rows) |
| `ORD_CUST_ID_INVALID` | 200 |
| `ORD_PROD_ID_INVALID` | 150 |

Also: uniqueness policy (all duplicate-key rows flagged), RI against Silver entity IDs, Gold exclusion of invalid orders/customers, pytest alignment, CSVs gitignored / manifest committed.

---

## Minor open items (didn't block Phase 5)

| Topic | Status | Notes |
|---|---|---|
| Revenue / LTV / segmentation / Gold exclusion | Resolved | In approved decisions |
| Catalog name in workspace | Low | Default `medallion_eval`; override via config |
| Zero-order products in `gold_sales_by_product` | Minor | Include with zero defaults |
| `signup_channel` allowed values | Minor | Not enumerated |
| Order date range | Minor | Generator picks fixed range, seed 42 |
| Dashboard histogram bins | Minor | Deferred to Phase 9 |
| `.gitignore` patterns | Minor | Documented; file not updated in design pass |

---

## Ready for Phase 5?

**Yes.** Ambiguities from requirements analysis are resolved in the design docs.

Next: implement `src/data_generation/`, produce base datasets, inject 700 issues, write CSVs to `data/raw/` (gitignored), commit manifest, add tests.
