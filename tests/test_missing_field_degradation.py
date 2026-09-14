import pytest
import pandas as pd
from src.metrics import calculate_kpi_summary, calculate_utilisation
from src.trends import calculate_trend_summary
from src.comparisons import compare_groups
from src.powerpoint import generate_assessment_presentation
from src.pdf_report import generate_pdf_report

def test_missing_date_trend_graceful_degradation():
    df = pd.DataFrame({"Volume": [10, 20, 30], "Team": ["A", "B", "C"]})
    # Date column not provided
    trend = calculate_trend_summary(df, date_col=None, metric_col="Volume")
    assert trend["direction"] == "Insufficient time points" or trend["direction"] == "Stable"

def test_missing_fte_utilisation_graceful_degradation():
    df = pd.DataFrame({"Volume": [10, 20, 30], "Team": ["A", "B", "C"]})
    util = calculate_utilisation(df, volume_col="Volume", fte_col=None)
    assert util["available"] is False
    assert "Omitted" in util["reason"] or "not available" in util["reason"].lower()

def test_export_with_missing_optional_analyses():
    df = pd.DataFrame({"Volume": [100, 200], "Category": ["X", "Y"]})
    mock_payload = {
        "metadata": {
            "author": "DARAMOLA OMOYELE",
            "assessment_question": "Basic evaluation",
            "target_audience": "Panel",
            "date": "2026-09-14",
            "time_available": "15 mins",
            "role": "Performance Analyst (HEO)"
        },
        "dataset": {
            "name": "Minimal Dataset",
            "row_count": 2,
            "col_count": 2,
            "granularity": "Records",
            "granularity_confirmed": True
        },
        "data_quality": {
            "health_score": 100.0,
            "fitness_status": "Fit for purpose",
            "fitness_reasons": ["Clean basic dataset"],
            "caveats": []
        },
        "kpis": {
            "volume": {
                "display_name": "Total Volume",
                "actual": 300,
                "target": None,
                "variance_pct": None,
                "unit": "units",
                "is_favorable": True,
                "commentary": "Total volume across records."
            }
        },
        "findings": [],
        "recommendations": [],
        "comparisons": None,
        "trends": None,
        "capacity": None,
        "driver_trees": None
    }
    
    # Generate PPTX without throwing errors
    prs = generate_assessment_presentation(mock_payload)
    assert prs is not None
    assert len(prs.slides) >= 6
    
    # Generate PDF without throwing errors
    pdf_bytes = generate_pdf_report(mock_payload)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
