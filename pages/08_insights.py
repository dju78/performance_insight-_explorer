"""Page 08: Evidence-Based Insights & Findings Curation.
Features:
- Deterministic insight generation directly from verified session computations
- Full insight metadata (Finding, Evidence, Confidence, Caveats, Limitations, Next Steps)
- Analyst curation workflow: Accept, Edit, Reject, Pin, Add Context
"""
import streamlit as st
import pandas as pd
from core.constants import WorkflowStage
from core.models import EvidenceInsight
from core.state import init_session_state, advance_workflow_stage, log_audit_event
from modules.insights.engine import generate_deterministic_insights

init_session_state()

st.title("💡 Stage 12: Evidence-Based Insights")
st.markdown("Curate, verify, and approve empirical diagnostic findings derived strictly from calculated results.")

kpi_results = st.session_state.get("kpi_results", {})
comparisons = st.session_state.get("comparison_summary")
trends = st.session_state.get("trend_summary")
qa_report = st.session_state.get("qa_report")

# Auto-generate insights if not present
if not st.session_state.get("insights_list"):
    insights = generate_deterministic_insights(kpi_results, comparisons, trends, qa_report)
    st.session_state.insights_list = insights

insights_list = st.session_state.get("insights_list", [])

if not insights_list:
    st.info("ℹ️ No active insights generated yet. Configure KPIs in **04_Performance_Overview** to generate empirical findings.")
    st.stop()

st.caption(f"Generated {len(insights_list)} empirical findings based on verified metric variances:")

# Display and Curate Insight Cards
for idx, ins in enumerate(insights_list):
    ins_id = getattr(ins, "id", f"INS-{idx+1:03d}")
    title = getattr(ins, "finding_title", "")
    evid = getattr(ins, "quantitative_evidence", "")
    kpi = getattr(ins, "kpi_affected", "")
    conf = getattr(ins, "confidence_level", "")
    sig = getattr(ins, "business_significance", "")
    lim = getattr(ins, "statistical_limitation", "")
    caveat = getattr(ins, "data_quality_caveat", "")
    follow = getattr(ins, "suggested_follow_up", "")
    cur_status = getattr(ins, "status", "Active")
    notes = getattr(ins, "analyst_context_notes", "")

    status_icon = "📌" if cur_status == "Pinned" else ("✅" if cur_status == "Accepted" else ("❌" if cur_status == "Rejected" else "💡"))

    with st.expander(f"{status_icon} [{ins_id}] **{title}** | KPI: `{kpi}` | Status: **{cur_status}**", expanded=(cur_status in ["Active", "Pinned"])):
        st.markdown(f"**Quantitative Evidence:** {evid}")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Confidence Level:** `{conf}`")
            st.markdown(f"**Business Significance:** *{sig}*")
            st.markdown(f"**Data Quality Caveat:** {caveat}")
        with c2:
            st.markdown(f"**Statistical Limitation:** {lim}")
            st.markdown(f"**Recommended Follow-Up:** {follow}")

        # Qualitative Notes
        analyst_note = st.text_input(
            "Analyst Operational Context / Notes",
            value=notes,
            key=f"ins_note_{ins_id}",
            placeholder="Add operational justification or context..."
        )
        if hasattr(ins, "analyst_context_notes"):
            ins.analyst_context_notes = analyst_note

        # Action Buttons
        b_c1, b_c2, b_c3 = st.columns(3)
        with b_c1:
            if st.button(f"✅ Accept Finding", key=f"acc_{ins_id}", use_container_width=True):
                if hasattr(ins, "status"):
                    ins.status = "Accepted"
                log_audit_event("INSIGHT_ACCEPTED", f"Accepted insight {ins_id}")
                st.success("Accepted finding.")
                st.rerun()
        with b_c2:
            if st.button(f"📌 Pin to Executive Summary", key=f"pin_{ins_id}", use_container_width=True):
                if hasattr(ins, "status"):
                    ins.status = "Pinned"
                log_audit_event("INSIGHT_PINNED", f"Pinned insight {ins_id}")
                st.info("Pinned finding.")
                st.rerun()
        with b_c3:
            if st.button(f"❌ Reject Finding", key=f"rej_{ins_id}", use_container_width=True):
                if hasattr(ins, "status"):
                    ins.status = "Rejected"
                log_audit_event("INSIGHT_REJECTED", f"Rejected insight {ins_id}")
                st.warning("Rejected finding.")
                st.rerun()

st.markdown("---")
if st.button("Proceed to Stage 13 (Recommendations & Priorities) ➡️", type="primary"):
    advance_workflow_stage(WorkflowStage.STAGE_12_INSIGHTS)
    st.success("Insights stage approved! Proceeding to Recommendations.")
