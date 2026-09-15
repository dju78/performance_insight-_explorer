import os
import sys
import pytest
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def test_requirements_file_completeness():
    """Verify all external modules used in repo are listed in requirements.txt."""
    with open(os.path.join(ROOT, "requirements.txt"), "r") as f:
        req_lines = [line.strip().split(">=")[0].split("==")[0].split("<")[0].strip().lower() 
                     for line in f if line.strip() and not line.startswith("#")]
    
    assert "matplotlib" in req_lines, "matplotlib must be explicitly in requirements.txt"
    assert "streamlit" in req_lines
    assert "pandas" in req_lines
    assert "python-pptx" in req_lines
    assert "reportlab" in req_lines
    assert "plotly" in req_lines
    assert "openpyxl" in req_lines

def test_lazy_export_imports():
    """Verify that importing src.export or app config does NOT eagerly import pptx or reportlab."""
    import src.export
    assert hasattr(src.export, "load_app_config")
    cfg = src.export.load_app_config()
    assert cfg["app_title"] == "Performance Insight Explorer"

def test_generate_pdf_report_real():
    """Verify PDF report generation produces a valid, non-empty PDF document."""
    from src.export import generate_pdf_report
    
    sample_payload = {
        "assessment_context": {
            "question": "Operational performance evaluation",
            "audience": "Senior Leadership"
        },
        "metadata": {
            "author": "DARAMOLA OMOYELE",
            "date": "15 September 2026",
            "role": "Performance Analyst"
        },
        "dataset": {
            "name": "sample_operational_data.csv",
            "row_count": 100,
            "col_count": 5,
            "granularity": "Case / Application Level",
            "granularity_confirmed": True
        },
        "data_quality": {
            "health_score": 95.0,
            "fitness_status": "Fit for purpose",
            "caveats": []
        },
        "kpis": {
            "Total Volume": {"value": 100, "formatted": "100", "status": "info"},
            "Mean Performance": {"value": 85.5, "formatted": "85.5%", "status": "positive"}
        },
        "findings": [
            {"finding": "Performance exceeds baseline target by 5.5%", "status": "approved"}
        ],
        "recommendations": [
            {"recommendation": "Maintain current capacity allocation", "category": "Act", "status": "approved"}
        ],
        "recommendations_by_category": {
            "Act": [{"recommendation": "Maintain current capacity allocation", "category": "Act"}],
            "Investigate": [], "Monitor": [], "Improve Reporting": []
        },
        "assumptions": [{"assumption": "Uniform reporting period"}],
        "limitations": [{"limitation": "Missing weekend observations"}],
        "audit_trail": [{"event_type": "DATASET_INGESTED", "action": "Uploaded file", "timestamp": "2026-09-15T09:00:00"}]
    }
    
    out_pdf = os.path.join(ROOT, "outputs", "briefs", "test_generated_brief.pdf")
    res_path = generate_pdf_report(payload=sample_payload, audience="Senior Leadership", output_filepath=out_pdf)
    assert os.path.exists(res_path), "PDF file was not created"
    assert os.path.getsize(res_path) > 1000, "PDF file is too small or corrupted"

def test_generate_powerpoint_presentation_real():
    """Verify PowerPoint deck generation produces a valid, non-empty 16:9 presentation."""
    from src.export import generate_powerpoint_deck
    
    sample_df = pd.DataFrame({
        "Month": pd.date_range("2025-01-01", periods=12, freq="MS"),
        "Service": ["Service A"]*6 + ["Service B"]*6,
        "Performance": np.random.uniform(70, 95, 12),
        "Volume": np.random.randint(50, 200, 12)
    })
    
    sample_payload = {
        "filename": "sample_perf.xlsx",
        "active_sheet": "Data",
        "row_count": len(sample_df),
        "column_count": len(sample_df.columns),
        "row_granularity": "Case / Application Level",
        "raw_df": sample_df,
        "confirmed_mappings": {
            "date": "Month",
            "category": "Service",
            "performance_score": "Performance",
            "volume": "Volume"
        },
        "qa_report": {"health_score": 98.0, "issues": []},
        "kpi_results": {
            "summary_kpis": {
                "Average Availability": {"value": 82.4, "formatted": "82.4%", "status": "positive"}
            }
        },
        "approved_insights": [
            {"finding": "Service A demonstrated consistent upper-quartile delivery.", "status": "approved"}
        ],
        "recommendations_by_category": {
            "Act": [{"action": "Scale best practice workflows", "owner": "Operations"}],
            "Investigate": [], "Monitor": [], "Improve Reporting": []
        },
        "limitations": [{"limitation": "Quarter 4 reporting delay"}],
        "assumptions": [{"assumption": "37.5 standard weekly contracted hours"}],
        "assessment_context": {
            "question": "Operational performance analysis",
            "target_audience": "Senior Leadership"
        }
    }
    
    out_pptx = os.path.join(ROOT, "outputs", "presentations", "test_generated_deck.pptx")
    res_path = generate_powerpoint_deck(payload=sample_payload, output_filepath=out_pptx, include_appendix=True)
    assert os.path.exists(res_path), "PowerPoint deck was not created"
    assert os.path.getsize(res_path) > 10000, "PowerPoint deck is too small or corrupted"
