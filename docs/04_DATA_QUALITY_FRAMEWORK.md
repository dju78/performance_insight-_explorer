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


