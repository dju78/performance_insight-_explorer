import streamlit as st
import pandas as pd
from src.state import init_session_state
from src.recommendations import RecommendationEngine

init_session_state()

st.title("🛠️ 09. Actionable Recommendations & Interventions")
st.markdown("""
Formulate operational interventions mapped strictly to **analyst-approved** root-cause findings.
- **Evidence-Backed Governance:** Recommendations are generated **only** from approved findings and remain **Pending** until analyst confirmation.
- **No Fabricated Metrics:** Expected impact fields are left empty for genuine analyst estimation.
""")

insights = st.session_state.get("insights_list", [])
approved_insights = [x for x in insights if x.get("status") == "approved"]

# Auto-generate draft recommendations strictly for approved insights if recommendations_list is empty
if approved_insights and not st.session_state.get("recommendations_list"):
    st.session_state["recommendations_list"] = RecommendationEngine.generate_recommendations(approved_insights)

recs = st.session_state.get("recommendations_list", [])

if not approved_insights and not recs:
    st.warning("⚠️ **No Evidence-Based Recommendations Available:** No analytical findings have been approved yet. Please go to **08. Insights** and approve at least one finding, or add an analyst-authored recommendation below.")
else:
    st.subheader(f"📋 Recommendation Review ({len(recs)} Items)")
    
    for i, rec in enumerate(recs):
        with st.container():
            st.markdown(f"### Recommendation #{i+1}: {rec.get('title')}")
            if rec.get("finding"):
                st.caption(f"**Linked Evidence:** {rec.get('finding')}")
                
            status = rec.get("status", "pending")
            st_color = "green" if status == "approved" else ("red" if status == "rejected" else "orange")
            st.markdown(f"**Status:** :{st_color}[{status.upper()}]")
            
            c1, c2 = st.columns(2)
            with c1:
                rec['action'] = st.text_area(f"Action Detail", value=rec.get('action', ''), key=f"rec_act_{i}", height=80)
                rec['expected_impact'] = st.text_input(f"Expected Impact (Analyst-Authored)", value=rec.get('expected_impact', ''), key=f"rec_imp_{i}", placeholder="e.g. 10% turnaround reduction within 3 weeks")
            with c2:
                rec['owner'] = st.text_input(f"Accountable Owner", value=rec.get('owner', 'Operations Manager'), key=f"rec_own_{i}")
                rec['timeframe'] = st.text_input(f"Timeframe / Effort", value=rec.get('timeframe', '2-4 Weeks'), key=f"rec_tf_{i}")
                
            b1, b2, b3 = st.columns([1, 1, 4])
            with b1:
                if st.button("✅ Accept", key=f"acc_rec_{i}", use_container_width=True):
                    rec['status'] = "approved"
                    st.session_state.audit_logger.log("RECOMMENDATION_APPROVED", f"Approved recommendation {rec.get('id')}", details={"id": rec.get("id"), "title": rec.get("title")})
                    st.rerun()
            with b2:
                if st.button("❌ Reject", key=f"rej_rec_{i}", use_container_width=True):
                    rec['status'] = "rejected"
                    st.session_state.audit_logger.log("RECOMMENDATION_REJECTED", f"Rejected recommendation {rec.get('id')}", details={"id": rec.get("id"), "title": rec.get("title")})
                    st.rerun()
            with b3:
                if st.button("✏️ Save & Approve", key=f"save_rec_{i}"):
                    rec['status'] = "approved"
                    st.session_state.audit_logger.log("RECOMMENDATION_EDITED", f"Edited and approved recommendation {rec.get('id')}", details={"id": rec.get("id")})
                    st.success("Saved and approved!")
                    st.rerun()
                    
            st.markdown("---")

# Add Custom Analyst-Authored Recommendation
with st.expander("➕ Add Custom Analyst-Authored Recommendation"):
    new_title = st.text_input("Intervention Title", placeholder="e.g. Fast-Track Triage for Priority Cases")
    new_action = st.text_area("Action Steps", placeholder="Specific operational implementation steps...")
    new_owner = st.text_input("Accountable Owner", placeholder="e.g. Service Delivery Lead")
    new_impact = st.text_input("Expected Impact", placeholder="e.g. Reduce queue wait time by 2 days")
    new_tf = st.text_input("Timeframe", placeholder="e.g. 2 Weeks")
    
    if st.button("Add & Approve Recommendation", type="primary"):
        if new_title and new_action:
            recs.append({
                "id": f"REC-CUST-{len(recs)+1:02d}",
                "title": new_title,
                "finding": "Analyst-Authored Intervention",
                "evidence": "Strategic intervention defined during operational interview analysis.",
                "action": new_action,
                "owner": new_owner or "Operations Lead",
                "timeframe": new_tf or "2 Weeks",
                "expected_impact": new_impact or "Operational optimization",
                "status": "approved"
            })
            st.session_state["recommendations_list"] = recs
            st.session_state.audit_logger.log("RECOMMENDATION_ADDED", f"Added custom recommendation: {new_title}")
            st.success("Custom recommendation added and approved!")
            st.rerun()
