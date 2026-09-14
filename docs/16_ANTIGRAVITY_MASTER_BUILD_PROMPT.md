# Anti-Gravity Master Build Prompt

You are building a production-quality local Streamlit application named **Performance Insight Explorer**.

Before writing code, read every file in this repository's `docs/` folder.

Treat these files as the controlling specification.

## Core requirement

The future assessment dataset is unknown.

Therefore:

**DO NOT HARD-CODE COLUMN NAMES OR A FIXED DATASET SCHEMA.**

Build the application around conceptual analytical roles and user-confirmed mapping.

## Required behaviour

1. Accept CSV, XLS and XLSX.
2. Preserve the raw uploaded data unchanged.
3. Profile the dataset.
4. Run transparent data-quality checks.
5. Suggest possible field mappings.
6. Require the user to confirm mappings.
7. Activate only calculations supported by mapped fields.
8. Prevent division by zero.
9. Never automatically delete outliers.
10. Never fabricate missing values.
11. Never claim causation from correlation.
12. Clearly label estimated metrics.
13. Record assumptions, limitations, filters and mappings.
14. Produce Analyst, Manager and Interview views.
15. Generate a six-slide PowerPoint.
16. Export charts, tables and an audit trail.
17. Run locally without external APIs.

## Architecture

Follow `docs/06_TECHNICAL_ARCHITECTURE.md`.

Keep analytical logic out of the Streamlit UI where practical.

Use modular functions and automated tests.

## Build order

Phase 1:
- repository structure
- ingestion
- profiling
- mapping
- QA
- tests

Phase 2:
- KPI engine
- trends
- comparisons
- visualisations
- tests

Phase 3:
- root-cause workspace
- insight cards
- assumptions
- limitations
- recommendations

Phase 4:
- Interview View
- PowerPoint export
- audit export
- final regression testing

## Quality gate

Do not mark the build complete until:

- all tests pass
- source data remains unmodified
- unsupported metrics are disabled
- zero denominators are safe
- every generated insight can be traced to data
- exports open successfully

After implementation provide:

1. file tree
2. test results
3. implemented features
4. known limitations
5. exact Windows commands to set up and run the application


