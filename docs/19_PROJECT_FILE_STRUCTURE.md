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


