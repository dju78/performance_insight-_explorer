import pytest
import pandas as pd
import os
from src.ingestion import generate_dataset_profile
from src.quality import run_structural_qa, evaluate_data_fitness
from src.mapping import suggest_mappings
from src.metrics import calculate_kpi_summary
from src.export import build_export_payload_from_state

DATASETS = [
    ("sample_data/customer_service_dataset.csv", "Customer Service"),
    ("sample_data/inspection_dataset.csv", "Inspections"),
    ("sample_data/case_level_dataset.csv", "Case Level"),
    ("sample_data/unfamiliar_operational_dataset.csv", "Licensing/Permits"),
    ("sample_data/poor_quality_dataset.csv", "Poor Quality Anomaly")
]

@pytest.mark.parametrize("file_path,name", DATASETS)
def test_full_pipeline_unknown_dataset(file_path, name):
    assert os.path.exists(file_path), f"Dataset {file_path} must exist"
    df = pd.read_csv(file_path)
    assert len(df) > 0, "Dataset must not be empty"
    
    # 1. Profile
    profile = generate_dataset_profile(df)
    assert "row_count" in profile
    assert "column_count" in profile or "col_count" in profile
    
    # 2. Quality QA
    qa = run_structural_qa(df)
    assert "health_score" in qa
    
    # 3. Mappings
    mappings = suggest_mappings(df)
    assert isinstance(mappings, dict)
    
    # 4. Fitness
    fitness = evaluate_data_fitness(qa, df, mappings)
    assert fitness["status"] in ["Fit for purpose", "Fit for purpose with caveats", "Insufficient for requested analysis"]
    
    # 5. Metrics
    kpis = calculate_kpi_summary(df, confirmed_mappings=mappings)
    assert isinstance(kpis, dict)
    
    # 6. Export payload
    mock_state = {
        "raw_df": df,
        "clean_df": df,
        "dataset_name": name,
        "row_granularity": "Records",
        "row_granularity_confirmed": True,
        "confirmed_mappings": mappings,
        "target_directions": {},
        "qa_report": qa,
        "insights_list": [{"id": "ins-1", "title": "Test Insight", "finding": "Observed variance", "evidence": "Verified", "severity": "medium", "status": "approved"}],
        "recommendations_list": [{"id": "rec-1", "title": "Test Rec", "action": "Rebalance queues", "owner": "Ops", "timeframe": "Week 1", "status": "approved"}],
        "assessment_question": "Investigate operational performance",
        "target_audience": "Panel",
        "response_time": "15 mins"
    }
    
    payload = build_export_payload_from_state(mock_state)
    assert payload["metadata"]["author"] == "DARAMOLA OMOYELE"
    assert payload["dataset"]["row_count"] == len(df)
    assert len(payload["findings"]) == 1
    assert len(payload["recommendations"]) == 1
