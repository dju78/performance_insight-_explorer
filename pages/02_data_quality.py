"""Page 02: 10-Dimension Enterprise Data Quality Engine.
Assesses Completeness, Validity, Accuracy, Consistency, Uniqueness, Timeliness, Integrity,
Conformity, Coverage, and Plausibility with remediation tracking and analysis gating.
"""
import sys
from pathlib import Path

# Ensure workspace root is in sys.path for Streamlit Cloud deployment
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
from core.constants import QualityDimension, QualitySeverity, RemediationAction, WorkflowStage
from core.state import init_session_state, advance_workflow_stage, log_audit_event, invalidate_derived_state
from modules.quality.engine import evaluate_data_quality_10d

init_session_state()

st.title("🛡️ Stage 4: 10-Dimension Data Quality Engine")
st.markdown("Automated multi-dimensional structural & semantic quality audit with remediation tracking.")

df = st.session_state.get("clean_df")
if df is None:
    st.warning("⚠️ No active dataset loaded. Please go to **01_Data_Ingestion** first.")
    st.stop()

# Evaluate Quality
remed = st.session_state.get("remediated_issues", {})
qa_report = evaluate_data_quality_10d(df, st.session_state.get("confirmed_mappings"), remed)
st.session_state.qa_report = qa_report

# High-Level Health Scorecard
health_score = qa_report.get("health_score", 100.0)
crit_count = qa_report.get("critical_count", 0)
high_count = qa_report.get("high_count", 0)
med_count = qa_report.get("medium_count", 0)
low_count = qa_report.get("low_count", 0)
is_blocked = qa_report.get("is_analysis_blocked", False)

c_q1, c_q2, c_q3, c_q4, c_q5 = st.columns(5)
with c_q1:
    st.metric("Overall Data Health", f"{health_score:.1f}/100")
with c_q2:
    st.metric("🚨 Critical Issues", f"{crit_count}", delta=None)
with c_q3:
    st.metric("⚠️ High Issues", f"{high_count}")
with c_q4:
    st.metric("🟡 Medium Issues", f"{med_count}")
with c_q5:
    st.metric("ℹ️ Low / Info", f"{low_count}")

# Blocking Status Alert
if is_blocked:
    st.error(f"🚨 **ANALYSIS BLOCKED:** {crit_count} Critical issue(s) require review and remediation before downstream analysis can proceed.")
    for reason in qa_report.get("blocking_reasons", []):
        st.caption(f"- ⛔ {reason}")
else:
    st.success("✅ **Quality Clearance Approved:** No unreviewed critical blockers. Dataset is fit for performance analysis.")

st.markdown("---")

# 10-Dimension Score Breakdown
st.subheader("📊 Quality Scores by Dimension")
dim_scores = qa_report.get("dimension_scores", {})
cols_dim = st.columns(5)
dim_list = list(dim_scores.items())

for idx, (dim_name, score) in enumerate(dim_list):
    col_idx = idx % 5
    with cols_dim[col_idx]:
        st.metric(dim_name, f"{score:.0f}%")

st.markdown("---")

# Issues Audit & Remediation Workspace
st.subheader("🔍 Quality Issue Registry & Remediation Manager")
issues = qa_report.get("issues", [])

if not issues:
    st.info("🎉 Excellent! No data quality issues detected across all 10 dimensions.")
else:
    # Filter controls
    f_c1, f_c2 = st.columns(2)
    with f_c1:
        sev_filter = st.multiselect("Filter by Severity", ["Critical", "High", "Medium", "Low"], default=["Critical", "High", "Medium", "Low"])
    with f_c2:
        dim_filter = st.multiselect("Filter by Dimension", [d.value for d in QualityDimension], default=[d.value for d in QualityDimension])

    filtered_issues = [
        i for i in issues 
        if i.get("severity") in sev_filter and i.get("dimension") in dim_filter
    ]

    st.caption(f"Displaying {len(filtered_issues)} of {len(issues)} issues:")

    for iss in filtered_issues:
        iid = iss["issue_id"]
        sev = iss["severity"]
        dim = iss["dimension"]
        title = iss["title"]
        desc = iss["description"]
        field = iss["field"]
        impact = iss.get("business_impact", "")
        treatment = iss.get("recommended_treatment", "")
        status = remed.get(iid, {}).get("status", iss.get("status", "Unresolved"))
        just = remed.get(iid, {}).get("justification", "")

        sev_icon = "🔴" if sev == "Critical" else ("🟠" if sev == "High" else ("🟡" if sev == "Medium" else "ℹ️"))

        with st.expander(f"{sev_icon} [{iid}] **{title}** | Field: `{field}` | Severity: **{sev}** | Status: `{status}`", expanded=(sev == "Critical")):
            st.markdown(f"**Description:** {desc}")
            st.markdown(f"**Business Impact:** {impact}")
            st.markdown(f"**Recommended Treatment:** {treatment}")

            if iss.get("sample_values"):
                st.caption(f"Sample Observations: {iss['sample_values']}")

            st.markdown("##### 🛠️ Analyst Remediation Action")
            c_r1, c_r2, c_r3 = st.columns([2, 3, 1])
            with c_r1:
                action_choice = st.selectbox(
                    "Remediation Treatment",
                    [
                        "Accept as Known Limitation",
                        "Exclude Affected Records",
                        "Flag in Governance Caveats",
                        "Add Justification"
                    ],
                    key=f"action_{iid}"
                )
            with c_r2:
                just_text = st.text_input("Analyst Justification / Working Note", value=just, key=f"just_{iid}", placeholder="Explain rationale for treatment...")
            with c_r3:
                if st.button("Apply Decision", key=f"btn_{iid}", type="primary"):
                    st.session_state.remediated_issues[iid] = {
                        "status": "Remediated",
                        "action": action_choice,
                        "justification": just_text
                    }
                    log_audit_event("QUALITY_ISSUE_REMEDIATED", f"Issue {iid} ({title}) remediated via '{action_choice}'. Justification: {just_text}")
                    invalidate_derived_state()
                    st.success(f"Updated {iid}")
                    st.rerun()

st.markdown("---")
col_b1, col_b2 = st.columns([3, 1])
with col_b1:
    st.session_state.data_quality_approved = st.checkbox(
        "✅ **I confirm that I have reviewed the Data Quality Audit and approve the dataset for analysis.**",
        value=st.session_state.get("data_quality_approved", False)
    )
with col_b2:
    if st.button("Proceed to Stage 5 (Column Mapping) ➡️", use_container_width=True, type="primary"):
        advance_workflow_stage(WorkflowStage.STAGE_04_QUALITY)
        st.success("Quality stage completed! Proceeding to Column Mapping.")
