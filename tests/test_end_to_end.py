"""End-to-End Integration workflow test."""
import os
import pandas as pd
from src.ingestion import load_file
from src.profiling import profile_dataset
from src.mapping import suggest_mappings, validate_mappings
from src.quality import run_quality_audit
from src.metrics import calculate_kpis
from src.trends import calculate_trends
from src.comparisons import compare_groups
from src.insights import generate_insights
from src.recommendations import RecommendationEngine
from src.powerpoint import generate_powerpoint_presentation
from src.reporting import generate_excel_summary


def test_full_pipeline_dataset_a():
    # 1. Ingestion
    df, sheets, meta = load_file("sample_data/dataset_a_team_month.csv", "dataset_a_team_month.csv")
    assert len(df) == 48
    
    # 2. Profiling
    prof = profile_dataset(df, "dataset_a_team_month.csv")
    assert prof["row_count"] == 48
    
    # 3. Mapping
    suggs = suggest_mappings(df)
    confirmed = {c: suggs[c]["suggested_role"] for c in df.columns if suggs[c]["suggested_role"]}
    val_res = validate_mappings(confirmed, df)
    assert val_res["enabled_kpi_count"] >= 3
    
    # 4. Quality
    qa = run_quality_audit(df, confirmed)
    assert qa["health_score"] >= 80.0
    
    # 5. KPIs
    kpi_res = calculate_kpis(df, confirmed)
    assert "target_achievement_pct" in kpi_res["summary_kpis"]
    assert "productivity" in kpi_res["summary_kpis"]
    
    # 6. Trends
    trend_res = calculate_trends(df, "Reporting_Month", "Cases_Completed")
    assert not trend_res.get("error")
    
    # 7. Comparisons
    comp_res = compare_groups(df, "Operational_Team", "Cases_Completed", denominator_col="Staff_FTE")
    assert not comp_res.get("error")
    
    # 8. Insights & Recommendations
    insights = generate_insights(kpi_res, qa, trend_res, comp_res)
    assert len(insights) >= 3
    recs = RecommendationEngine.generate_recommendations(insights, qa)
    assert len(recs["Act"]) > 0
    
    # 9. Exports
    ppt_out = "outputs/presentations/e2e_test_deck.pptx"
    generate_powerpoint_presentation(
        ppt_out, meta, qa, kpi_res["summary_kpis"], trend_res, comp_res, insights, recs, [], []
    )
    assert os.path.exists(ppt_out)
    
    xl_out = "outputs/reports/e2e_test_summary.xlsx"
    generate_excel_summary(
        xl_out, df, prof, qa, kpi_res, trend_res["trend_df"], comp_res["comparison_df"], insights, recs, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    )
    assert os.path.exists(xl_out)
