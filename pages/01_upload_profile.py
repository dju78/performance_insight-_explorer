import io
import os
import streamlit as st
import pandas as pd
from src.state import (
    init_session_state,
    compute_dataset_fingerprint,
    reset_derived_state_for_new_dataset,
    clear_dataset_for_new_upload,
    register_dataset,
    remove_dataset,
    set_primary_dataset,
    get_primary_dataset,
    get_reference_datasets,
    sync_analytical_model
)
from src.ingestion import ingest_file, generate_dataset_profile, get_excel_sheet_names, load_file
from src.brief_extractor import extract_assessment_brief
from src.relationships import validate_relationship, build_joined_analytical_model
from src.quality import run_structural_qa
from src.mapping import suggest_mappings

init_session_state()

st.title("📂 01. Assessment Brief & Multi-Dataset Hub")
st.markdown("""
Ingest your **Assessment Brief** (`.docx`, `.pdf`, `.txt`) and **Operational Datasets** (`.xlsx`, `.xls`, `.csv`).
Configure dataset roles, inspect structural profiles, map relationships (e.g. `Performance -> Users`), and confirm **Row Granularity**.
""")

# Top Action Controls
col_top_left, col_top_right = st.columns([2, 1])
with col_top_right:
    if st.session_state.get("raw_df") is not None or st.session_state.get("datasets"):
        if st.button("🗑️ Clear All & Start Fresh", type="secondary", use_container_width=True):
            clear_dataset_for_new_upload(preserve_assessment_context=False)
            st.success("All datasets and context cleared.")
            st.rerun()

st.markdown("---")

# ==============================================================================
# SECTION 1: ASSESSMENT BRIEF / INSTRUCTIONS INTAKE
# ==============================================================================
st.subheader("📋 Step 1: Assessment Brief & Instructions")
st.caption("Upload your assessment brief file (`.docx`, `.pdf`, `.txt`) or paste requirements. This file is treated as the business specification and is never profiled as tabular data.")

brief_col1, brief_col2 = st.columns([1, 1])

with brief_col1:
    brief_file = st.file_uploader(
        "Upload Assessment Brief File",
        type=["docx", "doc", "pdf", "txt", "md"],
        key="brief_file_uploader",
        help="Upload Question1.docx, PDF specification, or text brief."
    )
    if brief_file is not None:
        try:
            brief_bytes = brief_file.getvalue()
            brief_res = extract_assessment_brief(brief_bytes, brief_file.name)
            st.session_state.assessment_brief_data = {
                "filename": brief_file.name,
                "raw_text": brief_res.get("raw_text", ""),
                "questions": brief_res.get("questions", []),
                "question_count": brief_res.get("question_count", 0),
                "is_loaded": True
            }
            if brief_res.get("questions"):
                st.session_state["questions_must_answer"] = "\n".join(brief_res["questions"])
            if not st.session_state.get("assessment_question") and brief_res.get("raw_text"):
                st.session_state["assessment_question"] = brief_res["raw_text"][:300] + "..."
            st.success(f"Extracted {brief_res.get('question_count', 0)} questions from `{brief_file.name}`")
        except Exception as e:
            st.error(f"Failed to extract brief: {e}")

with brief_col2:
    brief_data = st.session_state.get("assessment_brief_data", {})
    if brief_data.get("is_loaded"):
        st.markdown(f"**📄 Active Brief:** `{brief_data.get('filename')}` ({brief_data.get('question_count', 0)} questions detected)")
        with st.expander("👁️ View Extracted Assessment Questions", expanded=True):
            for i, q in enumerate(brief_data.get("questions", []), 1):
                st.markdown(f"- **Q{i}:** {q}")
    else:
        st.info("💡 No brief file uploaded yet. You can upload `Question1.docx` or paste questions directly.")

st.markdown("---")

# ==============================================================================
# SECTION 2: MULTI-DATASET UPLOAD & ROLE ASSIGNMENT
# ==============================================================================
st.subheader("📊 Step 2: Ingest Operational & Reference Datasets")
st.markdown("Upload your tabular workbooks. You can assign explicit analytical roles to each file (e.g. Primary Dataset, Reference / Master Data).")

upload_ver = st.session_state.get("upload_widget_version", 0)
uploaded_files = st.file_uploader(
    "Upload Dataset(s) (XLSX, XLS, CSV)",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True,
    key=f"multi_uploader_{upload_ver}"
)

# Process any newly uploaded files
if uploaded_files:
    for ufile in uploaded_files:
        file_id = ufile.name
        if file_id not in st.session_state.datasets:
            f_bytes = ufile.getvalue()
            ext = os.path.splitext(ufile.name)[1].lower()
            sheets = ["Default"]
            active_sheet = "Default"
            if ext in [".xlsx", ".xls", ".xlsm"]:
                try:
                    sheets = get_excel_sheet_names(f_bytes)
                    # Auto-select sheet if standard
                    if "Performance Data" in sheets:
                        active_sheet = "Performance Data"
                    elif "Users" in sheets:
                        active_sheet = "Users"
                    else:
                        active_sheet = sheets[0] if sheets else "Default"
                except Exception:
                    sheets = ["Sheet1"]
                    active_sheet = "Sheet1"

            # Auto-infer default role
            fname_lower = ufile.name.lower()
            if "user" in fname_lower or "master" in fname_lower or "lookup" in fname_lower or "ref" in fname_lower:
                role = "Reference / Master Data"
            elif "target" in fname_lower or "bench" in fname_lower:
                role = "Targets / Benchmark Data"
            elif len(st.session_state.datasets) == 0 or "perf" in fname_lower:
                role = "Primary Analysis Dataset"
            else:
                role = "Secondary Operational Dataset"

            try:
                raw_df, sheets_loaded, meta = load_file(f_bytes, ufile.name, sheet_name=active_sheet)
                prof = generate_dataset_profile(raw_df)
                register_dataset(
                    dataset_id=file_id,
                    name=ufile.name,
                    role=role,
                    raw_df=raw_df,
                    clean_df=raw_df.copy(deep=True),
                    sheets=sheets_loaded or sheets,
                    active_sheet=active_sheet,
                    file_bytes=f_bytes,
                    profile=prof,
                    metadata=meta,
                    key_field="User" if "User" in raw_df.columns else "",
                    granularity="Periodic Snapshot" if role == "Primary Analysis Dataset" else ""
                )
                st.session_state.audit_logger.log(
                    "DATASET_REGISTERED", f"Registered dataset {ufile.name}",
                    filename=ufile.name, role=role, rows=len(raw_df), cols=len(raw_df.columns)
                )
            except Exception as e:
                st.error(f"Error reading `{ufile.name}`: {e}")

# Quick-load assessment files if present in workspace
st.markdown("#### 🚀 Quick-Load Practical Assessment Files")
q_c1, q_c2, q_c3 = st.columns(3)

with q_c1:
    if st.button("📁 Load Assessment Pair (performance.xlsx + Users.xlsx)", use_container_width=True, type="primary"):
        try:
            # 1. Performance
            if os.path.exists("performance.xlsx"):
                with open("performance.xlsx", "rb") as f:
                    p_bytes = f.read()
                raw_p, sheets_p, meta_p = load_file(p_bytes, "performance.xlsx", sheet_name="Performance Data")
                prof_p = generate_dataset_profile(raw_p)
                register_dataset(
                    dataset_id="performance.xlsx",
                    name="performance.xlsx",
                    role="Primary Analysis Dataset",
                    raw_df=raw_p,
                    clean_df=raw_p.copy(deep=True),
                    sheets=sheets_p,
                    active_sheet="Performance Data",
                    file_bytes=p_bytes,
                    profile=prof_p,
                    metadata=meta_p,
                    key_field="User",
                    granularity="Periodic Snapshot (1 row = 1 User for 1 Reporting Month)"
                )
            # 2. Users
            if os.path.exists("Users.xlsx"):
                with open("Users.xlsx", "rb") as f:
                    u_bytes = f.read()
                raw_u, sheets_u, meta_u = load_file(u_bytes, "Users.xlsx", sheet_name="Users")
                prof_u = generate_dataset_profile(raw_u)
                register_dataset(
                    dataset_id="Users.xlsx",
                    name="Users.xlsx",
                    role="Reference / Master Data",
                    raw_df=raw_u,
                    clean_df=raw_u.copy(deep=True),
                    sheets=sheets_u,
                    active_sheet="Users",
                    file_bytes=u_bytes,
                    profile=prof_u,
                    metadata=meta_u,
                    key_field="User",
                    granularity="Staff Master Record (1 row = 1 User)"
                )
            # 3. Brief
            if os.path.exists("Question1.docx"):
                with open("Question1.docx", "rb") as f:
                    b_bytes = f.read()
                b_res = extract_assessment_brief(b_bytes, "Question1.docx")
                st.session_state.assessment_brief_data = {
                    "filename": "Question1.docx",
                    "raw_text": b_res.get("raw_text", ""),
                    "questions": b_res.get("questions", []),
                    "question_count": b_res.get("question_count", 0),
                    "is_loaded": True
                }
                if b_res.get("questions"):
                    st.session_state["questions_must_answer"] = "\n".join(b_res["questions"])
            
            # Setup default relationship
            st.session_state.relationships = [{
                "left_dataset_id": "performance.xlsx",
                "left_key": "User",
                "right_dataset_id": "Users.xlsx",
                "right_key": "User",
                "join_type": "left"
            }]
            sync_analytical_model()
            st.success("Loaded performance.xlsx, Users.xlsx, and Question1.docx with automatic User relationship!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to quick-load assessment pair: {e}")

with q_c2:
    if st.button("📞 Customer Service Sample", use_container_width=True):
        if os.path.exists("sample_data/customer_service_dataset.csv"):
            df = pd.read_csv("sample_data/customer_service_dataset.csv")
            register_dataset(
                dataset_id="customer_service_dataset.csv",
                name="customer_service_dataset.csv",
                role="Primary Analysis Dataset",
                raw_df=df,
                clean_df=df.copy(deep=True),
                granularity="Periodic Snapshot"
            )
            sync_analytical_model()
            st.success("Loaded Customer Service dataset!")
            st.rerun()

with q_c3:
    if st.button("🔍 Inspections Sample", use_container_width=True):
        if os.path.exists("sample_data/inspection_dataset.csv"):
            df = pd.read_csv("sample_data/inspection_dataset.csv")
            register_dataset(
                dataset_id="inspection_dataset.csv",
                name="inspection_dataset.csv",
                role="Primary Analysis Dataset",
                raw_df=df,
                clean_df=df.copy(deep=True),
                granularity="Periodic Snapshot"
            )
            sync_analytical_model()
            st.success("Loaded Inspections dataset!")
            st.rerun()

# Display Profile & Config Cards for All Registered Datasets
if st.session_state.datasets:
    st.markdown("---")
    st.markdown("### 📋 Active Datasets & Independent Profiles")
    
    ROLE_OPTIONS = [
        "Primary Analysis Dataset",
        "Reference / Master Data",
        "Secondary Operational Dataset",
        "Targets / Benchmark Data"
    ]

    for ds_id, ds_info in list(st.session_state.datasets.items()):
        df = ds_info.get("raw_df")
        if df is None:
            continue
            
        with st.container():
            d_header_col, d_badge_col = st.columns([3, 1])
            is_primary = "Primary" in ds_info.get("role", "")
            badge = "🔵 **PRIMARY DATASET**" if is_primary else f"🟢 **{ds_info.get('role', 'REFERENCE')}**"
            
            with d_header_col:
                st.markdown(f"#### 📄 `{ds_info.get('name')}`")
            with d_badge_col:
                st.markdown(badge)

            c_ctrl1, c_ctrl2, c_ctrl3, c_ctrl4 = st.columns([2, 2, 2, 1])
            
            with c_ctrl1:
                curr_role = ds_info.get("role", "Primary Analysis Dataset")
                r_idx = ROLE_OPTIONS.index(curr_role) if curr_role in ROLE_OPTIONS else 0
                new_role = st.selectbox(
                    f"Dataset Role for {ds_info['name']}",
                    ROLE_OPTIONS,
                    index=r_idx,
                    key=f"role_sel_{ds_id}"
                )
                if new_role != curr_role:
                    ds_info["role"] = new_role
                    if "primary" in new_role.lower():
                        set_primary_dataset(ds_id)
                    sync_analytical_model()
                    st.rerun()

            with c_ctrl2:
                sheets = ds_info.get("sheets", ["Default"])
                if len(sheets) > 1:
                    active_sh = ds_info.get("active_sheet", sheets[0])
                    s_idx = sheets.index(active_sh) if active_sh in sheets else 0
                    new_sheet = st.selectbox(
                        f"Active Sheet for {ds_info['name']}",
                        sheets,
                        index=s_idx,
                        key=f"sheet_sel_{ds_id}"
                    )
                    if new_sheet != active_sh and ds_info.get("file_bytes"):
                        raw_df_new, _, meta_new = load_file(ds_info["file_bytes"], ds_info["name"], sheet_name=new_sheet)
                        ds_info["active_sheet"] = new_sheet
                        ds_info["raw_df"] = raw_df_new
                        ds_info["clean_df"] = raw_df_new.copy(deep=True)
                        ds_info["profile"] = generate_dataset_profile(raw_df_new)
                        ds_info["metadata"] = meta_new
                        if is_primary:
                            set_primary_dataset(ds_id)
                        sync_analytical_model()
                        st.rerun()
                else:
                    st.text_input("Active Sheet", value=sheets[0] if sheets else "Default", disabled=True, key=f"sh_dis_{ds_id}")

            with c_ctrl3:
                cols = list(df.columns)
                curr_key = ds_info.get("key_field", "")
                k_idx = cols.index(curr_key) if curr_key in cols else (0 if cols else 0)
                sel_key = st.selectbox(
                    f"Key Field for {ds_info['name']}",
                    cols,
                    index=k_idx,
                    key=f"key_sel_{ds_id}"
                )
                ds_info["key_field"] = sel_key

            with c_ctrl4:
                st.write("")
                st.write("")
                if st.button("🗑️ Remove", key=f"del_ds_{ds_id}", use_container_width=True):
                    remove_dataset(ds_id)
                    sync_analytical_model()
                    st.rerun()

            # Profile Metrics Card
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Rows", f"{len(df):,}")
            m2.metric("Columns", f"{len(df.columns):,}")
            null_cells = int(df.isnull().sum().sum())
            m3.metric("Missing Cells", f"{null_cells:,}")
            dup_rows = int(df.duplicated().sum())
            m4.metric("Duplicate Rows", f"{dup_rows:,}")
            key_col = ds_info.get("key_field")
            unique_keys = int(df[key_col].nunique()) if key_col and key_col in df.columns else len(df)
            m5.metric(f"Unique '{key_col or 'Rows'}'", f"{unique_keys:,}")

            # Preview
            with st.expander(f"🔍 Preview Table: {ds_info['name']} (First 5 rows)", expanded=False):
                st.dataframe(df.head(5), use_container_width=True)

            st.markdown("---")

# ==============================================================================
# SECTION 3: ROW GRANULARITY CONFIRMATION (FOR PRIMARY DATASET)
# ==============================================================================
primary_ds = get_primary_dataset()
if primary_ds is not None and primary_ds.get("raw_df") is not None:
    st.subheader("🔍 Step 3: Confirm Unit of Analysis / Row Granularity")
    st.markdown("""
    **Mandatory Analytical Step:** Explicitly specify what 1 row represents in your primary analytical dataset.
    This prevents misinterpreting row counts, prevents inappropriate summing of rates, and anchors all subsequent calculations.
    """)

    gran_options = [
        "Select / Specify...",
        "Periodic snapshot (1 row = 1 User for 1 Reporting Month)",
        "Periodic snapshot (1 row = 1 team/region aggregated for 1 month/quarter/week)",
        "Case / record (1 row = 1 individual case or application)",
        "Transaction / event (1 row = 1 individual activity or inspection)",
        "Staff member / resource (1 row = 1 individual caseworker or team)",
        "Custom specification"
    ]

    current_gran = st.session_state.get("row_granularity", "Select / Specify...")
    c_idx = 0
    for i, opt in enumerate(gran_options):
        if current_gran and current_gran.split("(")[0].strip().lower() in opt.lower():
            c_idx = i
            break

    g_col1, g_col2 = st.columns([3, 1])
    with g_col1:
        sel_gran = st.selectbox("What does 1 row represent in this dataset?", gran_options, index=c_idx)
        custom_gran = ""
        if sel_gran == "Custom specification":
            custom_gran = st.text_input("Specify custom row granularity:", value=st.session_state.get("custom_granularity", ""))

    with g_col2:
        st.write("")
        st.write("")
        if st.button("✅ Confirm Granularity", type="primary", use_container_width=True):
            final_gran = custom_gran.strip() if sel_gran == "Custom specification" else sel_gran.split("(")[0].strip()
            if final_gran and final_gran != "Select / Specify...":
                st.session_state["row_granularity"] = final_gran
                st.session_state["row_granularity_confirmed"] = True
                primary_ds["granularity"] = final_gran
                primary_ds["granularity_confirmed"] = True
                st.session_state.audit_logger.log("ROW_GRANULARITY_CONFIRMED", "Confirmed unit of analysis", details={"granularity": final_gran})
                st.success(f"Unit of analysis confirmed: `{final_gran}`")
                st.rerun()
            else:
                st.error("Please select a valid granularity.")

    if st.session_state.get("row_granularity_confirmed", False):
        st.info(f"📌 **Current Confirmed Unit of Analysis:** 1 Row = `{st.session_state.get('row_granularity')}`")

    st.markdown("---")

# ==============================================================================
# SECTION 4: RELATIONSHIP MAPPING & JOIN ENGINE
# ==============================================================================
ref_datasets = get_reference_datasets()
if primary_ds is not None and ref_datasets:
    st.subheader("🔗 Step 4: Map Relationships & Build Analytical Model")
    st.markdown("""
    Define relationships between your **Primary Analysis Dataset** and **Reference / Master Datasets** (e.g. `Performance.User -> Users.User`).
    The system validates key coverage, detects duplicate reference keys, and builds a unified joined analytical model.
    """)

    prim_df = primary_ds["raw_df"]
    
    # Configure relationship for each reference dataset
    for ref_ds in ref_datasets:
        r_id = ref_ds["id"]
        ref_df = ref_ds["raw_df"]
        
        st.markdown(f"#### Relationship: `{primary_ds['name']}` ⟷ `{ref_ds['name']}`")
        
        # Find existing relationship config or defaults
        existing_rel = None
        for r in st.session_state.get("relationships", []):
            if r.get("right_dataset_id") == r_id:
                existing_rel = r
                break

        r_c1, r_c2, r_c3, r_c4 = st.columns(4)
        
        with r_c1:
            prim_cols = list(prim_df.columns)
            p_default_key = "User" if "User" in prim_cols else prim_cols[0]
            if existing_rel:
                p_default_key = existing_rel.get("left_key", p_default_key)
            left_key = st.selectbox(
                f"Primary Key ({primary_ds['name']})",
                prim_cols,
                index=prim_cols.index(p_default_key) if p_default_key in prim_cols else 0,
                key=f"rel_lkey_{r_id}"
            )

        with r_c2:
            ref_cols = list(ref_df.columns)
            r_default_key = "User" if "User" in ref_cols else ref_cols[0]
            if existing_rel:
                r_default_key = existing_rel.get("right_key", r_default_key)
            right_key = st.selectbox(
                f"Reference Key ({ref_ds['name']})",
                ref_cols,
                index=ref_cols.index(r_default_key) if r_default_key in ref_cols else 0,
                key=f"rel_rkey_{r_id}"
            )

        with r_c3:
            join_type = st.selectbox(
                "Join Type",
                ["left", "inner", "right", "outer"],
                index=0,
                key=f"rel_jtype_{r_id}",
                help="Left join preserves all primary operational records."
            )

        # Validate relationship
        validation = validate_relationship(
            left_df=prim_df,
            left_key=left_key,
            right_df=ref_df,
            right_key=right_key,
            left_name=primary_ds["name"],
            right_name=ref_ds["name"]
        )

        with r_c4:
            st.write("")
            st.write("")
            if validation["status"] == "OPTIMAL":
                st.success("✅ Perfect Match (100%)")
            elif validation["status"] == "GOOD":
                st.info(f"✅ Match: {validation['match_rate']:.1%}")
            elif validation["status"] == "WARNING":
                st.warning(f"⚠️ Match: {validation['match_rate']:.1%}")
            else:
                st.error("❌ Key Misaligned")

        # Validation Diagnostic Card
        v_col1, v_col2, v_col3, v_col4 = st.columns(4)
        v_col1.metric("Matched Primary Rows", f"{validation['matched_rows']:,} / {validation['left_total_rows']:,}")
        v_col2.metric("Join Coverage", f"{validation['match_rate']:.1%}")
        v_col3.metric("Unmatched Rows", f"{validation['unmatched_rows']:,}")
        v_col4.metric("Reference Duplicate Keys", f"{validation['right_duplicates']:,}")

        if validation.get("warnings"):
            for w in validation["warnings"]:
                st.warning(f"⚠️ {w}")

        # Update relationship in state
        new_rel_entry = {
            "left_dataset_id": primary_ds["id"],
            "left_key": left_key,
            "right_dataset_id": r_id,
            "right_key": right_key,
            "join_type": join_type,
            "validation": validation
        }

        # Replace or add
        filtered_rels = [r for r in st.session_state.relationships if r.get("right_dataset_id") != r_id]
        filtered_rels.append(new_rel_entry)
        st.session_state.relationships = filtered_rels

    st.markdown("---")
    j_col1, j_col2 = st.columns([2, 1])
    with j_col1:
        st.markdown("**Unified Analytical Model:** Merges reference fields (e.g. `Operational Area -> Service`, `Band -> Band`) and calculates uncapped `Availability % = Available Hours / Contracted Hours` and `Service A & Band 3`.")
    with j_col2:
        if st.button("⚡ Build & Apply Joined Analytical Model", type="primary", use_container_width=True):
            sync_analytical_model()
            st.session_state.audit_logger.log("ANALYTICAL_MODEL_BUILT", "Constructed joined unified analytical model", details={"relationships": len(st.session_state.relationships)})
            st.success("Unified Joined Analytical Model successfully created! Proceed to **02. Data Quality** or **03. Column Mapping**.")
            st.rerun()

# Preview Joined Working Model
if st.session_state.get("clean_df") is not None:
    st.markdown("---")
    st.subheader("🌟 Active Working Analytical Dataset Preview")
    w_df = st.session_state["clean_df"]
    st.dataframe(w_df.head(10), use_container_width=True)
    
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Active Model Rows", f"{len(w_df):,}")
    p2.metric("Active Model Columns", f"{len(w_df.columns):,}")
    p3.metric("Active Columns List", f"{len(w_df.columns)} fields")
    p4.metric("Model Health Score", f"{st.session_state.get('structural_qa_report', {}).get('health_score', 100)}/100")
