"""Unit tests for Trend Analysis module."""
import pandas as pd
from src.trends import calculate_trends


def test_calculate_trends_chronological():
    df = pd.DataFrame({
        "Month": ["2025-01", "2025-02", "2025-03", "2025-04"],
        "Output": [100, 120, 150, 180]
    })
    res = calculate_trends(df, "Month", "Output")
    assert res["period_count"] == 4
    assert res["net_change"] == 80.0
    assert res["peak"]["value"] == 180.0
    assert res["trough"]["value"] == 100.0
    assert res["sustained_increase"] is True
