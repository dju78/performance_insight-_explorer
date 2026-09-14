"""Edge case testing for schema-flexible robustness."""
import numpy as np
import pandas as pd
from src.profiling import profile_dataset
from src.quality import run_quality_audit
from src.metrics import calculate_kpis, safe_divide


def test_empty_dataframe():
    df_empty = pd.DataFrame()
    prof = profile_dataset(df_empty, "empty.csv")
    assert prof["row_count"] == 0
    assert prof["column_count"] == 0
    
    qa = run_quality_audit(df_empty)
    assert qa["critical_count"] == 1


def test_single_row_dataframe():
    df_single = pd.DataFrame({"Actual": [100], "Target": [50]})
    kpi_res = calculate_kpis(df_single, {"Actual": "actual", "Target": "target"})
    assert kpi_res["summary_kpis"]["target_achievement_pct"]["value"] == 200.0


def test_all_zero_denominators():
    df_zero = pd.DataFrame({"Actual": [100, 200], "Target": [0, 0]})
    kpi_res = calculate_kpis(df_zero, {"Actual": "actual", "Target": "target"})
    assert kpi_res["summary_kpis"]["target_achievement_pct"]["value"] is None


def test_no_numeric_fields():
    df_text = pd.DataFrame({"Name": ["Alpha", "Beta"], "City": ["London", "Manchester"]})
    prof = profile_dataset(df_text, "text.csv")
    assert len(prof["candidate_numerics"]) == 0
    
    kpi_res = calculate_kpis(df_text, {"Name": "team", "City": "location"})
    assert len(kpi_res["summary_kpis"]) == 0
