"""Unit tests for Group Comparisons module."""
import pandas as pd
from src.comparisons import compare_groups


def test_compare_groups_ranking():
    df = pd.DataFrame({
        "Team": ["Alpha", "Alpha", "Beta", "Beta", "Gamma"],
        "Completions": [50, 60, 30, 40, 90],
        "FTE": [5, 5, 5, 5, 10]
    })
    res = compare_groups(df, "Team", "Completions", denominator_col="FTE")
    assert res["top_performer"] == "Alpha"  # 110/10 = 11.0 rate vs Gamma 90/10 = 9.0 vs Beta 70/10 = 7.0
    assert res["bottom_performer"] == "Beta"
    assert "Gamma" in res["small_sample_groups"]  # N=1 < 5
