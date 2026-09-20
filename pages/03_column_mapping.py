"""Page 03: Semantic Column Mapping & Role Assignment.
Maps source columns to 25+ standardized analytical roles across sectors with confidence scores
and explicit analyst confirmation controls.
"""
import sys
from pathlib import Path

# Ensure workspace root is in sys.path for Streamlit Cloud deployment
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
from core.constants import WorkflowStage
from core.state import init_session_state, advance_workflow_stage, log_audit_event, invalidate_derived_state
from modules.mapping.mapper import suggest_semantic_mappings, SEMANTIC_ROLE_CATALOG

init_session_state()

st.title("🏷️ Stage 5: Semantic Column Mapping & Taxonomy")
st.markdown("Assign standardized operational and analytical roles to dataset columns with confidence transparency.")

df = st.session_state.get("clean_df")
if df is None:
    st.warning("⚠️ No active dataset loaded. Please go to **01_Data_Ingestion** first.")
    st.stop()

# Generate or retrieve suggested mappings
suggestions = st.session_state.get("suggested_mappings", {})
if not suggestions:
    suggestions = suggest_semantic_mappings(df)
    st.session_state.suggested_mappings = suggestions

confirmed = st.session_state.get("confirmed_mappings", {})

st.info("💡 **Integrity Principle:** Inferred suggestions are recommendations only. Review each column and explicitly confirm mappings to activate KPI engines and diagnostic charts.")

# Role options list
role_keys = list(SEMANTIC_ROLE_CATALOG.keys())
role_labels = {k: f"{SEMANTIC_ROLE_CATALOG[k]['label']} ({SEMANTIC_ROLE_CATALOG[k]['category']})" for k in role_keys}
role_options = ["unmapped"] + role_keys

st.markdown("---")
st.subheader("📋 Column-to-Role Assignment Table")

updated_confirmed = dict(confirmed)

# Interactive Mapping Table
for col in df.columns:
    col_str = str(col)
    sug_info = suggestions.get(col_str, {})
    sug_role = sug_info.get("suggested_role", "unmapped")
    conf_pct = sug_info.get("confidence", 0.0) * 100.0
    reason = sug_info.get("reasoning", "No pattern detected")
    cur_val = confirmed.get(col_str, sug_role if conf_pct >= 50.0 else "unmapped")

    c1, c2, c3 = st.columns([3, 3, 4])
    with c1:
        st.markdown(f"**`{col_str}`**")
        sample_vals = df[col].dropna().head(3).astype(str).tolist()
        st.caption(f"Sample: {', '.join(sample_vals) if sample_vals else '<Empty>'}")
    with c2:
        idx = role_options.index(cur_val) if cur_val in role_options else 0
        sel = st.selectbox(
            "Assigned Role",
            role_options,
            format_func=lambda x: "Unmapped / Ignore" if x == "unmapped" else role_labels.get(x, x),
            index=idx,
            key=f"map_sel_{col_str}",
            label_visibility="collapsed"
        )
        updated_confirmed[col_str] = sel
    with c3:
        conf_color = "🟢" if conf_pct >= 70 else ("🟡" if conf_pct >= 40 else "⚪")
        st.caption(f"{conf_color} **Confidence:** {conf_pct:.0f}% | *{reason}*")

st.markdown("---")

c_btn1, c_btn2 = st.columns([2, 2])
with c_btn1:
    if st.button("💾 Save & Confirm Column Mappings", type="primary", use_container_width=True):
        st.session_state.confirmed_mappings = {k: v for k, v in updated_confirmed.items() if v != "unmapped"}
        advance_workflow_stage(WorkflowStage.STAGE_05_MAPPING)
        log_audit_event("MAPPINGS_CONFIRMED", f"Confirmed {len(st.session_state.confirmed_mappings)} mapped roles.")
        invalidate_derived_state()
        st.success("Column mappings confirmed successfully! Proceed to **04_KPI_Configuration**.")
        st.rerun()

with c_btn2:
    if st.button("🔄 Reset to Automatic Suggestions", use_container_width=True):
        st.session_state.confirmed_mappings = {c: info["suggested_role"] for c, info in suggestions.items() if info.get("confidence", 0) >= 0.50}
        invalidate_derived_state()
        st.info("Reset to high-confidence suggestions.")
        st.rerun()

# Role Coverage Summary
st.markdown("---")
st.subheader("📊 Mapped Role Coverage")
mapped_roles = set(st.session_state.get("confirmed_mappings", {}).values())

cov_cols = st.columns(4)
with cov_cols[0]:
    has_date = any(r in ["date", "reporting_period"] for r in mapped_roles)
    st.markdown(f"**Date / Period:** {'✅ Mapped' if has_date else '❌ Missing'}")
with cov_cols[1]:
    has_group = any(r in ["team", "department", "region", "product_service", "customer_segment"] for r in mapped_roles)
    st.markdown(f"**Group Dimensions:** {'✅ Mapped' if has_group else '❌ Missing'}")
with cov_cols[2]:
    has_perf = any(r in ["actual", "target", "volume_inflow", "quality_measure"] for r in mapped_roles)
    st.markdown(f"**Performance Metrics:** {'✅ Mapped' if has_perf else '❌ Missing'}")
with cov_cols[3]:
    has_cap = any(r in ["capacity_fte", "duration_wait_time", "cost"] for r in mapped_roles)
    st.markdown(f"**Capacity / Efficiency:** {'✅ Mapped' if has_cap else '⚪ Optional'}")
