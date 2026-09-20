"""Page 01: Data Ingestion & Profiling.
Supports CSV, Excel (multi-sheet), Parquet, JSON, chunked processing, encoding detection,
granularity confirmation, memory estimation, and transformation audit logging.
"""
import streamlit as st
import pandas as pd
from core.constants import WorkflowStage
from core.state import (
    init_session_state, advance_workflow_stage, log_audit_event, invalidate_derived_state, clear_dataset_state
)
from modules.ingestion.parser import read_file_contents, apply_column_transformation
from modules.profiling.profiler import profile_dataset
from modules.mapping.mapper import suggest_semantic_mappings
from modules.quality.engine import evaluate_data_quality_10d

init_session_state()

st.title("📁 Stage 2: Data Ingestion & Profiling")
st.markdown("Upload, inspect, and profile your operational performance datasets.")

# Ingestion Controls
with st.container():
    c_up1, c_up2 = st.columns([3, 1])
    with c_up1:
        uploaded_file = st.file_uploader(
            "Upload Operational Dataset",
            type=["csv", "xlsx", "xls", "parquet", "json"],
            help="Supports CSV, Excel, Parquet, and JSON datasets."
        )
    with c_up2:
        enc_choice = st.selectbox("Encoding Override", ["Auto-detect", "utf-8", "latin1", "cp1252", "iso-8859-1"])
        delim_choice = st.selectbox("Delimiter Override", ["Auto-detect", ",", ";", "\t", "|"])
        chunk_choice = st.selectbox("Processing Mode", ["In-Memory (Standard)", "Chunked (50k rows)", "Chunked (10k rows)"])

if uploaded_file is not None:
    chunk_sz = 50000 if "50k" in chunk_choice else (10000 if "10k" in chunk_choice else None)
    enc = None if enc_choice == "Auto-detect" else enc_choice
    delim = None if delim_choice == "Auto-detect" else delim_choice

    file_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name

    # Check if this is a newly uploaded file
    if st.session_state.get("uploaded_file_name") != filename:
        clear_dataset_state()
        df, sheets, meta = read_file_contents(
            file_bytes, filename, delimiter=delim, encoding=enc, chunk_size=chunk_sz
        )
        if df is not None:
            st.session_state.raw_df = df
            st.session_state.clean_df = df.copy()
            st.session_state.dataset_name = filename
            st.session_state.uploaded_file_name = filename
            st.session_state.available_sheets = sheets
            st.session_state.active_sheet = sheets[0] if sheets else "Default"
            st.session_state.metadata = meta
            st.session_state.data_profile = profile_dataset(df, filename)
            st.session_state.suggested_mappings = suggest_semantic_mappings(df)
            st.session_state.confirmed_mappings = {c: info["suggested_role"] for c, info in st.session_state.suggested_mappings.items() if info.get("confidence", 0) >= 0.50}
            st.session_state.qa_report = evaluate_data_quality_10d(df)
            
            # Auto-infer granularity
            inferred_gran = st.session_state.data_profile.get("inferred_granularity", "Not Confirmed")
            st.session_state.row_granularity = inferred_gran
            st.session_state.row_granularity_confirmed = False

            advance_workflow_stage(WorkflowStage.STAGE_02_INGEST)
            log_audit_event("DATASET_INGESTED", f"Uploaded {filename} with {len(df):,} rows and {len(df.columns)} columns.")
            st.success(f"Successfully loaded `{filename}` ({meta.get('file_size_mb', 0):.2f} MB)")
            st.rerun()

if st.session_state.get("clean_df") is not None:
    df = st.session_state["clean_df"]
    prof = st.session_state.get("data_profile", profile_dataset(df))

    # Multi-sheet selector for Excel
    sheets = st.session_state.get("available_sheets", [])
    if len(sheets) > 1:
        st.markdown("---")
        cur_sheet = st.session_state.get("active_sheet", sheets[0])
        s_idx = sheets.index(cur_sheet) if cur_sheet in sheets else 0
        new_sheet = st.selectbox("📑 Select Active Excel Worksheet", sheets, index=s_idx)
        if new_sheet != cur_sheet:
            st.session_state.active_sheet = new_sheet
            # Reload sheet
            # Update clean_df
            st.info(f"Switched active worksheet to `{new_sheet}`")

    # High-level Dataset Metrics
    st.markdown("---")
    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1:
        st.metric("Total Rows", f"{prof.get('row_count', len(df)):,}")
    with c_m2:
        st.metric("Total Columns", f"{prof.get('col_count', len(df.columns)):,}")
    with c_m3:
        st.metric("Memory Footprint", f"{prof.get('memory_mb', 0.0):.2f} MB")
    with c_m4:
        st.metric("Inferred Granularity", prof.get("inferred_granularity", "Standard Records")[:25] + "...")

    # Stage 3: Granularity Confirmation Gate
    st.markdown("---")
    st.header("🎯 Stage 3: Confirm Row Granularity")
    st.markdown("""
    **Crucial Integrity Gate:** Before calculating rates, sums, or productivity ratios, confirm what **one single row** represents in this dataset.
    """)

    granularity_options = [
        "Event / Transaction Log (1 row = 1 distinct case or event)",
        "Periodic Snapshot (1 row = 1 entity per reporting month/period)",
        "Aggregated Operational Summary (1 row = 1 team/service per period)",
        "Master Entity Record (1 row = 1 individual profile/staff/patient)",
        "Other / Custom Unit of Analysis"
    ]
    cur_gran = st.session_state.get("row_granularity", granularity_options[1])
    g_idx = granularity_options.index(cur_gran) if cur_gran in granularity_options else 1

    selected_gran = st.selectbox("Confirm Unit of Analysis (What 1 row represents)", granularity_options, index=g_idx)
    st.session_state.row_granularity = selected_gran

    if st.button("✅ Confirm Granularity & Lock Baseline", type="primary"):
        st.session_state.row_granularity_confirmed = True
        advance_workflow_stage(WorkflowStage.STAGE_03_GRANULARITY)
        log_audit_event("GRANULARITY_CONFIRMED", f"Confirmed unit of analysis: {selected_gran}")
        st.success(f"Granularity locked: `{selected_gran}`. Proceed to **02_Data_Quality**.")

    # Column-Level Schema Profile Table
    st.markdown("---")
    st.subheader("🔍 Column-Level Schema & Distribution Profile")
    
    cols_data = []
    for col, c_info in prof.get("columns", {}).items():
        cols_data.append({
            "Column Name": col,
            "Inferred Type": c_info.get("inferred_type", "string"),
            "Non-Null Count": f"{c_info.get('non_null_count', 0):,}",
            "Missing %": f"{c_info.get('null_pct', 0.0):.1f}%",
            "Unique Values": f"{c_info.get('unique_count', 0):,}",
            "Sample Values": ", ".join(c_info.get("sample_values", [])[:3])
        })
    st.dataframe(pd.DataFrame(cols_data), use_container_width=True)

    # Interactive Column Transformation Workspace
    with st.expander("🛠️ Column Transformations & Data Cleansing Workspace", expanded=False):
        st.caption("Apply explicit column casts, renames, or filters. Every action is recorded in the transformation log.")
        t_type = st.selectbox("Transformation Action", ["Rename Column", "Cast Data Type", "Drop Column", "Filter Allowed Values"])
        
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            target_col = st.selectbox("Target Column", df.columns)
        with c_t2:
            if t_type == "Rename Column":
                new_col_name = st.text_input("New Column Name", value=target_col)
                if st.button("Apply Rename"):
                    new_df, audit = apply_column_transformation(df, "rename_column", {"old_name": target_col, "new_name": new_col_name})
                    st.session_state.clean_df = new_df
                    st.session_state.transformation_log.append(audit)
                    invalidate_derived_state()
                    st.success(f"Renamed '{target_col}' -> '{new_col_name}'")
                    st.rerun()

            elif t_type == "Cast Data Type":
                new_type = st.selectbox("Target Type", ["numeric", "datetime", "string", "category"])
                if st.button("Apply Type Cast"):
                    new_df, audit = apply_column_transformation(df, "cast_type", {"column": target_col, "target_type": new_type})
                    st.session_state.clean_df = new_df
                    st.session_state.transformation_log.append(audit)
                    invalidate_derived_state()
                    st.success(f"Casted '{target_col}' to {new_type}")
                    st.rerun()

            elif t_type == "Drop Column":
                if st.button("Drop Column", type="secondary"):
                    new_df, audit = apply_column_transformation(df, "drop_column", {"column": target_col})
                    st.session_state.clean_df = new_df
                    st.session_state.transformation_log.append(audit)
                    invalidate_derived_state()
                    st.warning(f"Dropped '{target_col}'")
                    st.rerun()

    # Transformation Audit Trail
    t_log = st.session_state.get("transformation_log", [])
    if t_log:
        st.caption(f"Transformation History ({len(t_log)} modifications recorded):")
        st.dataframe(pd.DataFrame(t_log), use_container_width=True)
else:
    st.info("Upload a file or choose a demo dataset from the sidebar to begin.")
