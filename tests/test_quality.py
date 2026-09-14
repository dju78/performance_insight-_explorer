"""Unit tests for Data Quality Engine."""
import pandas as pd
from src.quality import run_quality_audit, Severity


def test_quality_audit_clean_data():
    df = pd.DataFrame({
        "ID": [1, 2, 3],
        "Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
        "Value": [100, 200, 300]
    })
    report = run_quality_audit(df, {"ID": "record_id", "Date": "date", "Value": "actual"})
    assert report["critical_count"] == 0
    assert report["health_score"] >= 90.0


def test_quality_audit_dataset_c_anomalies():
    df_c = pd.read_csv("sample_data/dataset_c_poor_quality.csv")
    report = run_quality_audit(df_c, {
        "Row_ID": "record_id",
        "Log_Date": "date",
        "Cases_In": "received",
        "Cases_Out": "completed",
        "Opening_BL": "opening_backlog",
        "Closing_BL": "closing_backlog",
        "Staff_Count": "staff",
        "Target": "target"
    })
    
    # Must flag critical issues: duplicates, invalid dates, negative values, reconciliation gaps
    assert report["critical_count"] > 0
    issue_titles = [i["title"] for i in report["issues"]]
    assert any("Duplicate" in t for t in issue_titles)
    assert any("Invalid Date" in t for t in issue_titles)
    assert any("Negative Values" in t for t in issue_titles)
    assert any("Backlog" in t or "Reconciliation" in t for t in issue_titles)
