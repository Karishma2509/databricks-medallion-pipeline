# Design Phase — Cursor Prompt History

## Prompt 1 — Solution Architecture and Design

### Prompt Sent to Cursor
We are now starting the Solution Design phase for the Databricks
Medallion Pipeline GenAI evaluation project.

Do NOT write implementation code yet.

First read these files:

1. cursor-workflow/project-context.md
2. cursor-workflow/spec.md
3. cursor-workflow/cursor-rules-or-instructions.md
4. cursor-workflow/task-breakdown.md
5. requirements-analysis.md

Also inspect the existing repository structure.

Your task is to propose a complete technical design for the project.

The design must cover:

1. Overall architecture
2. Source CSV datasets
3. Source schemas
4. Data-generation strategy
5. Intentional data-quality issue strategy
6. Bronze layer design
7. Silver layer design
8. Gold layer design
9. Data-quality flagging approach
10. Data-quality metrics
11. Testing strategy
12. Databricks SQL dashboard design
13. Project folder/code organization
14. Configuration approach
15. Git development strategy

IMPORTANT:

Do not treat unspecified requirements as confirmed facts.

For every important design decision, explicitly identify whether it is:

A. Required by the project specification
B. A proposed implementation decision
C. An assumption that needs confirmation

The requirements analysis identified these major ambiguities:

- complete source schemas
- revenue calculation
- lifetime_value_actual definition
- customer segmentation logic
- distribution of approximately 700 problematic records
- Silver quality flag design
- treatment of failed-quality records in Gold
- Databricks catalog/schema/table naming
- orchestration approach
- dashboard visualization choices

Provide a recommended solution for each ambiguity and explain the
reasoning.

For the approximately 700 intentional data-quality problems, propose
a concrete distribution across the three datasets and quality rules.
Make it traceable so that testing can verify that the expected problems
were detected.

For Silver, design a solution that preserves bad records and makes
their quality status measurable. Do not silently delete bad records.

For Gold, clearly define whether records with data-quality failures are
included or excluded from business aggregations and explain why.

For customer segmentation, propose a deterministic and simple rule that
can be implemented and tested. Do not introduce machine learning unless
the project requirements require it.

For revenue and lifetime value, propose clear formulas and explain
whether lifetime_value_actual should equal historical customer revenue.

For the dashboard, map each required visualization to an appropriate
Gold dataset and proposed visualization type.

For testing, define unit/integration validation for:
- missing required values
- duplicate identifiers
- invalid customer references
- invalid product references
- Gold calculations

Produce the response as a design proposal with clear sections and
tables where useful.

Do not modify project files yet.
Do not generate PySpark code yet.
Do not create CSVs yet.

At the end, provide a list titled:

"Design Decisions Requiring Candidate Review"

This list should contain only decisions that should be reviewed before
implementation begins.

### Cursor Response

Phase 4 documentation is updated. Here is the report.

## 1. Files changed

| File | Action |
|---|---|
| `design-notes.md` | Created (was empty) |
| `data-model.md` | Created (was empty) |
| `data-quality-strategy.md` | Created (was empty) |

No other files were modified.

---

## 2. What was added to each file

### `design-notes.md`

- Project purpose and links to companion docs
- **Approved design decisions** table (all 12 confirmed decisions)
- **Overall architecture** — data flow, layer responsibilities, orchestration (`src/` + thin notebooks)
- **Catalog/schema naming** — default `medallion_eval`, configurable, no Unity Catalog hard dependency
- **Data generation strategy** — base vs final row counts (10,000→10,015 customers, 100,000→100,035 orders, 500 products)
- **Bronze, Silver, Gold** design summaries aligned with approved decisions
- **Gold formulas** — revenue, AOV, `lifetime_value_actual = total_revenue`, segmentation thresholds
- **Dashboard design** — three visualizations mapped to Gold tables and chart types
- **Project organization** — folder layout
- **Configuration, testing, and Git** approach
- Cross-references to `data-model.md` and `data-quality-strategy.md`

### `data-model.md`

- **Source CSV schemas** for customers, orders, products (including `signup_channel`)
- **Base vs final row counts** with injection impact documented
- **Entity relationships** and revenue model (`line_revenue = quantity * unit_price`)
- **Customer segmentation** rules (No Purchase / Low / Mid / High)
- **Bronze tables** — business columns + ingestion metadata (`_ingest_batch_id`, `_source_file`, etc.)
- **Silver tables** — conformed columns, per-rule flags, `is_valid_record`, optional `dq_failure_reasons`
- **Gold tables** — all required output columns with definitions
- **DQ metrics tables** — `dq_metrics`, `dq_metrics_by_rule`
- **Source-to-target mapping** and dashboard data mapping

### `data-quality-strategy.md`

- **Required DQ rules** from specification
- **700-issue injection plan** with concrete distribution:

| Issue code | Count |
|---|---|
| `CUST_EMAIL_MISSING` | 50 |
| `CUST_ID_DUPLICATE` | 30 (15 pairs, +15 rows) |
| `ORD_CUST_ID_MISSING` | 100 |
| `ORD_PROD_ID_MISSING` | 100 |
| `ORD_ID_DUPLICATE` | 70 (35 pairs, +35 rows) |
| `ORD_CUST_ID_INVALID` | 200 |
| `ORD_PROD_ID_INVALID` | 150 |

- **Uniqueness policy** — all rows sharing a duplicated key flagged invalid
- **RI policy** — FK checked against corresponding Silver entity IDs
- **Silver flag definitions** — completeness, uniqueness, RI, `is_valid_record`
- **Quality metrics** — run-level and rule-level with expected counts
- **Gold exclusion policy** — invalid orders/customers excluded from aggregations
- **Testing alignment** — pytest + local Spark test cases mapped to rules
- **Git/traceability** — CSVs gitignored, manifest committed
- **Phase 5+ implementation checklist**

---

## 3. Remaining ambiguity

| Topic | Status | Notes |
|---|---|---|
| Revenue / LTV / segmentation / Gold exclusion / duplicate flagging / RI / Bronze / testing / Git | **Resolved** | Captured in approved decisions |
| Catalog name in workspace | **Low** | Default `medallion_eval`; override via config when implemented |
| Products with zero valid orders in `gold_sales_by_product` | **Minor** | Design recommends including with zero defaults; exact behavior left to implementation |
| `signup_channel` values | **Minor** | Kept as attribute; allowed values not enumerated (web, mobile, referral suggested) |
| Date range for orders | **Minor** | Not specified; generator can choose a fixed range with seed 42 |
| Dashboard bin boundaries for revenue distribution | **Minor** | Histogram on `total_revenue`; exact bins deferred to Phase 9 |
| `.gitignore` patterns | **Minor** | Policy documented; file not updated per scope constraints |

Nothing blocks Phase 5. The minor items can be decided during data generation or dashboard build.

---

## 4. Ready for Phase 5 Data Generation?

**Yes.** The design is ready for Phase 5.

Phase 4 acceptance criteria from `requirements-analysis.md` are met:

- Medallion architecture and data flow documented
- Source-to-target mappings and schemas defined for all three entities
- Data-quality strategy covers completeness, uniqueness, RI, flagging, and metrics
- Open ambiguities (revenue, LTV, segments, Gold filter, 700-issue distribution) are resolved in design docs

**Phase 5 next steps (not started):**

1. Implement data generator under `src/data_generation/`
2. Produce base datasets (10,000 / 100,000 / 500)
3. Inject 700 issues per manifest
4. Write final CSVs (10,015 / 100,035 / 500) to `data/raw/` (gitignored)
5. Commit `data/manifests/dq_injection_manifest.csv`
6. Add generation validation tests

No implementation code, configs, tests, or other files were created or modified.