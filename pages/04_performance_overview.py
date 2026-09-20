"""Page 04: Dynamic KPI Configuration & 3-Tier Performance Overview.
Features:
- Dynamic No-Code KPI builder with direction-aware RAG status
- 3-Tier View: Executive Summary, Analyst Diagnostics, Technical Details
- Multi-dimensional slicing and plain-English performance interpretation
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from core.constants import TargetDirection, WorkflowStage
from core.models import KPIDefinition
from core.state import (
    init_session_state, get_working_df, advance_workflow_stage, log_audit_event, invalidate_derived_state
)
from modules.kpi_engine.engine import compute_kpi_value, evaluate_kpi_rag_status

init_session_state()

st.title("📊 Stage 6 & 8: Performance Scorecard & Overview")

df = get_working_df()
if df is None:
    st.warning("⚠️ No active dataset loaded. Please go to **01_Data_Ingestion** first.")
    st.stop()

confirmed = st.session_state.get("confirmed_mappings", {})

# View Tier Switcher
c_t1, c_t2 = st.columns([3, 1])
with c_t1:
    st.markdown("Monitor target attainment, operational throughput, and directional RAG performance.")
with c_t2:
    view_tier = st.selectbox("Dashboard View Tier", ["Executive View", "Analyst View", "Technical View"])

# Multi-Dimensional Filter Bar
with st.expander("🔍 Interactive Slice-and-Dice Filters", expanded=False):
    dim_cols = [c for c, r in confirmed.items() if r in ["team", "department", "region", "product_service", "customer_segment", "status"]]
    if dim_cols:
        f_cols = st.columns(min(len(dim_cols), 4))
        for idx, col in enumerate(dim_cols[:4]):
            with f_cols[idx]:
                uniques = df[col].dropna().unique().tolist()
                sel_vals = st.multiselect(f"Filter {col}", uniques, default=uniques, key=f"filter_{col}")
                st.session_state.active_filters[col] = sel_vals
    else:
        st.caption("No categorical dimension columns mapped. Map 'Team', 'Department', or 'Region' to filter.")

# -------------------------------------------------------------
# DYNAMIC KPI REGISTRY & EVALUATION
# -------------------------------------------------------------
# Seed default standard KPIs from mapped columns if registry is empty
if not st.session_state.get("custom_kpi_registry"):
    auto_kpis = {}
    
    # 1. Actual Volume
    act_col = next((c for c, r in confirmed.items() if r == "actual"), None)
    tgt_col = next((c for c, r in confirmed.items() if r == "target"), None)
    if act_col:
        tgt_val = float(df[tgt_col].mean()) if (tgt_col and tgt_col in df.columns) else None
        auto_kpis["kpi_output"] = KPIDefinition(
            id="kpi_output",
            name=f"Delivered Volume ({act_col})",
            business_definition="Total operational output completed across the period.",
            formula=f"sum({act_col})",
            source_field=act_col,
            unit="Cases",
            aggregation_method="sum",
            target_value=tgt_val,
            directionality=TargetDirection.HIGHER_IS_BETTER
        )

    # 2. SLA / Quality Measure
    sla_col = next((c for c, r in confirmed.items() if r == "quality_measure"), None)
    if sla_col:
        auto_kpis["kpi_quality"] = KPIDefinition(
            id="kpi_quality",
            name=f"Quality / SLA Score ({sla_col})",
            business_definition="Average quality attainment or customer satisfaction score.",
            formula=f"mean({sla_col})",
            source_field=sla_col,
            unit="%",
            aggregation_method="mean",
            target_value=95.0,
            directionality=TargetDirection.HIGHER_IS_BETTER
        )

    # 3. Wait Time / Duration
    dur_col = next((c for c, r in confirmed.items() if r == "duration_wait_time"), None)
    if dur_col:
        auto_kpis["kpi_duration"] = KPIDefinition(
            id="kpi_duration",
            name=f"Average Processing Duration ({dur_col})",
            business_definition="Mean turnaround or wait duration per case.",
            formula=f"mean({dur_col})",
            source_field=dur_col,
            unit="Days / Mins",
            aggregation_method="mean",
            target_value=30.0,
            directionality=TargetDirection.LOWER_IS_BETTER
        )

    # 4. Inflow Volume
    inf_col = next((c for c, r in confirmed.items() if r == "volume_inflow"), None)
    if inf_col:
        auto_kpis["kpi_inflow"] = KPIDefinition(
            id="kpi_inflow",
            name=f"Demand Inflow ({inf_col})",
            business_definition="Total new demand received in period.",
            formula=f"sum({inf_col})",
            source_field=inf_col,
            unit="Cases",
            aggregation_method="sum",
            directionality=TargetDirection.INFORMATIONAL
        )

    st.session_state.custom_kpi_registry = auto_kpis

# Evaluate all KPIs in registry
evaluated_kpis = {}
for kpi_id, kpi_def in st.session_state.custom_kpi_registry.items():
    if isinstance(kpi_def, dict):
        kpi_obj = KPIDefinition(**kpi_def)
    else:
        kpi_obj = kpi_def

    val, series, msg = compute_kpi_value(df, kpi_obj)
    rag_eval = evaluate_kpi_rag_status(val, kpi_obj)

    evaluated_kpis[kpi_id] = {
        "name": kpi_obj.name,
        "actual": val,
        "target": kpi_obj.target_value,
        "unit": kpi_obj.unit,
        "direction": kpi_obj.directionality.value if hasattr(kpi_obj.directionality, "value") else str(kpi_obj.directionality),
        "status": rag_eval.get("status"),
        "color": rag_eval.get("color"),
        "icon": rag_eval.get("icon"),
        "variance": rag_eval.get("variance"),
        "variance_pct": rag_eval.get("variance_pct"),
        "interpretation": rag_eval.get("interpretation")
    }

st.session_state.kpi_results = evaluated_kpis

# -------------------------------------------------------------
# TIER 1: EXECUTIVE VIEW
# -------------------------------------------------------------
if view_tier == "Executive View":
    st.subheader("🎯 Executive KPI Scorecard")

    if evaluated_kpis:
        cols_kpi = st.columns(min(len(evaluated_kpis), 4))
        for idx, (kpi_id, res) in enumerate(evaluated_kpis.items()):
            col_idx = idx % 4
            with cols_kpi[col_idx]:
                act_str = f"{res['actual']:,.1f} {res['unit']}" if res['actual'] is not None else "N/A"
                tgt_str = f"Target: {res['target']:,.1f} {res['unit']}" if res['target'] is not None else "No target"
                var_str = f"{res['variance_pct']:+.1f}%" if res['variance_pct'] is not None else None
                
                st.metric(
                    label=f"{res['icon']} {res['name']}",
                    value=act_str,
                    delta=var_str,
                    help=res['interpretation']
                )
                st.caption(f"**Status:** {res['status']}")

    st.markdown("---")
    st.subheader("📋 Executive Summary Table")
    
    scorecard_rows = []
    for kpi_id, res in evaluated_kpis.items():
        scorecard_rows.append({
            "KPI Name": res["name"],
            "Actual Value": f"{res['actual']:,.1f} {res['unit']}" if res['actual'] is not None else "N/A",
            "Target Standard": f"{res['target']:,.1f} {res['unit']}" if res['target'] is not None else "N/A",
            "Variance %": f"{res['variance_pct']:+.1f}%" if res['variance_pct'] is not None else "N/A",
            "Status": f"{res['icon']} {res['status']}",
            "Operational Interpretation": res["interpretation"]
        })
    st.dataframe(pd.DataFrame(scorecard_rows), use_container_width=True)

# -------------------------------------------------------------
# TIER 2: ANALYST VIEW
# -------------------------------------------------------------
elif view_tier == "Analyst View":
    st.subheader("🔬 Analyst Diagnostic Scorecard & Custom KPI Builder")
    
    # Custom KPI Creator Expander
    with st.expander("➕ Define New Custom KPI (No-Code)", expanded=False):
        c_k1, c_k2 = st.columns(2)
        with c_k1:
            new_kpi_name = st.text_input("KPI Name", placeholder="e.g. Backlog Clearance Velocity")
            new_kpi_def = st.text_input("Business Definition", placeholder="e.g. Ratio of resolved cases to opening backlog")
            new_kpi_unit = st.text_input("Unit of Measure", value="Cases")
            new_kpi_agg = st.selectbox("Aggregation Method", ["sum", "mean", "median", "count"])
            new_kpi_source = st.selectbox("Source Column", df.columns)
        with c_k2:
            new_kpi_target = st.number_input("Target Value", value=100.0)
            new_kpi_warn = st.number_input("Warning Threshold", value=90.0)
            new_kpi_crit = st.number_input("Critical Threshold", value=80.0)
            new_kpi_dir = st.selectbox("Target Directionality", [
                TargetDirection.HIGHER_IS_BETTER.value,
                TargetDirection.LOWER_IS_BETTER.value,
                TargetDirection.TARGET_RANGE.value,
                TargetDirection.INFORMATIONAL.value
            ])

        if st.button("💾 Register Custom KPI", type="primary"):
            new_id = f"custom_kpi_{len(st.session_state.custom_kpi_registry) + 1}"
            st.session_state.custom_kpi_registry[new_id] = KPIDefinition(
                id=new_id,
                name=new_kpi_name,
                business_definition=new_kpi_def,
                formula=f"{new_kpi_agg}({new_kpi_source})",
                source_field=new_kpi_source,
                unit=new_kpi_unit,
                aggregation_method=new_kpi_agg,
                target_value=float(new_kpi_target),
                warning_threshold=float(new_kpi_warn),
                critical_threshold=float(new_kpi_crit),
                directionality=TargetDirection(new_kpi_dir)
            )
            log_audit_event("CUSTOM_KPI_CREATED", f"Defined custom KPI: {new_kpi_name}")
            st.success(f"Registered KPI '{new_kpi_name}'")
            st.rerun()

    # Detailed KPI Breakdown
    for kpi_id, res in evaluated_kpis.items():
        st.markdown(f"#### {res['icon']} {res['name']}")
        st.markdown(f"- **Actual:** `{res['actual']}` {res['unit']} | **Target:** `{res['target']}` {res['unit']} | **Variance:** `{res['variance_pct']}%`")
        st.markdown(f"- **Evaluation:** {res['interpretation']}")
        st.markdown("---")

# -------------------------------------------------------------
# TIER 3: TECHNICAL VIEW
# -------------------------------------------------------------
else:
    st.subheader("📐 Technical Mathematical & Formula Diagnostics")
    tech_rows = []
    for kpi_id, kpi_def in st.session_state.custom_kpi_registry.items():
        if isinstance(kpi_def, dict):
            k = KPIDefinition(**kpi_def)
        else:
            k = kpi_def
        res = evaluated_kpis.get(k.id, {})
        tech_rows.append({
            "KPI ID": k.id,
            "Mathematical Formula": k.formula,
            "Source Field": k.source_field or f"{k.numerator_field} / {k.denominator_field}",
            "Aggregation": k.aggregation_method,
            "Directionality": k.directionality.value if hasattr(k.directionality, "value") else str(k.directionality),
            "Min Sample Size": k.min_sample_size,
            "Evaluated Value": res.get("actual")
        })
    st.dataframe(pd.DataFrame(tech_rows), use_container_width=True)

st.markdown("---")
if st.button("Proceed to Stage 7 (Trends & Run Charts) ➡️", type="primary"):
    advance_workflow_stage(WorkflowStage.STAGE_08_OVERVIEW)
    st.success("Performance overview stage recorded.")
