import streamlit as st
import pandas as pd
from src.state import init_session_state, get_state, reset_analysis_only, reset_full_state
from src.export import load_app_config

st.set_page_config(
    page_title="Performance Insight Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_session_state()
config = load_app_config()

# Sidebar Assessment Context & Reset Controls
with st.sidebar:
    st.title("🎯 Assessment Hub")
    st.caption("Author: DARAMOLA OMOYELE | Performance Insight Explorer")
    
    st.markdown("---")
    st.subheader("📋 Assessment Context")
    with st.expander("Interview & Brief Context", expanded=True):
        st.session_state["assessment_question"] = st.text_area(
            "Assessment Question / Brief",
            value=st.session_state.get("assessment_question", ""),
            height=70,
            placeholder="e.g. Analyze backlogs and suggest 3 operational fixes..."
        )
        st.session_state["target_audience"] = st.text_input(
            "Target Audience",
            value=st.session_state.get("target_audience", "Senior Leadership"),
            placeholder="e.g. Operations Director, Team Leads"
        )
        st.session_state["output_format"] = st.selectbox(
            "Desired Output Format",
            ["Presentation Deck (PPTX)", "Executive Summary (Word/PDF)", "Live Briefing / Dashboard", "Analytical Memo"],
            index=0 if st.session_state.get("output_format") is None else ["Presentation Deck (PPTX)", "Executive Summary (Word/PDF)", "Live Briefing / Dashboard", "Analytical Memo"].index(st.session_state.get("output_format", "Presentation Deck (PPTX)"))
        )
        st.session_state["time_available"] = st.text_input(
            "Time Available / Presentation Length",
            value=st.session_state.get("time_available", "15 minutes"),
            placeholder="e.g. 10 mins presentation + 5 mins Q&A"
        )
        st.session_state["analyst_notes"] = st.text_area(
            "Analyst Working Notes / Scratchpad",
            value=st.session_state.get("analyst_notes", ""),
            height=60,
            placeholder="Key talking points or hypotheses..."
        )

    st.markdown("---")
    st.subheader("🔄 Safety & Reset Controls")
    if st.button("🧹 Reset Analysis Only", help="Clears mappings, metrics, and insights while keeping raw uploaded file intact.", use_container_width=True):
        reset_analysis_only()
        st.success("Analysis, mappings, and metrics reset safely. Raw dataset preserved.")
        st.rerun()
        
    if st.button("⚠️ Full State Reset", help="Clears everything including uploaded files.", use_container_width=True):
        reset_full_state()
        st.warning("Full session reset complete.")
        st.rerun()

# Main Landing Page
st.title("📊 Performance Insight Explorer")
st.markdown("### Pre-Interview Hardened Operational Performance & Diagnostic Toolkit")
st.caption("Designed for rapid, safe, and transparent operational dataset analysis under interview conditions.")

# Row Granularity Alert banner if data uploaded
if st.session_state.get("raw_df") is not None:
    st.info(f"📁 **Active Dataset:** {st.session_state.get('dataset_name', 'Uploaded File')} | **Rows:** {len(st.session_state['raw_df']):,} | **Columns:** {len(st.session_state['raw_df'].columns)}")
    
    granularity_status = st.session_state.get("row_granularity", "Not Confirmed")
    if granularity_status == "Not Confirmed" or not st.session_state.get("row_granularity_confirmed", False):
        st.warning(
            "⚠️ **ROW GRANULARITY REQUIRED:** Confirm what one row represents before interpreting rates, totals, or lifecycle metrics. "
            "Go to **01_Upload & Profile** to confirm row granularity."
        )
    else:
        st.success(f"✅ **Row Granularity Confirmed:** 1 Row = `{st.session_state['row_granularity']}`")

# Key Architectural Principles Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    #### 🛡️ Safe & Non-Destructive
    - Raw datasets remain untouched in memory
    - Safe division protects against zero-division errors
    - Automatic `.xls` (xlrd) and `.xlsx` (openpyxl) legacy ingestion
    """)

with col2:
    st.markdown("""
    #### 🧭 Target Directionality
    - Supports **Higher is better**, **Lower is better**, & **Neutral**
    - Processing times, backlog, and error rates correctly flagged
    - Dynamic variance commentary with zero-target guards
    """)

with col3:
    st.markdown("""
    #### 🎯 Human-in-the-Loop
    - Suggestions never auto-activate without analyst confirmation
    - Full **Accept / Edit / Reject** workflow for insights & recommendations
    - Standalone **Interview View** for rapid executive defense
    """)

st.markdown("---")
st.subheader("🚀 Quick Start Workflow")
st.markdown("""
1. **01 Upload & Profile:** Upload `.csv`, `.xlsx`, or legacy `.xls`. Set and confirm **Row Granularity**.
2. **02 Data Cleaning:** Review data hygiene, missingness, and safe numeric type conversions.
3. **03 Column Mapping:** Review auto-detected semantic roles, confirm mappings, and set **Target Directionality**.
4. **04 - 07 Analysis:** Inspect Overview, Trends, Driver Trees, and Operational Cohorts.
5. **08 & 09 Insights & Recommendations:** Accept, edit, or reject diagnostic findings.
6. **10 Interview View:** Review executive slide outlines, talking points, and Q&A defense.
7. **11 Export:** Download custom PowerPoint deck, sanitized audit trail, or Excel pack.
""")
