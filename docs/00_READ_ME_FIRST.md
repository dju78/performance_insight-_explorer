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


