"""Unit tests for KPI Engine and mathematical formulas."""
import numpy as np
import pandas as pd
from src.metrics import safe_divide, calculate_kpis


def test_safe_divide_scalars():
    assert safe_divide(10, 2) == 5.0
    assert np.isnan(safe_divide(10, 0))
    assert np.isnan(safe_divide(0, 0))
    assert safe_divide(10, 0, fill_value=0.0) == 0.0


def test_safe_divide_series():
    s_num = pd.Series([10, 20, 30])
    s_den = pd.Series([2, 0, 5])
    res = safe_divide(s_num, s_den)
    assert res.iloc[0] == 5.0
    assert np.isnan(res.iloc[1])
    assert res.iloc[2] == 6.0


def test_calculate_kpis_comprehensive():
    df = pd.DataFrame({
        "Actual": [90, 110, 100],
        "Target": [100, 100, 100],
        "Completed": [45, 55, 50],
        "FTE": [5.0, 5.0, 5.0],
        "Hours_Used": [350, 360, 340],
        "Hours_Avail": [400, 400, 400],
        "Opening_BL": [100, 110, 115],
        "Closing_BL": [110, 115, 120],
        "Received": [55, 60, 55]
    })
    mappings = {
        "Actual": "actual",
        "Target": "target",
        "Completed": "completed",
        "FTE": "fte",
        "Hours_Used": "hours_used",
        "Hours_Avail": "hours_available",
        "Opening_BL": "opening_backlog",
        "Closing_BL": "closing_backlog",
        "Received": "received"
    }
    kpi_res = calculate_kpis(df, mappings)
    summary = kpi_res["summary_kpis"]
    
    # Target Achievement: 300 / 300 * 100 = 100%
    assert summary["target_achievement_pct"]["value"] == 100.0
    assert summary["target_variance"]["value"] == 0.0
    
    # Productivity: 150 / 5.0 = 30.0 cases/FTE
    assert summary["productivity"]["value"] == 30.0
    
    # Utilisation: 1050 / 1200 * 100 = 87.5%
    assert summary["utilisation_pct"]["value"] == 87.5
    
    # Backlog Observed: 120 - 100 = +20 cases
    assert summary["backlog_change"]["value"] == 20.0
