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
st.markdown("Upload any operational dataset (`.csv`, `.xlsx`, `.xls`), inspect structural hygiene, and confirm **Row Granularity**.")

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

st.markdown("#### 🧪 Benchmark & Assessment Test Datasets")
col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)

def _load_sample(path, name, default_gran):
    try:
        df = pd.read_csv(path)
        fp = compute_dataset_fingerprint(df, os.path.basename(path))
        if fp != st.session_state.get("dataset_fingerprint"):
            reset_derived_state_for_new_dataset(fp)
        st.session_state["raw_df"] = df.copy()
        st.session_state["clean_df"] = df.copy()
        st.session_state["dataset_name"] = name
        st.session_state["active_sheet"] = "CSV_Default"
        st.session_state["data_profile"] = generate_dataset_profile(df)
        st.session_state["structural_qa_report"] = run_structural_qa(df)
        st.session_state["qa_report"] = st.session_state["structural_qa_report"]
        st.session_state["suggested_mappings"] = suggest_mappings(df)
        st.session_state["row_granularity"] = default_gran
        st.session_state["row_granularity_confirmed"] = True
        st.session_state.audit_logger.log(
            "FILE_UPLOADED", f"Loaded {name}", filename=os.path.basename(path),
            row_count=len(df), col_count=len(df.columns), details={"fingerprint": fp}
        )
        st.session_state.audit_logger.log("STRUCTURAL_QA_COMPLETED", "Executed Stage A Structural QA", details={"health_score": st.session_state["qa_report"]["health_score"]})
        st.success(f"Loaded {name} successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error loading {name}: {e}")

with col_s1:
    if st.button("📞 Customer Service", use_container_width=True):
        _load_sample("sample_data/customer_service_dataset.csv", "Customer Service Operations", "Periodic snapshot")

with col_s2:
    if st.button("🔍 Inspections", use_container_width=True):
        _load_sample("sample_data/inspection_dataset.csv", "Building & Safety Inspections", "Periodic snapshot")

with col_s3:
    if st.button("📋 Case Level", use_container_width=True):
        _load_sample("sample_data/case_level_dataset.csv", "Granular Case Records", "Case / record")

with col_s4:
    if st.button("📜 Permits & Licensing", use_container_width=True):
        _load_sample("sample_data/unfamiliar_operational_dataset.csv", "Licensing & Permits", "Periodic snapshot")

with col_s5:
    if st.button("⚠️ Poor Quality", use_container_width=True):
        _load_sample("sample_data/poor_quality_dataset.csv", "Dirty Anomaly Dataset", "Periodic snapshot")

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
                st.info(f"Workbook contains {len(sheets)} worksheets.")
                selected_sheet = st.selectbox("Select Active Worksheet to Analyze", sheets)
            else:
                selected_sheet = sheets[0] if sheets else None

        df_uploaded, clean_uploaded, profile = ingest_file(file_bytes, uploaded_file.name, sheet_name=selected_sheet)
        fp = compute_dataset_fingerprint(df_uploaded, uploaded_file.name)
        
        if fp != st.session_state.get("dataset_fingerprint"):
            reset_derived_state_for_new_dataset(fp)
            
        st.session_state["raw_df"] = df_uploaded.copy()
        st.session_state["clean_df"] = clean_uploaded.copy()
        st.session_state["dataset_name"] = uploaded_file.name
        st.session_state["active_sheet"] = selected_sheet or profile.get("active_sheet", "Default")
        st.session_state["data_profile"] = profile
        st.session_state["structural_qa_report"] = run_structural_qa(df_uploaded)
        st.session_state["qa_report"] = st.session_state["structural_qa_report"]
        st.session_state["suggested_mappings"] = suggest_mappings(clean_uploaded)
        
        st.session_state.audit_logger.log(
            "FILE_UPLOADED", "User uploaded data file", filename=uploaded_file.name,
            row_count=len(df_uploaded), col_count=len(df_uploaded.columns), details={"fingerprint": fp}
        )
        st.session_state.audit_logger.log("STRUCTURAL_QA_COMPLETED", "Executed Stage A Structural QA", details={"health_score": st.session_state["qa_report"]["health_score"]})
        st.success(f"Successfully ingested `{uploaded_file.name}` ({len(df_uploaded):,} rows, {len(df_uploaded.columns)} columns)")
    except Exception as e:
        st.error(f"Ingestion failed: {e}")

# Row Granularity / Unit of Analysis Confirmation
if st.session_state.get("raw_df") is not None:
    st.markdown("---")
    st.subheader("🔍 Step 2: Confirm Unit of Analysis / Row Granularity")
    st.markdown("""
    **Mandatory Analytical Step:** Explicitly state what each row in this dataset represents. 
    This prevents misinterpreting row counts as workload, prevents inappropriate summing of rates, and anchors all subsequent analysis.
    """)
    
    gran_options = [
        "Select / Specify...",
        "Case / record (1 row = 1 individual case or application)",
        "Periodic snapshot (1 row = 1 team/region aggregated for 1 month/quarter/week)",
        "Transaction / event (1 row = 1 individual activity, inspection, or status change)",
        "Staff member / resource (1 row = 1 individual caseworker or team)",
        "Custom specification"
    ]
    
    current_gran = st.session_state.get("row_granularity", "Select / Specify...")
    c_idx = 0
    for i, opt in enumerate(gran_options):
        if current_gran and current_gran.lower() in opt.lower():
            c_idx = i
            break
            
    sel_gran = st.selectbox("What does 1 row represent in this dataset?", gran_options, index=c_idx)
    custom_gran = ""
    if sel_gran == "Custom specification":
        custom_gran = st.text_input("Specify custom row granularity:", value=st.session_state.get("custom_granularity", ""))
        
    c_g1, c_g2 = st.columns([1, 3])
    with c_g1:
        if st.button("✅ Confirm Row Granularity", type="primary", use_container_width=True):
            final_gran = custom_gran.strip() if sel_gran == "Custom specification" else sel_gran.split("(")[0].strip()
            if final_gran and final_gran != "Select / Specify...":
                st.session_state["row_granularity"] = final_gran
                st.session_state["row_granularity_confirmed"] = True
                st.session_state.audit_logger.log("ROW_GRANULARITY_CONFIRMED", "Confirmed unit of analysis", details={"granularity": final_gran})
                st.success(f"Unit of analysis confirmed: `{final_gran}`")
                st.rerun()
            else:
                st.error("Please select or specify a valid row granularity.")
                
    if st.session_state.get("row_granularity_confirmed", False):
        st.info(f"📌 **Current Confirmed Unit of Analysis:** 1 Row = `{st.session_state.get('row_granularity')}`")
        
    # Dataset Preview & Profile Summary
    st.markdown("---")
    st.subheader("📊 Dataset Overview & Preview")
    df = st.session_state["raw_df"]
    st.dataframe(df.head(10), use_container_width=True)
    
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    p_col1.metric("Total Rows", f"{len(df):,}")
    p_col2.metric("Total Columns", f"{len(df.columns):,}")
    null_cells = int(df.isnull().sum().sum())
    p_col3.metric("Missing Values", f"{null_cells:,}")
    dup_rows = int(df.duplicated().sum())
    p_col4.metric("Duplicate Rows", f"{dup_rows:,}")
