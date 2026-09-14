

---

# FILE: README.md

# Performance Insight Explorer

A reusable, schema-flexible operational performance analytics application.

## Purpose

Performance Insight Explorer is designed to help an analyst receive an unfamiliar CSV or Excel dataset, understand its structure, assess data quality, map unknown columns to analytical roles, calculate transparent performance measures, identify trends and exceptions, communicate insight, and export presentation-ready outputs.

The first intended use case is a timed Performance Analyst assessment, but the application must remain generic and reusable.

## Key design rule

**Do not hard-code the incoming dataset schema.**

The system must use:

1. automatic profiling
2. suggested column-role mapping
3. user-confirmed mapping
4. conditional analytical modules

## Read these files first

1. `docs/01_PRODUCT_BLUEPRINT.md`
2. `docs/02_FUNCTIONAL_REQUIREMENTS.md`
3. `docs/05_DATA_MAPPING_AND_SCHEMA_STRATEGY.md`
4. `docs/06_TECHNICAL_ARCHITECTURE.md`
5. `docs/09_TEST_PLAN_AND_ACCEPTANCE_CRITERIA.md`
6. `docs/16_ANTIGRAVITY_MASTER_BUILD_PROMPT.md`

## Tomorrow's workflow

When a new dataset arrives:

**Upload → Profile → QA → Map → Analyse → Interpret → Recommend → Export**

The application must preserve the original source data and must never silently alter, delete, impute or reinterpret observations.

## Product owner

Daramola Omoyele


---

# FILE: docs/00_READ_ME_FIRST.md

# Read Me First

This documentation pack is the controlling specification for the Performance Insight Explorer.

The application is intentionally designed before the first live dataset is known. The architecture therefore assumes that future datasets may differ in:

- column names
- row granularity
- date format
- reporting period
- KPI definitions
- available denominators
- team or category structure
- target structure
- missingness
- operational context

## Build principle

The application must not be built around one dataset.

Instead, it must:

1. inspect the uploaded file
2. infer possible field roles
3. ask the analyst to confirm mappings
4. activate only supported calculations
5. expose formulas and assumptions
6. preserve analyst judgement

## Document hierarchy

If two documents appear to conflict, use this order:

1. Product Blueprint
2. Functional Requirements
3. Data Mapping and Schema Strategy
4. Analytics Specification
5. Data Quality Framework
6. Technical Architecture
7. Test Plan
8. UI/UX Specification
9. Export Specification
10. User Guide

## Non-negotiable rules

- Never overwrite source data.
- Never fabricate missing values.
- Never delete outliers automatically.
- Never claim causation from correlation.
- Never calculate a metric without the required denominator.
- Never hide limitations.
- Never present estimated values as observed values.
- Never hard-code BSR-specific field names into the core analytical engine.

The first use case may be BSR, but BSR must be treated as a configuration, not as the product architecture.


---

# FILE: docs/01_PRODUCT_BLUEPRINT.md

# Product Blueprint

## 1. Product name

**Performance Insight Explorer**

Subtitle:

**Operational Performance • Data Quality • Analysis • Insight**

## 2. Product vision

Create a reusable analytical decision-support application that can accept unfamiliar operational datasets and guide an analyst from raw data to transparent, defensible insight.

## 3. Problem

Performance analysts often receive data with little preparation time and inconsistent structures.

The analyst must rapidly answer:

- What data have I received?
- Can I trust it?
- What is happening?
- Where is performance changing?
- Which groups are different?
- What may explain the differences?
- What should happen next?
- What cannot yet be concluded?

## 4. Product objectives

The application should enable the user to:

- upload CSV, XLS or XLSX
- select a worksheet
- profile the dataset
- identify quality issues
- map unknown columns to analytical roles
- calculate supported KPIs
- analyse trends and comparisons
- inspect potential drivers
- record assumptions and limitations
- generate key findings
- generate evidence-linked recommendations
- create interview and management views
- export PowerPoint, charts, tables and audit records

## 5. Product principles

### 5.1 Reliability over complexity
The application should prefer a smaller number of correct, transparent calculations over many opaque features.

### 5.2 Transparency over automation
Every calculation should be explainable.

### 5.3 Analyst in control
The system may suggest, but the user confirms.

### 5.4 Conditional analysis
Only run a metric when its required fields are mapped and valid.

### 5.5 Preserve evidence
The raw uploaded dataset remains unchanged.

### 5.6 No false certainty
The system should use wording such as:

- may indicate
- is associated with
- appears consistent with
- requires further investigation

when the evidence does not support causation.

## 6. Primary users

- Performance Analysts
- Data Analysts
- Business Analysts
- Operational Managers
- Research Analysts

## 7. Initial use case

A timed Performance Analyst assessment where the file structure is unknown before receipt.

## 8. Core workflow

**Purpose → Upload → Profile → QA → Map → Analyse → Interpret → Recommend → Review → Export**

## 9. In scope

- local file upload
- profiling
- quality assessment
- flexible mapping
- KPI calculations
- trend analysis
- segment comparison
- backlog analysis
- productivity
- utilisation
- target performance
- processing time analysis
- outlier flagging
- root-cause exploration
- communication views
- audit trail
- PowerPoint export

## 10. Out of scope for Version 1

- automated causal inference
- machine-learning forecasting
- automatic data correction
- direct cloud publishing
- live databases
- external AI APIs
- automated decisions
- direct Power BI integration

## 11. Success definition

The product succeeds when an analyst can receive an unfamiliar operational dataset and reach a defensible, presentation-ready analysis without rewriting the application for the dataset.


---

# FILE: docs/02_FUNCTIONAL_REQUIREMENTS.md

# Functional Requirements

## FR-001 File upload

The system shall accept:

- CSV
- XLS
- XLSX

The system shall preserve the original file contents.

## FR-002 Excel worksheet selection

Where an Excel file contains multiple sheets, the user shall select the sheet to analyse.

## FR-003 Dataset profile

The application shall display:

- filename
- sheet
- row count
- column count
- data types
- unique counts
- candidate date fields
- candidate numeric fields
- candidate categorical fields
- earliest and latest date where available

## FR-004 Data quality scan

The system shall scan for:

- missing values
- duplicate rows
- duplicate IDs where mapped
- invalid dates
- numeric parsing problems
- negative values
- unexpected zeros
- constant columns
- high-cardinality categorical columns
- category spelling/case inconsistencies
- potential outliers

## FR-005 Quality issue severity

Each quality issue shall be classified as:

- Critical
- Warning
- Information

The reason shall be visible.

## FR-006 Flexible column mapping

The application shall support optional role mapping for:

- Record ID
- Date
- Reporting Period
- Team
- Department
- Branch
- Location
- Category
- Case Type
- Status
- Actual
- Target
- Cases Received
- Cases Completed
- Opening Backlog
- Closing Backlog
- Available Staff
- Available FTE
- Hours Available
- Hours Used
- Processing Time
- Cost
- Quality Measure
- Customer Measure

## FR-007 Mapping suggestions

The system may suggest likely mappings based on column names and data types.

The user must confirm each mapping.

## FR-008 Data preview

The user shall be able to inspect the first and last rows and sampled records.

## FR-009 KPI engine

The system shall calculate only metrics supported by mapped fields.

## FR-010 Target achievement

If Actual and Target are available:

Target Achievement % = Actual / Target × 100

Zero denominators must return a warning, not infinity.

## FR-011 Variance

Target Variance = Actual - Target

The UI shall not assume that positive variance is always favourable.

## FR-012 Productivity

If Completed and FTE are available:

Productivity = Completed / Available FTE

The selected denominator must be displayed.

## FR-013 Utilisation

If Hours Used and Hours Available exist:

Utilisation % = Hours Used / Hours Available × 100

## FR-014 Backlog movement

If opening and closing backlog exist:

Backlog Change = Closing Backlog - Opening Backlog

If opening backlog, received and closed exist:

Expected Closing Backlog = Opening Backlog + Received - Closed

## FR-015 Estimated flow pressure

If Received and Completed exist but actual backlog is unavailable:

Estimated Net Flow = Received - Completed

This must be labelled as an estimate.

## FR-016 Trend analysis

Where a valid time field exists, the system shall support:

- period totals
- period averages
- percentage change
- rolling trend where appropriate
- peaks
- troughs
- sustained improvement
- sustained deterioration

## FR-017 Comparison analysis

The system shall allow comparison by mapped dimensions such as:

- team
- location
- category
- case type
- status

## FR-018 Distribution analysis

The system shall support:

- histogram
- box plot
- mean
- median
- quartiles
- standard deviation

## FR-019 Relationship analysis

The system may provide:

- scatter plots
- correlation coefficients
- grouped relationships

The application shall display a warning that correlation does not establish causation.

## FR-020 Exception analysis

The system shall identify:

- top values
- bottom values
- largest changes
- largest target variances
- possible outliers
- groups far from the overall average

## FR-021 Root-cause workspace

The application shall organise possible drivers under:

- Demand
- Capacity
- Process
- Complexity
- Data Quality

## FR-022 Insight cards

Each insight card shall contain:

- Finding
- Evidence
- Interpretation
- Business implication
- Recommendation
- Limitation

## FR-023 Assumptions register

The user shall be able to record and edit assumptions.

## FR-024 Limitations register

The application shall suggest limitations and allow manual additions.

## FR-025 Communication views

The application shall provide:

- Analyst View
- Manager View
- Interview View

## FR-026 Interview View

Interview View shall provide a concise structure:

- objective
- approach
- data quality
- method
- 3–5 findings
- implications
- recommendations
- limitations
- next analysis

## FR-027 Visualisation selection

The application shall recommend:

- line chart for time trends
- bar chart for comparison
- histogram or box plot for distributions
- scatter plot for relationships

## FR-028 Filtering

Where available, filters shall include:

- date range
- team
- location
- category
- case type
- status

Active filters must remain visible.

## FR-029 Audit trail

The application shall log:

- filename
- worksheet
- load time
- mappings
- filters
- quality issues
- metrics generated
- exports

## FR-030 Export

The system shall support:

- PowerPoint
- PNG charts
- CSV analytical tables
- CSV audit trail
- Excel summary

## FR-031 PowerPoint

Default deck:

1. Objective and approach
2. Data quality and methodology
3. Performance overview
4. Trends and comparisons
5. Key insights and possible drivers
6. Recommendations, limitations and next steps

## FR-032 Offline-first operation

Version 1 shall not require external internet services or APIs.

## FR-033 Error handling

User-facing errors shall be understandable and actionable.

The application must fail safely rather than silently producing misleading output.


---

# FILE: docs/03_ANALYTICS_SPECIFICATION.md

# Analytics Specification

## 1. General rule

Every metric must document:

- definition
- formula
- required fields
- denominator
- interpretation
- limitations

## 2. Descriptive statistics

For numeric variables support:

- count
- non-missing count
- sum
- mean
- median
- standard deviation
- minimum
- maximum
- quartiles

For categorical variables support:

- count
- unique count
- frequency
- percentage distribution

## 3. Target achievement

Required:
- Actual
- Target

Formula:

`Target Achievement % = Actual / Target * 100`

Rules:

- If target = 0, do not calculate.
- If target is missing, mark metric unavailable.
- Never automatically interpret >100% as positive because some targets represent maximum thresholds.

## 4. Target variance

`Variance = Actual - Target`

`Variance % = (Actual - Target) / Target * 100`

Apply the same zero-denominator protection.

## 5. Productivity

Preferred formula:

`Productivity = Cases Completed / Available FTE`

Alternative denominators may be:

- headcount
- staff hours
- productive hours

The denominator label must be visible.

Limitation:
Productivity may be affected by case complexity, experience, process design and data completeness.

## 6. Utilisation

`Utilisation % = Hours Used / Hours Available * 100`

High utilisation must not automatically be described as good performance.

## 7. Backlog

Observed change:

`Closing Backlog - Opening Backlog`

Expected close:

`Opening Backlog + Received - Closed`

Reconciliation difference:

`Reported Closing Backlog - Expected Closing Backlog`

A non-zero difference should trigger review.

## 8. Net flow

Where backlog fields are absent:

`Net Flow = Received - Completed`

Label:
**Estimated pressure on workload / flow balance**

Do not label as actual backlog change.

## 9. Completion rate

Where received and completed are measured on a compatible cohort or period:

`Completion Rate = Completed / Received * 100`

The system must warn where period flows do not represent the same cohort.

## 10. Processing time

Show:

- mean
- median
- 25th percentile
- 75th percentile
- 90th percentile where sample size permits
- distribution
- trend
- group comparison

Prefer median when strongly skewed.

## 11. Trend analysis

Where date is available:

- aggregate to appropriate period
- sort chronologically
- calculate absolute and percentage period change
- identify largest increase/decrease
- distinguish single-period movement from repeated direction

## 12. Comparison

For group comparison:

- show raw values
- show rate/normalised value where a valid denominator exists
- show sample size

Avoid ranking tiny groups without warning.

## 13. Outliers

Default approach may include IQR or robust z-score.

Outlier status means:
**review required**

It does not mean:
**delete**

## 14. Correlation

Use Pearson only where approximately linear and numeric conditions are reasonable.

Provide Spearman as an alternative for monotonic/non-normal relationships.

Display:

`Association does not demonstrate causation.`

## 15. Statistical testing

Version 1 may optionally support:

- t-test
- Mann–Whitney
- chi-square
- ANOVA

Only expose tests where assumptions and the business question justify them.

Do not run tests merely because numeric fields exist.

## 16. Root-cause exploration

Root-cause categories:

### Demand
- incoming volume
- case mix
- seasonality
- growth rate

### Capacity
- FTE
- staff hours
- utilisation
- absences if available

### Process
- processing time
- stages
- rework
- queue accumulation

### Complexity
- case type
- risk category
- complexity indicator

### Data quality
- missingness
- inconsistent definitions
- reporting changes
- duplicates

## 17. Insight rule

An insight must be supported by a reproducible calculation or clearly labelled qualitative interpretation.

Structure:

**Finding → Evidence → Interpretation → Implication → Recommendation → Limitation**

## 18. Recommendation rule

Recommendations should be one of:

- Act
- Investigate
- Monitor
- Improve reporting

The application must not invent interventions unsupported by evidence.


---

# FILE: docs/04_DATA_QUALITY_FRAMEWORK.md

# Data Quality Framework

## Purpose

Determine whether the uploaded data is sufficiently reliable for the intended analysis.

## Dimensions

### Completeness
Check:
- missing cells
- missing key fields
- missing periods
- empty columns

### Uniqueness
Check:
- duplicate rows
- duplicate record IDs
- repeated business keys

### Validity
Check:
- date parse failures
- numeric parse failures
- impossible percentages
- negative values where unexpected
- zero denominators

### Consistency
Check:
- inconsistent labels
- case differences
- whitespace
- unit differences
- date-format inconsistencies

### Timeliness
Check:
- latest date
- reporting gaps
- stale periods

### Integrity
Check:
- reconciliation relationships
- totals versus components
- opening/closing balances where possible

### Plausibility
Check:
- extreme values
- sudden discontinuities
- impossible relationships

## Severity model

### Critical
Likely to invalidate a major part of the analysis.

Examples:
- key metric mostly missing
- date field unusable
- denominator invalid
- probable duplicate counting

### Warning
May influence interpretation.

Examples:
- moderate missingness
- potential outliers
- category inconsistencies

### Information
Should be documented but is not necessarily harmful.

Examples:
- unused constant field
- small amount of missing optional metadata

## Handling policy

The application may:
- flag
- describe
- filter temporarily for analysis
- allow user-approved cleaning views

The application must not:
- overwrite
- silently impute
- silently remove
- silently merge categories

## QA output

For each issue report:

- issue type
- field
- count
- percentage
- severity
- sample records
- suggested analyst action
- status: unresolved / reviewed / accepted


---

# FILE: docs/05_DATA_MAPPING_AND_SCHEMA_STRATEGY.md

# Data Mapping and Schema Strategy

## Objective

Allow the application to work with datasets whose columns are unknown before upload.

## Core rule

The analytical engine must operate on **roles**, not physical column names.

Example:

A future dataset may contain:

- `Team Name`
- `Operational Unit`
- `Branch`
- `Service Area`

Any of these may be mapped to the role `Group`.

## Supported roles

### Identity
- Record ID

### Time
- Date
- Reporting Period

### Dimensions
- Team
- Department
- Branch
- Location
- Category
- Case Type
- Status

### Performance
- Actual
- Target
- Cases Received
- Cases Completed
- Opening Backlog
- Closing Backlog
- Processing Time

### Capacity
- Staff
- FTE
- Hours Available
- Hours Used

### Other
- Cost
- Quality Measure
- Customer Measure

## Mapping process

1. Profile columns.
2. Infer data type.
3. Apply name-pattern suggestions.
4. Display suggestions with confidence.
5. User confirms or rejects.
6. Store mapping in session state.
7. Activate supported metrics.

## Suggestion patterns

Examples:

### Date role
Keywords:
- date
- month
- week
- year
- period
- quarter

### Team/group role
Keywords:
- team
- branch
- unit
- region
- area
- location

### Target role
Keywords:
- target
- expected
- goal
- benchmark

### Received role
Keywords:
- received
- incoming
- demand
- applications
- new cases

### Completed role
Keywords:
- completed
- closed
- decisions
- processed
- resolved

### Backlog role
Keywords:
- backlog
- open
- outstanding
- pending

### FTE role
Keywords:
- fte
- staff
- resource
- capacity

### Processing time role
Keywords:
- processing time
- duration
- days
- turnaround
- elapsed

## Mapping constraints

- One physical field may map to multiple conceptual roles only with explicit user approval.
- A required metric shall remain disabled until its inputs are valid.
- Suggested mapping must never be treated as confirmed mapping.
- Mapping must be exportable in the audit trail.

## Unknown columns

Unmapped fields remain available for:
- filtering
- exploration
- later mapping

Never discard them.

## Saved profiles

Future versions may allow reusable mapping profiles, for example:

- BSR assessment
- Customer service operations
- Finance operations

Profiles must remain configuration files, not hard-coded application logic.


---

# FILE: docs/06_TECHNICAL_ARCHITECTURE.md

# Technical Architecture

## Technology

- Python 3.11+
- Streamlit
- pandas
- numpy
- plotly
- openpyxl
- python-pptx
- scipy
- pyyaml
- pytest

## Architecture

UI Layer
↓
Session State / Controller
↓
Ingestion Layer
↓
Profiling Layer
↓
Quality Engine
↓
Mapping Engine
↓
Analytics Engine
↓
Insight Engine
↓
Visualisation Layer
↓
Reporting / Export
↓
Audit Layer

## Recommended structure

```text
performance_insight_explorer/
├── app.py
├── requirements.txt
├── README.md
├── pages/
├── src/
├── config/
├── tests/
├── docs/
├── sample_data/
└── outputs/
```

## Modules

### `src/ingestion.py`
Responsibilities:
- file validation
- CSV parsing
- Excel parsing
- worksheet list
- safe data loading

### `src/profiling.py`
Responsibilities:
- types
- dimensions
- unique counts
- date range
- numeric/categorical detection

### `src/quality.py`
Responsibilities:
- missingness
- duplicates
- validity
- category consistency
- outliers
- integrity checks

### `src/mapping.py`
Responsibilities:
- role catalogue
- suggestions
- confidence score
- user-confirmed mapping

### `src/metrics.py`
Responsibilities:
- safe division
- KPI formulas
- metadata
- calculation trace

### `src/trends.py`
Responsibilities:
- time aggregation
- period change
- trend summary

### `src/comparisons.py`
Responsibilities:
- group comparisons
- normalisation
- sample-size warnings

### `src/root_cause.py`
Responsibilities:
- evidence-linked driver exploration

### `src/insights.py`
Responsibilities:
- convert calculated evidence into structured insight cards

### `src/visualisations.py`
Responsibilities:
- chart selection
- labels
- chart objects

### `src/powerpoint.py`
Responsibilities:
- six-slide export
- chart placement
- metadata

### `src/audit.py`
Responsibilities:
- audit events
- mapping record
- filter record
- export log

## State

Maintain:

- raw_df
- working_df
- active_sheet
- mappings
- filters
- qa_results
- assumptions
- limitations
- metrics
- insights
- recommendations
- export_settings

`raw_df` must never be modified.

## Error handling

Use:
- explicit validation
- user-readable errors
- safe defaults
- exception logging

Never continue with a failed key calculation.

## Performance

Version 1 should work comfortably for ordinary assessment-sized datasets.

For larger datasets:
- cache loading
- cache profiling
- avoid repeated full scans
- aggregate before plotting

## Offline requirement

No external API calls are required for the core application.


---

# FILE: docs/07_UI_UX_SPECIFICATION.md

# UI and UX Specification

## Design goal

Professional, calm, analytical, fast to use under time pressure.

## Branding

Title:
**Performance Insight Explorer**

Subtitle:
**Operational Performance • Data Quality • Analysis • Insight**

Author:
**DARAMOLA OMOYELE**

Do not use official BSR, HSE, ONS or government logos.

## Navigation

1. Home
2. Upload & Profile
3. Data Quality
4. Column Mapping
5. Performance Overview
6. Trends
7. Comparisons
8. Root Cause
9. Insights
10. Recommendations
11. Interview View
12. Export
13. Audit Trail

## Home

Show:
- purpose
- simple workflow
- disclaimer
- start button

## Upload & Profile

Show:
- uploader
- sheet selector
- profile cards
- data preview

## Data Quality

Show:
- critical count
- warning count
- information count
- issue table
- sample affected rows

## Mapping

Use:
- dropdowns
- confidence suggestions
- explanation of each role
- mapping status

## Performance Overview

Show only supported KPIs.

Never show blank KPI cards.

## Trends

Allow:
- metric selection
- time aggregation
- grouping
- line chart
- data table

## Comparisons

Allow:
- group field
- metric
- rate/normalised option
- sample-size display

## Root Cause

Use five panels:
- Demand
- Capacity
- Process
- Complexity
- Data Quality

## Interview View

Minimal, presentation-focused layout.

Show:
- objective
- approach
- data quality
- 3–5 insights
- recommendations
- limitations

Avoid dense controls.

## Export

Allow:
- PowerPoint
- PNG
- CSV
- XLSX
- audit trail

## UX rules

- Never hide active filters.
- Never silently clean data.
- Always label estimated metrics.
- Provide plain-English metric explanations.
- Prefer one clear chart over many decorative charts.


---

# FILE: docs/08_EXPORT_AND_REPORTING_SPEC.md

# Export and Reporting Specification

## PowerPoint

Default six-slide structure:

### Slide 1 — Objective and Approach
- question
- audience
- dataset
- method

### Slide 2 — Data Quality and Methodology
- key QA checks
- important issues
- assumptions
- analytical method

### Slide 3 — Performance Overview
- headline KPIs
- target performance
- high-level status

### Slide 4 — Trends and Comparisons
- strongest trend chart
- strongest comparison chart
- concise interpretation

### Slide 5 — Key Insights and Possible Drivers
- 3–5 findings
- supporting evidence
- potential drivers
- caution where causal evidence is absent

### Slide 6 — Recommendations and Next Steps
- immediate actions
- investigation
- monitoring
- limitations

## File naming

Use:

`performance_insight_YYYYMMDD_HHMM.pptx`

## Chart export

PNG with:
- title
- labels
- readable dimensions
- date generated where appropriate

## Table export

CSV or XLSX.

Include:
- filters
- metric definition
- generation date

## Audit export

CSV fields:

- timestamp
- event
- file
- sheet
- mapping
- filter
- metric
- note

## Export QA

Before export check:

- unsupported metrics absent
- zero-denominator issues resolved
- charts match calculations
- active filters documented
- estimates labelled
- assumptions present
- limitations present


---

# FILE: docs/09_TEST_PLAN_AND_ACCEPTANCE_CRITERIA.md

# Test Plan and Acceptance Criteria

## Test philosophy

The application must be trusted because calculations are testable and reproducible.

## Unit tests

### Ingestion
- CSV loads
- XLSX loads
- invalid file handled
- empty file handled

### Mapping
- suggestion patterns work
- manual mapping overrides suggestion
- unmapped fields remain available

### Quality
- missing values counted
- duplicates detected
- invalid dates identified
- inconsistent categories flagged
- outliers flagged but not removed

### Metrics
- target achievement correct
- variance correct
- productivity correct
- utilisation correct
- backlog movement correct
- zero denominator safe

### Trend
- chronological sort correct
- percentage change correct
- missing periods handled

### Export
- PowerPoint opens
- expected slide count
- CSV audit exports
- chart PNG generated

## Integration tests

### Workflow 1
CSV → Profile → Map → KPI → Chart → Export

### Workflow 2
Excel → Sheet selection → QA → Map → Trend → PowerPoint

### Workflow 3
Dataset missing key fields → unsupported metrics disabled cleanly

## Edge cases

Test:

- one-row dataset
- one-column dataset
- no numeric fields
- no dates
- all missing field
- all zero denominator
- duplicate headers
- mixed types
- large category count
- strange Excel sheet names
- non-chronological dates
- negative values
- extreme outliers

## Acceptance criteria

Release Version 1 only when:

- file upload works
- source data is preserved
- mapping is user-controlled
- data quality issues are visible
- unsupported calculations do not run
- division by zero is safe
- KPI formulas pass tests
- active filters are visible
- insight cards cite calculated evidence
- limitations can be recorded
- PowerPoint export works
- audit trail works
- all automated tests pass

## Regression rule

Every bug fixed must receive a regression test where practical.


---

# FILE: docs/10_SECURITY_PRIVACY_GOVERNANCE.md

# Security, Privacy and Governance

## Version 1 deployment model

Local-first.

## Rules

- Do not upload source data to external services.
- Do not make external API calls for analysis.
- Do not store credentials.
- Do not persist source files unless the user explicitly exports or saves them.
- Do not unnecessarily display personal identifiers.
- Do not include source records in presentation exports unless required.
- Keep raw data separate from working analysis.

## Sensitive data

If the dataset contains names, emails, IDs or other personal data:

- minimise display
- avoid including identifiers in charts
- avoid exporting row-level personal data unless necessary
- document handling decisions

## Governance

Maintain:

- assumptions register
- limitations register
- audit trail
- metric definitions
- mapping record
- export record

## Decision-support disclaimer

The application supports analytical judgement.

It does not make operational decisions automatically.


---

# FILE: docs/11_USER_GUIDE.md

# User Guide

## 1. Start the application

Run:

`streamlit run app.py`

## 2. Upload a file

Choose CSV, XLS or XLSX.

For Excel select the relevant worksheet.

## 3. Review profile

Confirm:

- expected row count
- expected columns
- plausible date range
- sensible data types

## 4. Review quality

Investigate:

- critical issues first
- duplicates
- missing key fields
- invalid values
- outliers
- category inconsistencies

Do not remove anything automatically.

## 5. Map columns

Map only fields you understand.

If uncertain:
- inspect values
- check assessment instructions
- leave unmapped until clear

## 6. Select analysis

Run only relevant modules.

Examples:
- trend
- target performance
- productivity
- utilisation
- backlog
- comparison

## 7. Review insights

For each finding ask:

- Is it supported?
- Is the denominator correct?
- Could another explanation exist?
- Is this correlation or causation?
- Does it matter operationally?

## 8. Record assumptions

Write down anything you had to assume.

## 9. Record limitations

Document missing information and analytical constraints.

## 10. Prepare Interview View

Select only the strongest 3–5 insights.

## 11. Export

Export only after final QA.


---

# FILE: docs/12_INTERVIEW_QUICK_GUIDE.md

# Interview Quick Guide

## 60-minute assessment workflow

### 0–5 minutes — Understand
Write down:
- question
- audience
- decision required
- deliverable

### 5–10 minutes — Upload and profile
Check:
- shape
- dates
- variables
- likely identifiers

### 10–15 minutes — QA
Check:
- missing
- duplicates
- invalid values
- outliers
- reconciliation

### 15–20 minutes — Map
Confirm:
- time
- group
- actual
- target
- demand
- completion
- backlog
- capacity

### 20–35 minutes — Analyse
Focus on:
- baseline
- trends
- comparisons
- exceptions
- rates not just counts

### 35–45 minutes — Investigate
Ask:
- demand?
- capacity?
- process?
- complexity?
- data quality?

### 45–50 minutes — Recommend
Use:
- finding
- evidence
- implication
- recommendation
- limitation

### 50–55 minutes — Interview View
Prepare:
- objective
- approach
- QA
- 3–5 insights
- recommendations

### 55–60 minutes — Final QA
Confirm:
- formulas
- denominators
- chart labels
- assumptions
- limitations

## Verbal answer structure

**Purpose → Quality → Method → Finding → Why it matters → Limitation → Recommendation**

## If challenged

Say:

"The available evidence supports this as an indication, but I would not treat it as proof of causation. I would investigate the additional factors before making a definitive causal conclusion."


---

# FILE: docs/13_DECISION_LOG_TEMPLATE.md

# Decision Log Template

Use this file during development.

| Date | Decision | Reason | Alternatives considered | Impact | Owner |
|---|---|---|---|---|---|
| | | | | | |

Examples:

- Chose manual confirmation for column mapping.
- Chose local-first architecture.
- Disabled automatic outlier removal.
- Used median alongside mean for processing-time analysis.


---

# FILE: docs/14_CHANGELOG.md

# Changelog

## [0.1.0] - Initial specification
- Product blueprint created
- Schema-flexible architecture defined
- Data-quality framework defined
- Analytics rules defined
- Export requirements defined
- Test plan defined

## Future entries

Use format:

### Added
### Changed
### Fixed
### Removed


---

# FILE: docs/15_DATA_DICTIONARY_TEMPLATE.md

# Data Dictionary Template

Complete this when the live dataset arrives.

| Source Column | Analytical Role | Data Type | Definition | Unit | Allowed Values | Missing % | Notes |
|---|---|---|---|---|---|---:|---|
| | | | | | | | |

## Important questions

For every important field determine:

- What does one row represent?
- Is this a stock or a flow?
- Is the field cumulative?
- What reporting period does it cover?
- Is the denominator compatible?
- Is the value observed or estimated?
- Are definitions stable across periods?


---

# FILE: docs/16_ANTIGRAVITY_MASTER_BUILD_PROMPT.md

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


---

# FILE: docs/17_TOMORROW_DATA_ONBOARDING_CHECKLIST.md

# Tomorrow Data Onboarding Checklist

Use this immediately when the live assessment arrives.

## Step 1 — Read the instructions before opening the data

Record:

- exact question
- required output
- audience
- time limit
- whether external tools/code are permitted
- whether presentation is required

## Step 2 — Save an untouched copy

Do not edit the original assessment file.

## Step 3 — Upload to Performance Insight Explorer

Confirm:
- correct file
- correct sheet
- row count
- column count

## Step 4 — Identify row granularity

Answer:

**What does one row represent?**

Possible examples:
- case
- team-month
- application
- transaction
- employee
- day

Do not calculate rates until this is understood.

## Step 5 — Complete data dictionary

Use `15_DATA_DICTIONARY_TEMPLATE.md`.

## Step 6 — QA

Check:
- missing
- duplicates
- dates
- categories
- denominators
- outliers
- reconciliation

## Step 7 — Confirm mappings

Never accept suggested mapping without checking sample values.

## Step 8 — Run only relevant analysis

Do not analyse every available field.

Answer the assessment question.

## Step 9 — Review findings manually

For each finding ask:

- is it correct?
- does the chart support it?
- does it need a denominator?
- could another explanation exist?

## Step 10 — Export only after review

Use the Interview View or PowerPoint only if it matches the assessment instructions.


---

# FILE: docs/18_BSR_STAGE1_ALIGNMENT.md

# BSR Stage 1 Alignment

This document describes the first use case without hard-coding BSR into the product.

## Technical areas

The application should support evidence relevant to:

### Analysis and Insight
The user should be able to:
- identify trends
- compare groups
- calculate transparent performance measures
- investigate exceptions
- form evidence-based recommendations
- explain why a method was selected

### Communicating Analysis and Insight
The application should:
- provide audience-appropriate views
- use clear charts
- produce concise findings
- connect evidence to operational implications
- support verbal explanation

### Quality Assurance of Data and Analysis
The application should:
- profile source data
- identify missingness
- detect duplicates
- flag validity issues
- protect denominators
- record assumptions
- record limitations
- support reproducibility

## Possible operational concepts

The core product may support concepts such as:

- demand
- completions
- target performance
- backlog
- processing time
- availability
- utilisation
- productivity

These are analytical concepts, not hard-coded dataset columns.

## Important

When the live assessment arrives, follow the assessment instructions even if they differ from this initial use case.


---

# FILE: docs/19_PROJECT_FILE_STRUCTURE.md

# Recommended Project File Structure

```text
performance_insight_explorer/
│
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── CHANGELOG.md
│
├── pages/
│   ├── 01_upload_profile.py
│   ├── 02_data_quality.py
│   ├── 03_column_mapping.py
│   ├── 04_performance_overview.py
│   ├── 05_trends.py
│   ├── 06_comparisons.py
│   ├── 07_root_cause.py
│   ├── 08_insights.py
│   ├── 09_recommendations.py
│   ├── 10_interview_view.py
│   ├── 11_export.py
│   └── 12_audit_trail.py
│
├── src/
│   ├── ingestion.py
│   ├── profiling.py
│   ├── quality.py
│   ├── mapping.py
│   ├── metrics.py
│   ├── trends.py
│   ├── comparisons.py
│   ├── root_cause.py
│   ├── insights.py
│   ├── visualisations.py
│   ├── recommendations.py
│   ├── reporting.py
│   ├── powerpoint.py
│   └── audit.py
│
├── config/
│   ├── metric_definitions.yaml
│   ├── mapping_patterns.yaml
│   └── settings.yaml
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_quality.py
│   ├── test_mapping.py
│   ├── test_metrics.py
│   ├── test_trends.py
│   ├── test_exports.py
│   └── test_powerpoint.py
│
├── docs/
├── sample_data/
└── outputs/
    ├── reports/
    ├── presentations/
    ├── charts/
    └── audit/
```


---

# FILE: templates/ASSUMPTIONS_REGISTER.md

# Assumptions Register

| ID | Assumption | Why needed | Impact if wrong | Status |
|---|---|---|---|---|
| A1 | | | | Open |


---

# FILE: templates/LIMITATIONS_REGISTER.md

# Limitations Register

| ID | Limitation | Impact on analysis | Mitigation / next step |
|---|---|---|---|
| L1 | | | |
