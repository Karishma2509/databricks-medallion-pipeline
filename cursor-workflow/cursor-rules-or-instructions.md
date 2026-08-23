# Cursor Rules and Instructions

## 1. Project Context

Before implementing a task, consider:

- cursor-workflow/project-context.md
- cursor-workflow/spec.md
- requirements-analysis.md
- design-notes.md
- data-model.md
- data-quality-strategy.md

Do not make assumptions that conflict with these documents.

## 2. Scope

Implement only the requested task.

Do not generate the entire project unless explicitly requested.

Do not silently introduce additional requirements.

If a requirement is ambiguous, identify the ambiguity before
implementing it.

## 3. Code Quality

Prefer:

- readable code
- modular functions
- meaningful variable names
- reusable transformations
- appropriate error handling
- explicit schemas where appropriate
- testable logic

Use PySpark and Spark SQL appropriately for Databricks.

## 4. Data Quality

Never hide data-quality problems by deleting bad records.

Quality issues should be:

- identified
- flagged
- measurable
- documented

## 5. Bronze

Bronze should preserve source information.

Do not modify Bronze merely to make downstream validation pass.

## 6. Silver

Silver is responsible for validation and conformance.

Implement quality checks incrementally.

Do not combine unrelated quality checks into one opaque transformation.

## 7. Gold

Gold should contain business-oriented analytical outputs.

Business calculations must be explainable and testable.

## 8. Testing

Every significant transformation should have validation.

When a test fails:

1. inspect the error
2. identify the root cause
3. make the smallest appropriate change
4. re-run the test
5. document the result when relevant

## 9. AI-Generated Code

Do not assume generated code is correct.

Before accepting AI-generated code:

- review it
- understand it
- run it
- validate the result

If generated code is rejected or modified, document why.

## 10. Security

Never generate or hard-code:

- passwords
- API keys
- access tokens
- secrets
- credentials

## 11. Documentation

Important decisions should be documented.

AI prompts and significant AI-assisted decisions should be recorded
in the ai-prompts directory.

## 12. Git

Make meaningful commits after stable project milestones.

Do not create meaningless commits for every small keystroke.