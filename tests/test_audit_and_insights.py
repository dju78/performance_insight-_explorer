"""Additional tests for audit, root cause, insights, and governance registers."""
import os
import pytest
import pandas as pd
import numpy as np
from src.audit import AuditLogger
from src.root_cause import analyze_root_cause_pillars, calculate_correlations
from src.insights import generate_insights
from src.recommendations import RecommendationEngine, AssumptionsRegister, LimitationsRegister


def test_audit_logger_flow():
    logger = AuditLogger()
    assert len(logger.get_dataframe()) == 0
    
    logger.log("TEST_EVENT", "Test description", "file.csv", "Sheet1", row_count=100, col_count=10)
    df_audit = logger.get_dataframe()
    assert len(df_audit) == 1
    assert df_audit.iloc[0]["event_type"] == "TEST_EVENT"
    assert df_audit.iloc[0]["filename"] == "file.csv"
    
    csv_str = logger.to_csv()
    assert "TEST_EVENT" in csv_str


def test_root_cause_correlations_and_disclaimer():
    df = pd.DataFrame({
        "A": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "B": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        "C": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    })
    corr_res = calculate_correlations(df, ["A", "B", "C"])
    assert "disclaimer" in corr_res
    assert "causation" in corr_res["disclaimer"].lower()
    assert corr_res["pearson_matrix"].loc["A", "B"] == 1.0
    assert corr_res["pearson_matrix"].loc["A", "C"] == -1.0


def test_root_cause_pillars_analysis():
    df = pd.DataFrame({
        "Cases_In": [100, 150, 120, 200],
        "Staff_FTE": [10, 10, 10, 10],
        "Cycle_Days": [12, 15, 14, 25]
    })
    mappings = {"Cases_In": "received", "Staff_FTE": "fte", "Cycle_Days": "processing_time"}
    kpi_res = {"summary_kpis": {"utilisation_pct": {"value": 94.0}}}
    qa_report = {"health_score": 92.0, "critical_count": 0, "warning_count": 1}
    
    pillars = analyze_root_cause_pillars(df, mappings, kpi_res, qa_report)
    assert "demand" in pillars
    assert "capacity" in pillars
    assert "process" in pillars
    assert "complexity" in pillars
    assert "data_quality" in pillars
    assert pillars["capacity"]["risk_level"] == "High"


def test_insights_and_recommendations_integration():
    kpi_res = {
        "summary_kpis": {
            "target_achievement_pct": {"value": 105.0},
            "target_variance": {"value": 50},
            "backlog_change": {"value": -20},
            "productivity": {"value": 15.2, "unit": "Cases/FTE"},
            "utilisation_pct": {"value": 85.0}
        }
    }
    qa_report = {"health_score": 98.0, "critical_count": 0, "warning_count": 0}
    
    insights = generate_insights(kpi_res, qa_report)
    assert len(insights) >= 3
    for ins in insights:
        assert "finding" in ins
        assert "evidence" in ins
        assert "interpretation" in ins
        assert "business_implication" in ins
        assert "recommendation" in ins
        assert "limitation" in ins
        assert "traceable_metric" in ins
        
    recs = RecommendationEngine.generate_recommendations(insights, qa_report)
    assert "Act" in recs
    assert "Investigate" in recs
    assert "Monitor" in recs
    assert "Improve Reporting" in recs


def test_assumptions_and_limitations_registers():
    asm = AssumptionsRegister()
    new_id = asm.add("Test Assumption", "Why", "Impact")
    assert new_id.startswith("ASM-")
    assert len(asm.get_dataframe()) >= 4
    
    lim = LimitationsRegister()
    new_lim_id = lim.add("Test Limitation", "Impact", "Mitigation")
    assert new_lim_id.startswith("LIM-")
    assert len(lim.get_dataframe()) >= 3
