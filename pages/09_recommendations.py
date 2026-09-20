"""Page 09: Prioritized Recommendations, Impact-Effort Matrix & Traceability.
Features:
- Prioritized recommendations following directly from accepted evidence insights
- Impact x Effort framework (Quick Wins, Strategic Initiatives, Investigations)
- Non-prescriptive wording safeguards
- Full lifecycle Traceability Matrix (Data -> Calculation -> Finding -> Recommendation -> Action -> Outcome)
- One-click conversion of recommendations into tracked action items
"""
import streamlit as st
import pandas as pd
from core.constants import WorkflowStage
from core.state import init_session_state, advance_workflow_stage, log_audit_event
from modules.recommendations.engine import generate_prioritized_recommendations, build_traceability_matrix
from modules.actions.tracker import convert_recommendation_to_action

init_session_state()

st.title("🎯 Stage 13: Prioritized Recommendations & Traceability")
st.markdown("Formulate actionable, evidence-grounded operational interventions with Impact × Effort prioritization.")

insights = st.session_state.get("insights_list", [])
if not insights:
    st.info("ℹ️ No active insights found. Complete Stage 12 (Insights) before generating recommendations.")
    st.stop()

# Generate or retrieve recommendations
if not st.session_state.get("recommendations_list"):
    recs = generate_prioritized_recommendations(insights)
    st.session_state.recommendations_list = recs

recommendations = st.session_state.get("recommendations_list", [])

# Impact x Effort Overview
st.subheader("1️⃣ Prioritization Matrix (Impact × Effort)")

col_qw, col_si, col_fi = st.columns(3)
quick_wins = [r for r in recommendations if getattr(r, "category", "") == "Quick Win" or getattr(r, "category", {}).value == "Quick Win"]
strat_inits = [r for r in recommendations if "Strategic" in str(getattr(r, "category", ""))]
monitors = [r for r in recommendations if "Monitoring" in str(getattr(r, "category", "")) or "Investigation" in str(getattr(r, "category", ""))]

with col_qw:
    st.markdown("##### ⚡ Quick Wins (High Impact / Low-Med Effort)")
    st.caption(f"{len(quick_wins)} recommended intervention(s)")
with col_si:
    st.markdown("##### 🏛️ Strategic Initiatives (High Impact / High Effort)")
    st.caption(f"{len(strat_inits)} recommended intervention(s)")
with col_fi:
    st.markdown("##### 🔍 Continuous Monitoring / Investigation")
    st.caption(f"{len(monitors)} recommended action(s)")

st.markdown("---")

# Recommendations List & Action Conversion
st.subheader("2️⃣ Recommended Operational Interventions")

for rec in recommendations:
    rec_id = getattr(rec, "id", "")
    prob = getattr(rec, "problem_addressed", "")
    act_prop = getattr(rec, "proposed_action", "")
    benefit = getattr(rec, "expected_benefit", "")
    prio = getattr(rec, "priority", "High")
    prio_str = prio.value if hasattr(prio, "value") else str(prio)
    cat = getattr(rec, "category", "Quick Win")
    cat_str = cat.value if hasattr(cat, "value") else str(cat)
    owner = getattr(rec, "responsible_owner", "Operations Lead")
    ts = getattr(rec, "timescale", "30-60 days")
    succ = getattr(rec, "success_measure", "")
    risk = getattr(rec, "risk", "")
    conf = getattr(rec, "confidence_level", "")

    with st.expander(f"📌 [{rec_id}] **{cat_str}**: {prob[:60]}... | Priority: **{prio_str}** | Owner: `{owner}`"):
        st.markdown(f"**Problem Addressed:** {prob}")
        st.markdown(f"**Proposed Operational Action:** {act_prop}")
        st.markdown(f"**Expected Benefit:** {benefit}")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"- **Implementation Timescale:** `{ts}`")
            st.markdown(f"- **Target Success Metric:** `{succ}`")
            st.markdown(f"- **Implementation Risk:** {risk}")
        with c2:
            st.markdown(f"- **Assigned Accountable Owner:** `{owner}`")
            st.markdown(f"- **Evidence Grounding Confidence:** `{conf}`")

        # Convert to Tracked Action Form
        st.markdown("##### 📋 Convert into Tracked Action Item")
        c_a1, c_a2, c_a3 = st.columns([3, 2, 1])
        with c_a1:
            act_title = st.text_input("Action Title", value=f"Implement {rec_id} Intervention", key=f"act_title_{rec_id}")
        with c_a2:
            act_owner = st.text_input("Action Owner", value=owner, key=f"act_owner_{rec_id}")
        with c_a3:
            if st.button("➕ Convert to Action", key=f"btn_conv_{rec_id}", type="primary"):
                action_item = convert_recommendation_to_action(
                    rec, act_title, act_prop, act_owner, "Operations", "Next Month End"
                )
                st.session_state.action_registry.append(action_item)
                log_audit_event("ACTION_CONVERTED_FROM_REC", f"Converted {rec_id} to Action Item {action_item.id}")
                st.success(f"Created action item [{action_item.id}]! View in Action Tracking.")
                st.rerun()

# -------------------------------------------------------------
# 3. END-TO-END TRACEABILITY MATRIX
# -------------------------------------------------------------
st.markdown("---")
st.subheader("3️⃣ End-to-End Lifecycle Traceability Matrix")
st.caption("Verifiable chain linking Data -> Calculation -> Finding -> Recommendation -> Action -> Outcome.")

trace_df = build_traceability_matrix(
    st.session_state.get("dataset_name", "Active Dataset"),
    st.session_state.get("kpi_results", {}),
    insights,
    recommendations,
    st.session_state.get("action_registry", [])
)
st.dataframe(trace_df, use_container_width=True)

st.markdown("---")
if st.button("Proceed to Stage 14 (Action Tracking & Realization) ➡️", type="primary"):
    advance_workflow_stage(WorkflowStage.STAGE_13_RECOMMENDATIONS)
    st.success("Recommendations approved.")
