import os
import sys
import py_compile
import importlib
import pytest
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

ALL_PAGES = [
    "app.py",
    "pages/01_upload_profile.py",
    "pages/02_data_quality.py",
    "pages/03_column_mapping.py",
    "pages/04_performance_overview.py",
    "pages/05_trends.py",
    "pages/06_comparisons.py",
    "pages/07_root_cause.py",
    "pages/08_insights.py",
    "pages/09_recommendations.py",
    "pages/10_public_presentation.py",
    "pages/11_export.py",
    "pages/12_audit_trail.py"
]

@pytest.mark.parametrize("page_rel_path", ALL_PAGES)
def test_page_syntax_and_compilation(page_rel_path):
    """Verify every single page compiles without syntax errors."""
    full_path = os.path.join(ROOT, page_rel_path)
    assert os.path.exists(full_path), f"Page file missing: {page_rel_path}"
    py_compile.compile(full_path, doraise=True)

def test_src_modules_import_cleanly():
    """Verify all backend analytics, metrics, QA, trends, comparisons, and export engines import without error."""
    src_modules = [
        "src.state",
        "src.ingestion",
        "src.profiling",
        "src.quality",
        "src.mapping",
        "src.metrics",
        "src.trends",
        "src.comparisons",
        "src.root_cause",
        "src.insights",
        "src.recommendations",
        "src.visualisations",
        "src.reporting",
        "src.audit",
        "src.export",
        "src.powerpoint",
        "src.pdf_report",
        "src.brief_extractor",
        "src.relationships"
    ]
    for mod_name in src_modules:
        mod = importlib.import_module(mod_name)
        assert mod is not None, f"Failed to import {mod_name}"

def test_full_pipeline_and_exports_simulation():
    """Simulate full end-to-end data pipeline from ingestion to multi-format export."""
    from src.ingestion import ingest_file
    from src.quality import run_quality_audit
    from src.mapping import suggest_mappings
    from src.metrics import calculate_kpis
    from src.trends import calculate_trend_summary
    from src.comparisons import compare_groups
    from src.insights import generate_rule_based_insights
    from src.recommendations import RecommendationEngine
    from src.export import (
        build_export_payload_from_state,
        generate_pdf_report,
        generate_powerpoint_deck,
        generate_executive_excel_pack,
        generate_audit_trail_text
    )
    
    # 1. Ingest sample data
    sample_path = os.path.join(ROOT, "sample_data", "dataset_a_team_month.xlsx")
    assert os.path.exists(sample_path)
    
    df, sheets, meta = ingest_file(sample_path)
    assert df is not None and len(df) > 0
    
    # 2. QA & Mapping
    mappings = suggest_mappings(df)
    qa_report = run_quality_audit(df, mappings)
    assert qa_report["health_score"] >= 0
    
    # 3. Metrics
    kpi_res = calculate_kpis(df, mappings, target_direction="higher_is_better")
    date_c = mappings.get("date")
    num_cols = list(df.select_dtypes(include=[np.number]).columns)
    metric_c = mappings.get("performance_score") or mappings.get("volume") or (num_cols[0] if num_cols else None)
    obj_cols = [c for c in df.columns if df[c].dtype == "object" or str(df[c].dtype).startswith("str")]
    group_c = mappings.get("category") or mappings.get("team") or (obj_cols[0] if obj_cols else df.columns[0])
    
    trend_res = calculate_trend_summary(df, date_c, metric_c)
    comp_res = compare_groups(df, group_c, metric_c)
    
    # 4. Insights & Recs
    insights = generate_rule_based_insights(df, mappings, target_directions={"score": "higher_is_better"})
    engine = RecommendationEngine()
    recs = engine.generate_recommendations(insights, qa_report=qa_report)
    
    # 5. Build Payload
    sim_state = {
        "raw_df": df,
        "clean_df": df,
        "confirmed_mappings": mappings,
        "row_granularity": "Periodic snapshot",
        "row_granularity_confirmed": True,
        "insights_list": [{"finding": i.get("title", ""), "status": "approved"} for i in insights],
        "recommendations_list": [{"recommendation": r.get("title", ""), "category": r.get("category", "Act"), "status": "approved"} for r in recs],
        "dataset_name": "dataset_a_team_month.xlsx",
        "active_sheet": "Sheet1",
        "assessment_question": "Evaluate team monthly delivery trends",
        "questions_must_answer": "1. Which teams met target?\n2. What is the overall trend?",
        "target_audience": "Director of Operations",
        "response_time": "15 mins",
        "trend_summary": trend_res,
        "comparison_summary": comp_res,
        "qa_report": qa_report,
        "kpi_results": kpi_res,
        "assumptions": [{"assumption": "Monthly reporting cycles"}],
        "limitations": [{"limitation": "No case-level variance"}],
        "audit_trail": [{"event_type": "DATA_INGESTED", "action": "Loaded dataset_a", "timestamp": "2026-09-15T09:30:00"}]
    }
    
    payload = build_export_payload_from_state(sim_state)
    assert payload["is_valid_for_export"] is True
    
    # 6. Test PDF export
    pdf_out = os.path.join(ROOT, "outputs", "briefs", "test_e2e_simulation.pdf")
    p_pdf = generate_pdf_report(payload, audience="Senior Leadership", output_filepath=pdf_out)
    assert os.path.exists(p_pdf) and os.path.getsize(p_pdf) > 1000
    
    # 7. Test PPTX export
    pptx_out = os.path.join(ROOT, "outputs", "presentations", "test_e2e_simulation.pptx")
    p_pptx = generate_powerpoint_deck(payload, output_filepath=pptx_out, include_appendix=True)
    assert os.path.exists(p_pptx) and os.path.getsize(p_pptx) > 10000
    
    # 8. Test Excel export
    xlsx_out = os.path.join(ROOT, "outputs", "reports", "test_e2e_simulation.xlsx")
    p_xlsx = generate_executive_excel_pack(payload, output_filepath=xlsx_out)
    assert os.path.exists(p_xlsx) and os.path.getsize(p_xlsx) > 5000
    
    # 9. Test Audit Trail export
    txt_out = os.path.join(ROOT, "outputs", "audit", "test_e2e_audit.txt")
    p_txt = generate_audit_trail_text(payload["audit_trail"], output_filepath=txt_out)
    assert os.path.exists(p_txt) and os.path.getsize(p_txt) > 50
