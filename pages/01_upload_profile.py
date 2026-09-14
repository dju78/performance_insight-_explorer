import io
import os
import streamlit as st
import pandas as pd
from src.state import (
    init_session_state,
    compute_dataset_fingerprint,
    reset_derived_state_for_new_dataset,
    clear_dataset_for_new_upload
)
from src.ingestion import ingest_file, generate_dataset_profile, get_excel_sheet_names
from src.quality import run_structural_qa
from src.mapping import suggest_mappings

init_session_state()

st.title("📂 01. Data Upload & Profiling")
st.markdown("Upload any operational dataset (`.csv`, `.xlsx`, `.xls`), select active worksheets, or load benchmark test data.")

# Clear Data Button (if data currently loaded)
if st.session_state.get("raw_df") is not None:
    c_clear, _ = st.columns([1, 2])
    with c_clear:
        if st.button("🗑️ Clear Current Data & Start New Upload", type="secondary", use_container_width=True):
            clear_dataset_for_new_upload(preserve_assessment_context=True)
            st.success("Current dataset cleared. You may now upload a new dataset.")
            st.rerun()

# Dynamic uploader key for clean visual reset
upload_ver = st.session_state.get("upload_widget_version", 0)
uploaded_file = st.file_uploader("Upload Operational Data File", type=["csv", "xlsx", "xls"], key=f"uploader_{upload_ver}")

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    if st.button("Load: Standard Ops (Dataset A)", use_container_width=True):
        try:
            df = pd.read_csv("sample_data/dataset_a_team_month.csv")
            fp = compute_dataset_fingerprint(df, "dataset_a_team_month.csv")
            if fp != st.session_state.get("dataset_fingerprint"):
                reset_derived_state_for_new_dataset(fp)
            st.session_state["raw_df"] = df.copy()
            st.session_state["clean_df"] = df.copy()
            st.session_state["dataset_name"] = "Dataset A (Team-Month Benchmark)"
            st.session_state["active_sheet"] = "CSV_Default"
            st.session_state["data_profile"] = generate_dataset_profile(df)
            st.session_state["structural_qa_report"] = run_structural_qa(df)
            st.session_state["qa_report"] = st.session_state["structural_qa_report"]
            st.session_state["suggested_mappings"] = suggest_mappings(df)
            st.session_state["row_granularity"] = "Periodic snapshot"
            st.session_state["row_granularity_confirmed"] = True
            st.session_state.audit_logger.log(
                "FILE_UPLOADED", "Loaded Dataset A", filename="dataset_a_team_month.csv",
                row_count=len(df), col_count=len(df.columns), details={"fingerprint": fp}
            )
            st.session_state.audit_logger.log("STRUCTURAL_QA_COMPLETED", "Executed Stage A Structural QA", details={"health_score": st.session_state["qa_report"]["health_score"]})
            st.success("Loaded Dataset A successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading sample: {e}")

with col_s2:
    if st.button("Load: Case Details (Dataset B)", use_container_width=True):
        try:
            df = pd.read_csv("sample_data/dataset_b_case_level.csv")
            fp = compute_dataset_fingerprint(df, "dataset_b_case_level.csv")
            if fp != st.session_state.get("dataset_fingerprint"):
                reset_derived_state_for_new_dataset(fp)
            st.session_state["raw_df"] = df.copy()
            st.session_state["clean_df"] = df.copy()
            st.session_state["dataset_name"] = "Dataset B (Case Level Details)"
            st.session_state["active_sheet"] = "CSV_Default"
            st.session_state["data_profile"] = generate_dataset_profile(df)
            st.session_state["structural_qa_report"] = run_structural_qa(df)
            st.session_state["qa_report"] = st.session_state["structural_qa_report"]
            st.session_state["suggested_mappings"] = suggest_mappings(df)
            st.session_state["row_granularity"] = "Case / record"
            st.session_state["row_granularity_confirmed"] = True
            st.session_state.audit_logger.log(
                "FILE_UPLOADED", "Loaded Dataset B", filename="dataset_b_case_level.csv",
                row_count=len(df), col_count=len(df.columns), details={"fingerprint": fp}
            )
            st.session_state.audit_logger.log("STRUCTURAL_QA_COMPLETED", "Executed Stage A Structural QA", details={"health_score": st.session_state["qa_report"]["health_score"]})
            st.success("Loaded Dataset B successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading sample: {e}")

with col_s3:
    if st.button("Load: Dirty Anomaly (Dataset C)", use_container_width=True):
        try:
            df = pd.read_csv("sample_data/dataset_c_poor_quality.csv")
            fp = compute_dataset_fingerprint(df, "dataset_c_poor_quality.csv")
            if fp != st.session_state.get("dataset_fingerprint"):
                reset_derived_state_for_new_dataset(fp)
            st.session_state["raw_df"] = df.copy()
            st.session_state["clean_df"] = df.copy()
            st.session_state["dataset_name"] = "Dataset C (Poor Quality Anomaly)"
            st.session_state["active_sheet"] = "CSV_Default"
            st.session_state["data_profile"] = generate_dataset_profile(df)
            st.session_state["structural_qa_report"] = run_structural_qa(df)
            st.session_state["qa_report"] = st.session_state["structural_qa_report"]
            st.session_state["suggested_mappings"] = suggest_mappings(df)
            st.session_state["row_granularity"] = "Transaction / event"
            st.session_state["row_granularity_confirmed"] = True
            st.session_state.audit_logger.log(
                "FILE_UPLOADED", "Loaded Dataset C", filename="dataset_c_poor_quality.csv",
                row_count=len(df), col_count=len(df.columns), details={"fingerprint": fp}
            )
            st.session_state.audit_logger.log("STRUCTURAL_QA_COMPLETED", "Executed Stage A Structural QA", details={"health_score": st.session_state["qa_report"]["health_score"]})
            st.success("Loaded Dataset C successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading sample: {e}")

with col_s4:
    if st.button("Load: 15-Col Assessment Test", use_container_width=True):
        try:
            df = pd.read_csv("sample_data/performance_insight_explorer_test_data.csv")
            fp = compute_dataset_fingerprint(df, "performance_insight_explorer_test_data.csv")
            if fp != st.session_state.get("dataset_fingerprint"):
                reset_derived_state_for_new_dataset(fp)
            st.session_state["raw_df"] = df.copy()
            st.session_state["clean_df"] = df.copy()
            st.session_state["dataset_name"] = "Assessment Benchmark Test Data (15 Cols)"
            st.session_state["active_sheet"] = "CSV_Default"
            st.session_state["data_profile"] = generate_dataset_profile(df)
            st.session_state["structural_qa_report"] = run_structural_qa(df)
            st.session_state["qa_report"] = st.session_state["structural_qa_report"]
            st.session_state["suggested_mappings"] = suggest_mappings(df)
            st.session_state["row_granularity"] = "Periodic snapshot"
            st.session_state["row_granularity_confirmed"] = True
            st.session_state.audit_logger.log(
                "FILE_UPLOADED", "Loaded 15-Col Assessment Benchmark", filename="performance_insight_explorer_test_data.csv",
                row_count=len(df), col_count=len(df.columns), details={"fingerprint": fp}
            )
            st.session_state.audit_logger.log("STRUCTURAL_QA_COMPLETED", "Executed Stage A Structural QA", details={"health_score": st.session_state["qa_report"]["health_score"]})
            st.success("Loaded 15-Column Test Data successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading test CSV: {e}")

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        sheets = []
        selected_sheet = None
        
        if ext in [".xlsx", ".xls", ".xlsm"]:
            bio = io.BytesIO(file_bytes)
            sheets = get_excel_sheet_names(bio)
            if len(sheets) > 1:
                cur_sheet = st.session_state.get("active_sheet")
                default_sheet_idx = sheets.index(cur_sheet) if cur_sheet in sheets else 0
                selected_sheet = st.selectbox(
                    "📑 Select Worksheet to Analyse:",
                    sheets,
                    index=default_sheet_idx,
                    help="Choose the operational data sheet to analyse. Avoid selecting README or metadata sheets."
                )
            elif len(sheets) == 1:
                selected_sheet = sheets[0]
                
        # Ingest file
        bio_ingest = io.BytesIO(file_bytes)
        raw_df, clean_df, profile = ingest_file(bio_ingest, uploaded_file.name, sheet_name=selected_sheet)
        fp = compute_dataset_fingerprint(clean_df, uploaded_file.name, sheet_name=selected_sheet or "")
        
        # Check if dataset or worksheet changed
        if fp != st.session_state.get("dataset_fingerprint"):
            reset_derived_state_for_new_dataset(fp)
            if selected_sheet and selected_sheet != st.session_state.get("active_sheet"):
                st.session_state.audit_logger.log(
                    "WORKSHEET_SELECTED", f"Selected worksheet '{selected_sheet}' from '{uploaded_file.name}'",
                    details={"sheet": selected_sheet, "fingerprint": fp}
                )
                
        st.session_state["raw_df"] = raw_df
        st.session_state["clean_df"] = clean_df
        st.session_state["dataset_name"] = uploaded_file.name
        st.session_state["uploaded_file_name"] = uploaded_file.name
        st.session_state["uploaded_file_bytes"] = file_bytes
        st.session_state["active_sheet"] = selected_sheet or "CSV_Default"
        st.session_state["data_profile"] = profile
        st.session_state["structural_qa_report"] = run_structural_qa(clean_df)
        st.session_state["qa_report"] = st.session_state["structural_qa_report"]
        st.session_state["suggested_mappings"] = suggest_mappings(clean_df)
        
        st.session_state.audit_logger.log(
            "FILE_UPLOADED", f"Uploaded {uploaded_file.name} (Sheet: {selected_sheet})",
            filename=uploaded_file.name, row_count=len(raw_df), col_count=len(raw_df.columns),
            details={"fingerprint": fp, "sheet": selected_sheet}
        )
        st.session_state.audit_logger.log(
            "STRUCTURAL_QA_COMPLETED", "Executed Stage A Structural QA",
            details={"health_score": st.session_state["qa_report"]["health_score"]}
        )
        st.success(f"Successfully loaded `{uploaded_file.name}` (Sheet: `{st.session_state['active_sheet']}`, {len(raw_df):,} rows, {len(raw_df.columns)} cols). Stage A Structural QA completed.")
    except Exception as e:
        st.error(f"Error ingesting file: {e}")

# Mandatory Row Granularity Section
if st.session_state.get("raw_df") is not None:
    st.markdown("---")
    st.subheader("🔍 Step 1: Confirm Row Granularity")
    st.markdown(
        "> ⚠️ **IMPORTANT:** Confirm row granularity before interpreting rates, totals, or lifecycle metrics."
    )
    
    granularity_options = [
        "Case / record",
        "Customer / applicant",
        "Transaction / event",
        "Agent-day summary",
        "Periodic snapshot",
        "Other"
    ]
    
    current_gran = st.session_state.get("row_granularity", "Case / record")
    default_idx = granularity_options.index(current_gran) if current_gran in granularity_options else 0
    
    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        selected_gran = st.selectbox(
            "What does one row represent in this dataset?",
            granularity_options,
            index=default_idx,
            help="Defines how counts, sums, and lifecycle rates should be aggregated."
        )
        if selected_gran == "Other":
            custom_gran = st.text_input("Specify custom row representation:", value=st.session_state.get("row_granularity_custom", ""))
            if custom_gran:
                selected_gran = custom_gran
                
    with col_g2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("✅ Confirm Row Granularity", type="primary", use_container_width=True):
            st.session_state["row_granularity"] = selected_gran
            st.session_state["row_granularity_confirmed"] = True
            st.session_state.audit_logger.log("ROW_GRANULARITY_CONFIRMED", f"Confirmed granularity: {selected_gran}", details={"granularity": selected_gran})
            st.success(f"Confirmed: 1 Row = {selected_gran}")
            st.rerun()

    if st.session_state.get("row_granularity_confirmed", False):
        st.success(f"🎯 **Confirmed Unit of Analysis:** 1 Row = `{st.session_state['row_granularity']}`")
    else:
        st.warning("Granularity not yet confirmed. Click 'Confirm Row Granularity' above.")

    # Assessment Context Section
    st.markdown("---")
    st.subheader("🎯 Step 2: Assessment & Brief Context")
    st.caption("Standardise context metadata across all analytical pages and generated export decks.")
    
    ctx_c1, ctx_c2 = st.columns(2)
    with ctx_c1:
        st.session_state["assessment_question"] = st.text_input(
            "Assessment Question / Business Objective:",
            value=st.session_state.get("assessment_question", ""),
            placeholder="e.g. Identify primary drivers of backlog accumulation and assess team throughput variance."
        )
        st.session_state["target_audience"] = st.selectbox(
            "Primary Target Audience:",
            ["Senior Leadership", "Operational Management", "Analyst / Technical", "General Briefing"],
            index=["Senior Leadership", "Operational Management", "Analyst / Technical", "General Briefing"].index(st.session_state.get("target_audience", "Senior Leadership"))
        )
    with ctx_c2:
        st.session_state["output_format"] = st.selectbox(
            "Target Deliverable:",
            ["Presentation Deck (PPTX)", "Executive PDF Briefing", "Analytical Excel Pack", "Full Multi-Format Suite"],
            index=["Presentation Deck (PPTX)", "Executive PDF Briefing", "Analytical Excel Pack", "Full Multi-Format Suite"].index(st.session_state.get("output_format", "Presentation Deck (PPTX)"))
        )
        st.session_state["time_available"] = st.text_input(
            "Time Available for Presentation / Briefing:",
            value=st.session_state.get("time_available", "15 minutes")
        )
        
    st.session_state["analyst_notes"] = st.text_area(
        "Analyst Context & Scope Notes (Optional):",
        value=st.session_state.get("analyst_notes", ""),
        placeholder="e.g. Analysis covers Jan-Dec 2025 across 5 regional operational teams."
    )

    # Data Profile Summary
    st.markdown("---")
    st.subheader("📊 Dataset Health & Profile Overview")
    profile = st.session_state.get("data_profile", {})
    qa = st.session_state.get("structural_qa_report", {})
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Rows", f"{profile.get('row_count', 0):,}")
    c2.metric("Total Columns", profile.get('col_count', 0))
    c3.metric("Structural Health Score", f"{qa.get('health_score', 100):.1f} / 100")
    c4.metric("Completeness %", f"{profile.get('completeness_pct', 0):.1f}%")
    
    st.markdown(f"#### Sample Preview (First 5 Rows - Worksheet: `{st.session_state['active_sheet']}`)")
    st.dataframe(st.session_state["clean_df"].head(5), use_container_width=True)
else:
    st.info("Please upload a file or load one of the benchmark datasets above to begin.")

