import streamlit as st
import pandas as pd
from src.state import init_session_state
from src.mapping import (
    suggest_mappings,
    validate_mapping_integrity,
    SEMANTIC_ROLES,
    ROLE_CATALOGUE
)
from src.quality import run_semantic_qa, run_quality_audit

init_session_state()

st.title("🗺️ 03. Semantic Column Mapping & Target Setup")
st.markdown("""
Review auto-detected provisional mapping suggestions and confirm analytical roles.
- **Provisional Safety:** Suggested mappings **never** activate KPIs automatically until you click **Confirm Mappings**.
- **Target Directionality:** Set whether **Higher is better**, **Lower is better**, or **Neutral** for key targets and metrics.
""")

df = st.session_state.get("clean_df")
if df is None:
    st.warning("⚠️ Please upload a dataset on Page 01 first.")
    st.stop()

# Generate suggestions for active dataset if not present
if not st.session_state.get("suggested_mappings"):
    st.session_state["suggested_mappings"] = suggest_mappings(df)

suggested = st.session_state.get("suggested_mappings", {})
confirmed = st.session_state.get("confirmed_mappings", {})
target_dirs = st.session_state.get("target_directions", {})

suggested_count = len([k for k, v in suggested.items() if v.get("suggested_role")])
confirmed_count = len([k for k, v in confirmed.items() if v])

col_a, col_b, col_c = st.columns(3)
col_a.metric("Total Dataset Columns", len(df.columns))
col_b.metric("Provisional Suggestions", suggested_count)
col_c.metric("Confirmed Mappings", confirmed_count)

st.markdown("---")
st.subheader("📋 Column Review & Role Assignment")

mapping_form = {}
direction_form = {}

# Table Header
h1, h2, h3, h4 = st.columns([2, 2, 2, 2])
h1.markdown("**Source Column**")
h2.markdown("**Suggested Role (Confidence)**")
h3.markdown("**Confirmed Semantic Role**")
h4.markdown("**Target Direction**")

for col in df.columns:
    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    col_info = suggested.get(col, {})
    sug_role = col_info.get("suggested_role")
    sug_conf = col_info.get("confidence", 0.0)
    
    with c1:
        st.markdown(f"**`{col}`**")
        st.caption(f"Type: `{df[col].dtype}` | Nulls: `{df[col].isna().sum()}`")
        
    with c2:
        if sug_role:
            st.markdown(f"💡 `{sug_role}`")
            st.caption(f"Confidence: `{sug_conf*100:.0f}%`")
        else:
            st.caption("Unmapped")
            
    with c3:
        current_val = confirmed.get(col) or sug_role or "unmapped"
        role_options = ["unmapped"] + SEMANTIC_ROLES
        idx = role_options.index(current_val) if current_val in role_options else 0
        selected_role = st.selectbox(
            f"Role for {col}",
            role_options,
            index=idx,
            key=f"map_{col}",
            label_visibility="collapsed"
        )
        mapping_form[col] = selected_role
        
    with c4:
        if selected_role in ["target", "metric_rate", "metric_time", "metric_cost", "actual", "processing_time", "cost", "quality_measure", "customer_measure"]:
            cur_dir = target_dirs.get(col, "lower_is_better" if "time" in selected_role or "cost" in selected_role or "duration" in col.lower() or "error" in col.lower() or "tat" in col.lower() else "higher_is_better")
            dir_options = ["higher_is_better", "lower_is_better", "neutral"]
            dir_labels = {"higher_is_better": "📈 Higher is better", "lower_is_better": "📉 Lower is better", "neutral": "⚖️ Neutral / descriptive"}
            dir_idx = dir_options.index(cur_dir) if cur_dir in dir_options else 0
            
            sel_dir = st.selectbox(
                f"Direction for {col}",
                dir_options,
                format_func=lambda x: dir_labels[x],
                index=dir_idx,
                key=f"dir_{col}",
                label_visibility="collapsed"
            )
            direction_form[col] = sel_dir
        else:
            st.caption("Direction: N/A")

st.markdown("---")
col_btn1, col_btn2 = st.columns([1, 1])

with col_btn1:
    if st.button("✅ Confirm All Column Mappings & Target Directions", type="primary", use_container_width=True):
        st.session_state["confirmed_mappings"] = {k: v for k, v in mapping_form.items() if v != "unmapped"}
        st.session_state["target_directions"] = direction_form
        
        # Run Stage B Semantic QA immediately
        st.session_state["semantic_qa_report"] = run_semantic_qa(df, st.session_state["confirmed_mappings"])
        st.session_state["qa_report"] = run_quality_audit(df, st.session_state["confirmed_mappings"])
        
        st.session_state.audit_logger.log(
            "COLUMN_MAPPINGS_CONFIRMED",
            f"Confirmed {len(st.session_state['confirmed_mappings'])} column mappings",
            details={
                "confirmed_count": len(st.session_state["confirmed_mappings"]),
                "mappings": st.session_state["confirmed_mappings"],
                "target_directions": st.session_state["target_directions"]
            }
        )
        st.session_state.audit_logger.log(
            "SEMANTIC_QA_COMPLETED",
            "Executed Stage B Semantic QA after mapping confirmation",
            details={"semantic_issues": st.session_state["semantic_qa_report"]["total_issues"]}
        )
        st.success("Column mappings and target directions confirmed safely! Downstream analytical pages unlocked.")
        st.rerun()

with col_btn2:
    if st.button("🔄 Reset Mappings to Auto-Suggestions", use_container_width=True):
        st.session_state["suggested_mappings"] = suggest_mappings(df)
        st.session_state["confirmed_mappings"] = {}
        st.session_state["semantic_qa_report"] = None
        st.info("Reset to provisional suggestions. Please review and click 'Confirm All Column Mappings'.")
        st.rerun()

# Mapping Validation Report
val_report = validate_mapping_integrity(df, st.session_state.get("confirmed_mappings", {}))
if val_report["errors"]:
    st.error(f"⚠️ **Mapping Errors Detected:** {len(val_report['errors'])}")
    for err in val_report["errors"]:
        st.markdown(f"- {err}")
elif val_report["warnings"]:
    st.warning(f"ℹ️ **Mapping Advisory:**")
    for warn in val_report["warnings"]:
        st.markdown(f"- {warn}")
else:
    if st.session_state.get("confirmed_mappings"):
        st.success("✅ Semantic mapping is valid and ready for full downstream analysis.")
