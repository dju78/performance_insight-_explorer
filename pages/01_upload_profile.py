import streamlit as st
import pandas as pd
from src.state import init_session_state
from src.ingestion import ingest_file, generate_dataset_profile

init_session_state()

st.title("📂 01. Data Upload & Profiling")
st.markdown("Upload any operational dataset (`.csv`, `.xlsx`, `.xls`) or load sample benchmarking data.")

uploaded_file = st.file_uploader("Upload Operational Data File", type=["csv", "xlsx", "xls"])

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    if st.button("Load Sample: Standard Operations (Dataset A)", use_container_width=True):
        try:
            df = pd.read_csv("sample_data/dataset_a_team_month.csv")
            st.session_state["raw_df"] = df.copy()
            st.session_state["clean_df"] = df.copy()
            st.session_state["dataset_name"] = "Dataset A (Team-Month Benchmark)"
            st.session_state["data_profile"] = generate_dataset_profile(df)
            st.session_state["row_granularity"] = "Periodic snapshot"
            st.session_state["row_granularity_confirmed"] = True
            st.session_state.audit_logger.log("LOAD_SAMPLE_DATASET", "Loaded Dataset A", details={"name": "Dataset A"})
            st.success("Loaded Dataset A successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading sample: {e}")

with col_s2:
    if st.button("Load Sample: Case-Level Details (Dataset B)", use_container_width=True):
        try:
            df = pd.read_csv("sample_data/dataset_b_case_level.csv")
            st.session_state["raw_df"] = df.copy()
            st.session_state["clean_df"] = df.copy()
            st.session_state["dataset_name"] = "Dataset B (Case Level Details)"
            st.session_state["data_profile"] = generate_dataset_profile(df)
            st.session_state["row_granularity"] = "Case / record"
            st.session_state["row_granularity_confirmed"] = True
            st.session_state.audit_logger.log("LOAD_SAMPLE_DATASET", "Loaded Dataset B", details={"name": "Dataset B"})
            st.success("Loaded Dataset B successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading sample: {e}")

with col_s3:
    if st.button("Load Sample: Poor Quality Anomaly (Dataset C)", use_container_width=True):
        try:
            df = pd.read_csv("sample_data/dataset_c_poor_quality.csv")
            st.session_state["raw_df"] = df.copy()
            st.session_state["clean_df"] = df.copy()
            st.session_state["dataset_name"] = "Dataset C (Poor Quality Anomaly)"
            st.session_state["data_profile"] = generate_dataset_profile(df)
            st.session_state["row_granularity"] = "Transaction / event"
            st.session_state["row_granularity_confirmed"] = True
            st.session_state.audit_logger.log("LOAD_SAMPLE_DATASET", "Loaded Dataset C", details={"name": "Dataset C"})
            st.success("Loaded Dataset C successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading sample: {e}")

if uploaded_file is not None:
    try:
        raw_df, clean_df, profile = ingest_file(uploaded_file, uploaded_file.name)
        st.session_state["raw_df"] = raw_df
        st.session_state["clean_df"] = clean_df
        st.session_state["dataset_name"] = uploaded_file.name
        st.session_state["data_profile"] = profile
        st.session_state.audit_logger.log("FILE_UPLOADED", f"Uploaded {uploaded_file.name}", filename=uploaded_file.name, row_count=len(raw_df), col_count=len(raw_df.columns))
        st.success(f"Successfully uploaded and profiled `{uploaded_file.name}` ({len(raw_df):,} rows, {len(raw_df.columns)} columns)")
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
            st.session_state.audit_logger.log("CONFIRM_ROW_GRANULARITY", f"Confirmed granularity: {selected_gran}", details={"granularity": selected_gran})
            st.success(f"Confirmed: 1 Row = {selected_gran}")
            st.rerun()

    if st.session_state.get("row_granularity_confirmed", False):
        st.success(f"🎯 **Confirmed Unit of Analysis:** 1 Row = `{st.session_state['row_granularity']}`")
    else:
        st.warning("Granularity not yet explicitly confirmed. Click 'Confirm Row Granularity' above.")

    # Data Profile Summary
    st.markdown("---")
    st.subheader("📊 Dataset Health & Profile Overview")
    profile = st.session_state.get("data_profile", {})
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Rows", f"{profile.get('row_count', 0):,}")
    c2.metric("Total Columns", profile.get("col_count", 0))
    c3.metric("Duplicate Rows", f"{profile.get('duplicate_rows', 0):,}")
    c4.metric("Complete Rows %", f"{profile.get('completeness_pct', 0):.1f}%")
    
    st.markdown("#### Sample Preview (First 5 Rows)")
    st.dataframe(st.session_state["clean_df"].head(5), use_container_width=True)
    
    with st.expander("Detailed Column Schema & Types"):
        col_summary = []
        for col, meta in profile.get("columns", {}).items():
            col_summary.append({
                "Column Name": col,
                "Inferred Type": meta.get("inferred_type"),
                "Null Count": meta.get("null_count"),
                "Null Pct": f"{meta.get('null_pct', 0):.1f}%",
                "Unique Values": meta.get("unique_count"),
                "Sample Values": ", ".join(map(str, meta.get("sample_values", [])[:3]))
            })
        st.dataframe(pd.DataFrame(col_summary), use_container_width=True)
else:
    st.info("Please upload a file or load one of the sample benchmark datasets above to begin.")
