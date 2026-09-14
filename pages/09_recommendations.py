import streamlit as st
import pandas as pd
from src.state import init_session_state

init_session_state()

st.title("🛠️ 09. Actionable Recommendations & Interventions")
st.markdown("""
Formulate operational interventions mapped to root-cause findings.
- **Review Workflow:** Explicitly **Accept**, **Edit**, or **Reject** recommendations.
- Only approved recommendations will flow into executive summaries and presentations.
""")

insights = st.session_state.get("insights_list", [])
approved_insights = [x for x in insights if x.get("status") == "approved"]

if not st.session_state.get("recommendations_list"):
    # Generate initial draft recommendations based on approved or general insights
    default_recs = []
    base_items = approved_insights if approved_insights else insights
    for item in base_items:
        rec_title = f"Operational Intervention for {item.get('title', 'Identified Issue')}"
        rec_action = f"Implement targeted workflow standardisation and triage for {item.get('title', 'process bottleneck')} to improve throughput and consistency."
        default_recs.append({
            "id": f"rec_{item.get('id', 'gen')}",
            "title": rec_title,
            "action": rec_action,
            "owner": "Operations Lead",
            "timeframe": "1-3 Weeks",
            "expected_impact": "15-20% variance reduction",
            "status": "pending"
        })
    if not default_recs:
        default_recs.append({
            "id": "rec_default_1",
            "title": "Establish Daily Operational Triage Cadence",
            "action": "Hold 15-minute daily standups to reallocate resources across high-volume stages.",
            "owner": "Service Delivery Manager",
            "timeframe": "Immediate (Week 1)",
            "expected_impact": "Stabilize queue volatility and eliminate backlog spikes.",
            "status": "approved"
        })
    st.session_state["recommendations_list"] = default_recs

recs = st.session_state.get("recommendations_list", [])

st.subheader(f"📋 Recommendation Review ({len(recs)} Items)")

for i, rec in enumerate(recs):
    with st.container():
        st.markdown(f"### Recommendation #{i+1}: {rec.get('title')}")
        
        status = rec.get("status", "pending")
        st_color = "green" if status == "approved" else ("red" if status == "rejected" else "orange")
        st.markdown(f"**Status:** :{st_color}[{status.upper()}]")
        
        c1, c2 = st.columns(2)
        with c1:
            rec['action'] = st.text_area(f"Action Detail", value=rec.get('action', ''), key=f"rec_act_{i}", height=80)
            rec['expected_impact'] = st.text_input(f"Expected Impact", value=rec.get('expected_impact', ''), key=f"rec_imp_{i}")
        with c2:
            rec['owner'] = st.text_input(f"Workstream Owner", value=rec.get('owner', 'Operations Manager'), key=f"rec_own_{i}")
            rec['timeframe'] = st.text_input(f"Timeframe / Effort", value=rec.get('timeframe', '2-4 Weeks'), key=f"rec_tf_{i}")
            
        b1, b2, b3 = st.columns([1, 1, 4])
        with b1:
            if st.button("✅ Accept", key=f"acc_rec_{i}", use_container_width=True):
                rec['status'] = "approved"
                st.session_state.audit_logger.log("ACCEPT_RECOMMENDATION", f"Accepted recommendation {rec.get('id')}", details={"id": rec.get("id"), "title": rec.get("title")})
                st.rerun()
        with b2:
            if st.button("❌ Reject", key=f"rej_rec_{i}", use_container_width=True):
                rec['status'] = "rejected"
                st.session_state.audit_logger.log("REJECT_RECOMMENDATION", f"Rejected recommendation {rec.get('id')}", details={"id": rec.get("id"), "title": rec.get("title")})
                st.rerun()
        with b3:
            if st.button("✏️ Save & Approve", key=f"save_rec_{i}"):
                rec['status'] = "approved"
                st.session_state.audit_logger.log("EDIT_APPROVE_RECOMMENDATION", f"Edited recommendation {rec.get('id')}", details={"id": rec.get("id")})
                st.success("Saved and approved!")
                st.rerun()
                
        st.markdown("---")

# Add new custom recommendation
with st.expander("➕ Add Custom Recommendation"):
    new_title = st.text_input("Intervention Title", placeholder="e.g. Implement Fast-Track Queue")
    new_action = st.text_area("Action Steps", placeholder="Specific operational steps...")
    new_owner = st.text_input("Accountable Owner", placeholder="e.g. Operations Director")
    new_impact = st.text_input("Expected Impact", placeholder="e.g. 25% cycle time reduction")
    new_tf = st.text_input("Timeframe", placeholder="e.g. 2 weeks")
    
    if st.button("Add & Approve Recommendation", type="primary"):
        if new_title and new_action:
            recs.append({
                "id": f"rec_custom_{len(recs)+1}",
                "title": new_title,
                "action": new_action,
                "owner": new_owner or "Operations Lead",
                "timeframe": new_tf or "2 Weeks",
                "expected_impact": new_impact or "Improved efficiency",
                "status": "approved"
            })
            st.session_state["recommendations_list"] = recs
            st.session_state.audit_logger.log("ADD_CUSTOM_RECOMMENDATION", f"Added recommendation: {new_title}")
            st.success("Custom recommendation added and approved!")
            st.rerun()
