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


