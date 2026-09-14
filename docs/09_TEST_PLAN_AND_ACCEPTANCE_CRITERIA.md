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


