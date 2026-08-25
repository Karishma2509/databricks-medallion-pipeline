# Requirements Analysis — Cursor Prompt History

## Prompt 1 — Initial Requirements Analysis

### What I asked Cursor

```
I'm starting the Databricks Medallion Architecture GenAI eval. The repo has
folder scaffolding (src/bronze, src/silver, src/gold, src/data_generation,
tests, data, notebooks) but almost no implementation yet.

I need to understand the assignment before writing code. Read:
- cursor-workflow/project-context.md
- cursor-workflow/spec.md
- cursor-workflow/cursor-rules-or-instructions.md
- cursor-workflow/task-breakdown.md

Walk the repo too. Do not write code in this step.

Put together a requirements analysis for:
1. Functional requirements
2. Data requirements
3. Bronze-layer requirements
4. Silver-layer requirements
5. Gold-layer requirements
6. Data-quality requirements
7. Dashboard requirements
8. Testing requirements
9. Documentation requirements
10. Git/version-control expectations
11. AI-assisted development expectations
12. Important assumptions or ambiguities

For each area, separate what the project docs already specify from what we
still need to decide ourselves. Don't invent requirements. Include measurable
acceptance criteria per major phase — later phases will build on those.
```

### What Cursor returned

Cursor walked the scaffold and produced the analysis below. At that point most implementation files were still empty.

---

## 1. Functional Requirements

| Requirement | Explicitly specified | Still needs a decision |
|---|---|---|
| End-to-end e-commerce sales pipeline | Yes — customers, orders, products through Medallion layers to a dashboard | How to orchestrate (notebooks vs jobs vs Python modules) |
| Medallion flow: CSV → Bronze → Silver → Gold → Databricks SQL Dashboard | Yes | Catalog/schema/table naming in Databricks |
| Incremental development | Yes — don't build everything at once | Task order within each phase |
| Data generation with intentional quality issues | Yes — ~700 problematic records for Silver to catch | Generator tech, how issues spread across check types |
| Bronze ingestion for all three datasets | Yes | One job vs separate ingestion per dataset |
| Silver validation and conformance | Yes | Single table vs valid/quarantine split |
| Gold business aggregations (3 outputs) | Yes — Sales by Product, Revenue by Customer, Customer Segmentation | Materialized tables vs views; refresh strategy |
| Databricks SQL dashboard | Yes — 3 required visualizations | Layout, chart types, filters |
| Security: no secrets in source/Git | Yes | Where to store credentials when needed |
| Scope discipline | Yes — one task at a time | How to gate each PR/commit to a single phase |

---

## 2. Data Requirements

| Requirement | Explicitly specified | Still needs a decision |
|---|---|---|
| Three CSV sources: `customers.csv`, `orders.csv`, `products.csv` | Yes | Exact file location (e.g. `data/`) |
| Scale: ~10,000 customers, ~100,000 orders, ~500 products | Yes (approximate) | Exact counts; whether "~" is good enough |
| ~700 intentionally problematic records total | Yes | Split across datasets and issue types |
| **customers.csv** fields | Partial — `customer_id`, `customer_name`, `email`, plus segmentation attributes | Full schema, types, `customer_segment` definition |
| **orders.csv** fields | Partial — `order_id`, `customer_id`, `product_id`, plus revenue measures | Revenue field names, quantity, order date, currency |
| **products.csv** fields | Partial — `product_id`, `product_name`, `category`, plus sales attributes | Price/unit fields, extra attributes |
| Delta as storage format (Bronze onward) | Yes | Partitioning, table properties, Unity Catalog vs Hive metastore |
| Traceability to source | Yes | Source file name, row number, load timestamp, batch ID, etc. |
| Gold field lists | Yes — see sections 5 and spec | Join keys, how bad Silver rows affect Gold |

---

## 3. Bronze-Layer Requirements

| Requirement | Explicitly specified | Still needs a decision |
|---|---|---|
| Read raw CSV files | Yes | Read options (header, delimiter, encoding, infer vs explicit schema) |
| Preserve source records | Yes | Keep raw string columns alongside typed columns? |
| Store as Delta | Yes | Table paths, overwrite vs append, idempotency |
| Add ingestion metadata | Yes | Which metadata columns and naming |
| Support traceability | Yes | Lineage fields, Bronze row identity |
| Don't silently clean or remove quality issues | Yes | Bronze-level DQ flags? (spec implies no cleaning) |
| Don't modify Bronze to make downstream validation pass | Yes (cursor-rules) | Validation limited to row counts/schemas per task-breakdown |

---

## 4. Silver-Layer Requirements

| Requirement | Explicitly specified | Still needs a decision |
|---|---|---|
| Validate and conform Bronze data | Yes | How far "conform" goes (cast/trim only?) |
| **Completeness** — missing required values | Yes — customer `email`; orders `customer_id`, `product_id` | Other required fields; null vs blank |
| **Uniqueness** — duplicate identifiers | Yes — `customer_id`, `order_id` | What to do with duplicates (flag all, first wins, etc.) |
| **Referential integrity** | Yes — `orders.customer_id` → customers; `orders.product_id` → products | Orphan handling in Silver vs Gold |
| Preserve bad records; don't silently delete | Yes | Flag design: booleans, reason codes, quarantine tables |
| Quality indicators and measurable metrics | Yes | Pass rate, counts by rule, where metrics live |
| Implement checks incrementally | Yes (cursor-rules) | One check per commit vs per module |
| Don't combine unrelated checks into one opaque transformation | Yes (cursor-rules) | Module boundaries |

---

## 5. Gold-Layer Requirements

### Sales by Product

| Field | Explicitly specified | Still needs a decision |
|---|---|---|
| `product_id`, `product_name`, `category` | Yes | Join path (Silver products + orders) |
| `total_orders`, `total_revenue`, `average_order_value` | Yes | Exclude failed RI orders? AOV formula |

### Revenue by Customer

| Field | Explicitly specified | Still needs a decision |
|---|---|---|
| `customer_id`, `customer_name`, `customer_segment` | Yes | Segment source field and join logic |
| `total_orders`, `total_revenue`, `average_order_value`, `lifetime_value_actual` | Yes | Is LTV the same as `total_revenue`? |

### Customer Segmentation

| Field | Explicitly specified | Still needs a decision |
|---|---|---|
| `customer_segment`, `customer_count`, `average_revenue`, `total_revenue` | Yes | Aggregation grain; customers with zero orders |

| Cross-cutting | Explicitly specified | Still needs a decision |
|---|---|---|
| Business-oriented, explainable, testable calculations | Yes (cursor-rules) | Rounding, currency precision, date filters |
| Only validated/clean data vs all data | Not specified | Filter policy for Gold inputs |

---

## 6. Data-Quality Requirements

| Requirement | Explicitly specified | Still needs a decision |
|---|---|---|
| Detect intentional issues from generated data | Yes | Test fixtures aligned to ~700 known bad records |
| Completeness failures | Yes — examples listed | Full rule catalog and severity |
| Uniqueness failures | Yes — `customer_id`, `order_id` | Composite keys not mentioned |
| Referential-integrity failures | Yes — invalid customer/product references | Internal RI on products/customers? |
| Quality metrics | Yes — "measurable" | Table, notebook output, or tests |
| Never hide DQ problems by deleting records | Yes (cursor-rules, spec) | How Gold treats flagged Silver rows |
| Document DQ strategy | Implied by cursor-rules + task-breakdown Phase 4 | `data-quality-strategy.md` content |

---

## 7. Dashboard Requirements

| Requirement | Explicitly specified | Still needs a decision |
|---|---|---|
| Platform: Databricks SQL Dashboard | Yes | Lakeview vs legacy SQL dashboard |
| **1. Top 10 Products by Revenue** | Yes | Chart type, sort order, time range |
| **2. Customer Revenue Distribution** | Yes | Bins, histogram vs percentile, outliers |
| **3. Customer Segmentation** | Yes | Chart type (bar, pie, table) |
| Data source | Implied — Gold tables | Direct SQL on Gold vs semantic layer |
| Minimum of three visualizations | Yes | Extra KPIs not required |

---

## 8. Testing Requirements

| Requirement | Explicitly specified | Still needs a decision |
|---|---|---|
| Verify intentional DQ problems are detected | Yes | pytest, notebook assertions, or Databricks jobs |
| Cover: missing values, duplicates, invalid customer/product refs | Yes | Exact expected counts for ~700 issues |
| Test source data generation | Yes (task-breakdown) | Generation validation scripts |
| Test Bronze ingestion | Yes — row counts and schemas | Tolerance for approximate scale |
| Test completeness, uniqueness, RI | Yes | Unit vs integration; local Spark vs Databricks |
| Test Gold calculations | Yes | Golden-file expected aggregates |
| Every significant transformation should have validation | Yes (cursor-rules) | Coverage threshold |
| On failure: inspect, root cause, minimal fix, re-run, document | Yes (cursor-rules) | Where debugging notes go |

---

## 9. Documentation Requirements

| Requirement | Explicitly specified | Still needs a decision |
|---|---|---|
| Document important decisions | Yes | Format and location (`design-notes.md`, etc.) |
| Record AI prompts and significant AI decisions in `ai-prompts/` | Yes | One file per phase (already scaffolded) |
| Data generation approach | Yes (task-breakdown) | Level of detail |
| Debugging decisions when relevant | Yes | `debugging-notes.md` usage |
| Update README | Yes (task-breakdown Phase 12) | README structure |
| Final artifacts: reflection, AI usage summary | Yes (task-breakdown) | Templates for `reflection.md`, `final-ai-usage-summary.md` |
| Referenced docs before implementation | Yes (cursor-rules) | When each doc gets written relative to code |

---

## 10. Git / Version-Control Expectations

| Requirement | Explicitly specified | Still needs a decision |
|---|---|---|
| Git for incremental project history | Yes | Branch strategy (main only vs feature branches) |
| Meaningful commits at project stages | Yes — setup, requirements, design, data gen, Bronze, Silver, Gold, testing, debugging, dashboard, documentation | Commit message conventions |
| Meaningful milestones; avoid noise commits | Yes (cursor-rules) | Granularity within a phase |
| Baseline commit after foundation | Yes (task-breakdown Phase 2) | Whether foundation is already done |
| Never commit secrets | Yes | `.gitignore` for local config, tokens, large data |

---

## 11. AI-Assisted Development Expectations

| Requirement | Explicitly specified | Still needs a decision |
|---|---|---|
| Cursor used across full lifecycle | Yes | Model/settings per task |
| Review and validate AI output before acceptance | Yes | Review checklist |
| Don't assume generated code is correct | Yes (cursor-rules) | Run/validate steps per change |
| Document rejected or modified AI code and why | Yes (cursor-rules) | `ai-prompts/` vs `design-notes.md` |
| Identify ambiguities before implementing | Yes (cursor-rules) | Escalation when blocked |
| Implement only requested task | Yes | Phase boundaries in prompts |
| Use PySpark / Spark SQL appropriately | Yes (cursor-rules) | Notebook vs `src/` module layout |

---

## 12. Assumptions and Open Questions

### Things we're assuming (not fully spelled out in the docs)

1. **Databricks runtime** — PySpark on Databricks is implied; local dev approach isn't defined.
2. **Revenue calculation** — Orders need a monetary measure; field name and formula (e.g. `quantity × unit_price`) aren't defined.
3. **`lifetime_value_actual`** — Probably total historical revenue per customer; not formally defined vs `total_revenue`.
4. **`customer_segment`** — Required for Gold but segmentation rules aren't in the generator requirements.
5. **Gold input filter** — Unclear if Gold uses only Silver rows passing all DQ checks or all rows with flags excluded at query time.
6. **~700 bad records** — Total across all datasets/issue types; split not specified.
7. **"Approximately" scale** — Whether exact 10k/100k/500 or variance is OK.
8. **Silver "conformance"** — Scope of cleaning (trim, cast, normalize) vs validation-only isn't detailed.
9. **Dashboard "Customer Revenue Distribution"** — Visualization type and definition of "distribution" not specified.
10. **Orchestration** — No requirement for Workflows, DLT, or CI/CD; just the end-to-end outcome.
11. **Unity Catalog** — Not mentioned; catalog/schema naming is open.
12. **Existing empty scaffold** — Folders exist; implementation hadn't started when this was written.

### Conflicts to avoid

- Bronze must not clean data; Silver must not delete bad records — cursor-rules reinforce both.
- Incremental delivery vs complete pipeline — build phase by phase, not all at once.

---

## Acceptance Criteria by Phase

Mapped to `task-breakdown.md`. Where the docs give a number we use it; otherwise these are proposals to confirm in design.

### Phase 1 — Local Setup
- Git installed and repo cloned/open in Cursor.
- `git status` runs without error.

### Phase 2 — Project Foundation
- Folder structure matches task-breakdown intent.
- `cursor-workflow/*` docs present; baseline Git commit exists.
- No secrets in tracked files.

### Phase 3 — Requirements Analysis
- This document done with explicit vs decision items separated.
- Assumptions and ambiguities listed.
- Acceptance criteria defined per phase.
- Recorded in `requirements-analysis.md` and `ai-prompts/01-requirements-analysis.md`.

### Phase 4 — Solution Design
- Architecture diagram and data flow documented.
- Source-to-target mappings and schemas for all three entities.
- DQ strategy covers completeness, uniqueness, RI, flagging, and metrics.
- Open ambiguities (revenue, LTV, segments, Gold filter) resolved in design.

### Phase 5 — Data Generation
- `customers.csv` ≈ 10,000 rows; `orders.csv` ≈ 100,000; `products.csv` ≈ 500.
- Exactly **700** (or documented total) intentional DQ issues injectable and traceable.
- Generation approach documented.
- Validation script confirms counts and presence of each issue type.

### Phase 6 — Bronze
- Three Delta tables created from CSVs.
- Row counts match source CSVs (no dropped rows).
- Ingestion metadata columns populated on every row.
- Schemas documented and validated by tests.
- No DQ cleaning applied in Bronze.

### Phase 7 — Silver
- Completeness flags detect missing `email`, `customer_id`, `product_id` as specified.
- Uniqueness flags detect duplicate `customer_id` and `order_id`.
- RI flags detect orphan `orders.customer_id` and `orders.product_id`.
- 100% of Bronze rows retained in Silver (or equivalent auditable preservation).
- Quality metrics report counts matching known ~700 issues (± agreed tolerance).
- Checks implemented incrementally with test coverage per check.

### Phase 8 — Gold
- Three Gold outputs exist with all required columns per spec.
- `average_order_value` = `total_revenue / total_orders` where orders > 0 (per design).
- Business logic documented and covered by tests with known expected aggregates on sample/fixture data.

### Phase 9 — Dashboard
- One Databricks SQL dashboard published with all three required visualizations.
- Top 10 Products shows ≤10 products ranked by revenue.
- Customer Revenue Distribution renders from Gold customer revenue data.
- Customer Segmentation visualization uses Gold segmentation output.

### Phase 10 — Testing
- Automated tests pass for: data generation, Bronze ingest, each Silver DQ rule, Gold calculations.
- Tests assert detection of missing values, duplicates, and invalid FK references.
- Quality metric calculations verified against expected counts.

### Phase 11 — Debugging
- Any test failures logged in `debugging-notes.md` with root cause and fix.
- Full test suite passes after fixes.
- Fixes are minimal and scoped to failing behavior.

### Phase 12 — Finalization
- Git history shows meaningful stage commits (requirements → design → data → Bronze → Silver → Gold → dashboard → tests → docs).
- `README.md` describes setup, run order, and validation steps.
- `ai-prompts/` complete; `reflection.md` and `final-ai-usage-summary.md` filled in.
- Submission artifacts ready; no credentials in repository.

---

## Summary

Medallion e-commerce pipeline: three CSV sources, Delta layers, Silver DQ with bad data preserved, three Gold aggregates, three-widget Databricks SQL dashboard — built incrementally with Git, tests, and documented AI workflow.

Biggest gaps to resolve in **Phase 4 (Design)** before coding: full schemas, revenue/LTV definitions, customer segmentation rules, distribution of the ~700 DQ issues, Silver flag/metric design, Gold inclusion rules for failed DQ rows, and Databricks workspace/naming conventions.

---

## Candidate Review Notes

### Accepted

- Separation between explicit requirements and implementation decisions.
- Calling out unresolved items: revenue calculation, customer segmentation, LTV, Gold inclusion rules.
- Testing and Git requirements identified.
- Phased acceptance criteria structure.

### To confirm in design (not locked yet)

- Exact number of intentional data-quality issues.
- Exact source schemas.
- Revenue calculation.
- Lifetime value definition.
- Customer segmentation logic.
- Treatment of Silver quality failures in Gold.
- Dashboard visualization choices.
- Databricks table/catalog naming.
- Orchestration approach.

These weren't fully specified in the project context — resolve in design, don't treat as confirmed requirements.

### Rejected

None at this stage.

### Key decision

Don't start implementation until the major design ambiguities are resolved.
