"""Unit tests for PowerPoint 6-slide deck generator."""
import os
from pptx import Presentation
from src.powerpoint import generate_powerpoint_presentation


def test_generate_powerpoint_deck():
    out_path = "outputs/presentations/test_deck.pptx"
    meta = {"filename": "test.csv", "row_count": 100, "column_count": 5}
    qa = {"critical_count": 0, "warning_count": 1, "health_score": 95.0, "issues": []}
    kpi_sum = {"target_achievement_pct": {"name": "Target Achievement %", "value": 102.5, "unit": "%", "formula": "A/T*100", "interpretation": "Target met."}}
    insights = [{"category": "Target", "finding": "Good delivery.", "evidence": "102.5%", "business_implication": "Safe", "recommendation": "Maintain"}]
    recs = {"Act": [{"title": "Rebalance", "action": "Rebalance load", "rationale": "Throughput", "owner": "Ops"}]}
    
    path = generate_powerpoint_presentation(
        out_path, meta, qa, kpi_sum, None, None, insights, recs, [], []
    )
    assert os.path.exists(path)
    
    prs = Presentation(path)
    assert len(prs.slides) == 6
