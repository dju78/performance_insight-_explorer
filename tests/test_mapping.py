"""Unit tests for column role mapping module."""
import pandas as pd
from src.mapping import suggest_mappings, validate_mappings, ROLE_CATALOGUE


def test_suggest_mappings_keywords():
    df = pd.DataFrame({
        "case_reference_id": [1, 2],
        "received_date": ["2025-01-01", "2025-01-02"],
        "cases_completed": [10, 15],
        "staff_fte": [2.5, 3.0],
        "target_output": [12, 14]
    })
    suggs = suggest_mappings(df)
    assert suggs["case_reference_id"]["suggested_role"] == "record_id"
    assert suggs["received_date"]["suggested_role"] == "date"
    assert suggs["cases_completed"]["suggested_role"] in ["completed", "actual"]
    assert suggs["staff_fte"]["suggested_role"] == "fte"
    assert suggs["target_output"]["suggested_role"] == "target"


def test_validate_mappings_enabled_kpis():
    df = pd.DataFrame({
        "col_a": [10, 20],
        "col_b": [2, 4]
    })
    confirmed = {"col_a": "completed", "col_b": "fte"}
    res = validate_mappings(confirmed, df)
    assert res["kpi_status"]["productivity"]["enabled"] is True
    assert res["kpi_status"]["utilisation"]["enabled"] is False
