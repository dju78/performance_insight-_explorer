"""Unit tests for data profiling module."""
import pandas as pd
from src.profiling import profile_dataset


def test_profile_basic():
    df = pd.DataFrame({
        "ID": [1, 2, 3, 4],
        "Date": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"],
        "Cases": [10, 20, 30, 40],
        "Team": ["Alpha", "Beta", "Alpha", "Beta"]
    })
    prof = profile_dataset(df, "test.csv")
    assert prof["row_count"] == 4
    assert prof["column_count"] == 4
    assert "Date" in prof["candidate_dates"]
    assert "Cases" in prof["candidate_numerics"]
    assert "ID" in prof["candidate_ids"]
