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


