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


