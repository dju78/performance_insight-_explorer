import pytest
import pandas as pd
from src.state import init_session_state, reset_derived_state_for_new_dataset
from src.ingestion import generate_dataset_profile
from src.quality import run_structural_qa, evaluate_data_fitness
from src.mapping import suggest_mappings
from src.metrics import calculate_kpi_summary
from src.export import build_export_payload_from_state
from src.powerpoint import generate_assessment_presentation
from src.pdf_report import generate_pdf_report

def test_simulated_unknown_assessment():
    """Simulates receiving an unknown assessment brief and dataset."""
    # Step 1: Assessment Intake
    intake = {
        "assessment_question": "Determine why customer wait times spiked in Q3 and propose operational remedies.",
        "questions_must_answer": "Which channels missed SLA?\nWhat is the capacity deficit?",
        "target_audience": "Director of Customer Services",
        "response_time": "10 minutes briefing",
        "mandatory_measures": "Wait time SLA < 60s"
    }
    
    # Step 2: Ingest unknown dataset
    df = pd.read_csv("sample_data/customer_service_dataset.csv")
    profile = generate_dataset_profile(df)
    qa = run_structural_qa(df)
    
    # Step 3: Column Mappings
    mappings = suggest_mappings(df)
    fitness = evaluate_data_fitness(qa, df, mappings)
    assert fitness["status"] in ["Fit for purpose", "Fit for purpose with caveats"]
    
    # Step 4: Calculate KPIs
    kpis = calculate_kpi_summary(df, confirmed_mappings=mappings)
    assert len(kpis) > 0
    
    # Step 5: Analyst Approves Diagnostic Insights and Recommendations
    state = {
        "raw_df": df,
        "clean_df": df,
        "dataset_name": "Customer Support Operations",
        "row_granularity": "Periodic snapshot",
        "row_granularity_confirmed": True,
        "confirmed_mappings": mappings,
        "target_directions": {"Average_Wait_Time_Sec": "lower"},
        "qa_report": qa,
        "insights_list": [
            {
                "id": "ins-1",
                "title": "Wait Time Exceeded SLA in Telephony",
                "finding": "Telephony average wait time reached 140s vs 60s target.",
                "evidence": "Average_Wait_Time_Sec in Telephony channel",
                "severity": "high",
                "status": "approved"
            }
        ],
        "recommendations_list": [
            {
                "id": "rec-1",
                "title": "Implement Multi-Skilling and Shift Rebalancing",
                "action": "Train web chat agents for peak telephony overflow.",
                "owner": "Head of Contact Centre",
                "timeframe": "Immediate (Days 1-14)",
                "expected_impact": "Reduce telephony wait time by 35%",
                "status": "approved"
            }
        ],
        **intake
    }
    
    # Step 6: Build Export Payload
    payload = build_export_payload_from_state(state)
    assert payload["metadata"]["author"] == "DARAMOLA OMOYELE"
    assert payload["metadata"]["target_audience"] == "Director of Customer Services"
    
    # Step 7: Export Presentations and Documents
    prs = generate_assessment_presentation(payload)
    assert prs is not None
    assert len(prs.slides) >= 6
    
    pdf = generate_pdf_report(payload)
    assert pdf is not None
    assert len(pdf) > 1000
