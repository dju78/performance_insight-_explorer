# Performance Insight Explorer

**Enterprise Performance Analysis, Diagnostic and Decision-Support Platform**  
*Production-Quality, Multi-Sector Operational Decision-Support & Diagnostic System*

- **Live Production App:** [https://performance-insight-explorer.streamlit.app](https://performance-insight-explorer.streamlit.app)
- **GitHub Repository:** [https://github.com/dju78/performance_insight-_explorer](https://github.com/dju78/performance_insight-_explorer)
- **Product Owner / Lead Architect:** DARAMOLA OMOYELE  
- **Version:** 2.0.0 (`v2.0-enterprise-platform`)  
- **License:** MIT / Enterprise Operational Analysis

---

## 🌟 Overview & Dual-Mode Positioning

**Performance Insight Explorer** is an enterprise-grade, schema-flexible operational performance analysis and decision-support platform built with Python and Streamlit.

The platform supports two distinct operational modes:
1. **Organization Mode (Default):** Complete end-to-end performance analysis lifecycle, dynamic no-code KPI builder, 10-dimension data quality engine, Shewhart statistical process control (SPC) charts, multivariate root-cause driver modeling, evidence-based insight curation, Impact $\times$ Effort recommendation matrix, action tracking, scenario forecasting, and enterprise governance.
2. **Assessment Mode:** Preserves timed practical assessment intakes, prompt cards, executive interview summaries, and assessor Q&A defense.

---

## 🔄 End-to-End Performance Analysis Lifecycle

The platform guides users through an auditable, rigorous 15-stage operational lifecycle:

$$\text{Define Question} \rightarrow \text{Ingest \& Profile} \rightarrow \text{Confirm Granularity} \rightarrow \text{10D Quality QA} \rightarrow \text{Semantic Mapping} \rightarrow \text{KPI Configuration} \rightarrow \text{Method Selection} \rightarrow \text{Overview Scorecard} \rightarrow \text{SPC Trends} \rightarrow \text{RCA Diagnostics} \rightarrow \text{Uncertainty Review} \rightarrow \text{Evidence Insights} \rightarrow \text{Prioritized Recs} \rightarrow \text{Action Tracking} \rightarrow \text{Governance \& Export}$$

---

## 🏛️ Multi-Sector Enterprise Application

Works out-of-the-box across diverse operational sectors without assuming rigid column schemas:
- **Healthcare & Social Care:** Emergency Department triage, wait times, bed occupancy, doctor FTE, 4-hour SLA attainment.
- **Sales & Commercial Operations:** Inbound leads, SDR capacity, conversion rate %, deal cycle duration, target vs actual revenue.
- **Customer Service Operations:** Omnichannel ticket inflow, First Contact Resolution (FCR %), CSAT scores, agent utilization, backlog inventory.
- **Human Resources & Workforce:** Department headcount, sick absence rates, voluntary turnover %, vacancy rates, recruitment expenditure.
- **Local Government & Public Services:** Planning applications received, statutory 8-week determination %, case officer caseloads.
- **General Business Operations & Manufacturing:** Production throughput, machine capacity utilization, cycle time, scrap/rework rates.

---

## 🛡️ Key Enterprise Features & Defenses

1. **10-Dimension Data Quality Engine:** Evaluates Completeness, Validity, Accuracy, Consistency, Uniqueness, Timeliness, Integrity, Conformity, Coverage, and Plausibility with analysis-blocking triggers for critical issues and interactive remediation (Accept, Exclude, Flag, Justify, Clean).
2. **Dynamic No-Code KPI Builder:** Configure custom metrics, numerators/denominators, 12 aggregation methods, target directionalities (Higher is Better, Lower is Better, Target Range, Exact Target, Informational), warning/critical thresholds, and safe zero-denominator arithmetic.
3. **Statistical & Diagnostic Depth:** Shewhart SPC run charts ($\pm 3\sigma$ control limits), ANOVA between-group significance ($p$-values), Cohen's $d$ effect sizes, Pareto 80/20 curves, multivariate OLS regression driver importance ($R^2$), 5-Whys trees, and Ishikawa Fishbone categories.
4. **Impact × Effort Prioritization & Traceability:** Formulates Quick Wins, Strategic Initiatives, Investigations, and Monitoring actions with non-prescriptive wording safeguards and a full traceability chain ($\text{Data} \rightarrow \text{Calculation} \rightarrow \text{Finding} \rightarrow \text{Recommendation} \rightarrow \text{Action} \rightarrow \text{Outcome}$).
5. **Action Tracking & Benefits Realization:** Track assigned actions (Owner, Due Date, Status, Baseline vs Expected vs Actual) with explicit causality caveat disclosures.
6. **Operational Scenario Simulator:** Model what-if demand volume, staffing/FTE, and productivity adjustments with baseline, optimistic, and conservative trajectory projections.
7. **Security & Privacy Safeguards:** Protection against spreadsheet formula injection (CWE-1236 escaping leading `=`, `+`, `-`, `@`), small-cell statistical suppression ($n < 5$ disclosure control), RBAC permissions, and tamper-evident SHA-256 audit chaining.
8. **Multi-Format Reporting:** Generates PowerPoint presentation decks (16:9), ReportLab PDF briefing memos, sanitized multi-tab Excel evidence workbooks, and Markdown summaries.

---

## 🚀 Quick Start (Local Setup)

```powershell
# 1. Clone repository
git clone https://github.com/dju78/performance_insight-_explorer.git
cd "performance analysis"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run automated tests (130 tests)
python -m pytest

# 4. Launch Streamlit Application
streamlit run app.py
```

---

## 📁 Repository Structure

```
├── app.py                         # Unified Dual-Mode Entry Point
├── core/
│   ├── constants.py               # Enums (Modes, Roles, Stages, Severities)
│   ├── models.py                  # Dataclasses (KPIs, Quality, Insights, Recs, Actions)
│   ├── security.py                # Formula injection sanitizer, suppression, RBAC, audit hashing
│   └── state.py                   # Centralized Session State & Project Bundle Save/Resume
├── modules/
│   ├── ingestion/                 # CSV, Excel, Parquet, JSON, chunking & transformation log
│   ├── profiling/                 # Cardinality, granularity heuristics, memory estimate
│   ├── quality/                   # 10-Dimension Data Quality Engine & remediation
│   ├── mapping/                   # 25+ Semantic Roles & statistical confidence inferrer
│   ├── kpi_engine/                # Dynamic formula evaluator & RAG directionality
│   ├── analysis/                  # Descriptive stats, SPC run charts, ANOVA, Pareto
│   ├── diagnostics/               # 10-Step RCA, driver correlations, regression importance
│   ├── forecasting/               # Scenario simulator & what-if capacity planner
│   ├── insights/                  # Deterministic evidence insight engine
│   ├── recommendations/           # Impact-Effort matrix & end-to-end traceability
│   ├── actions/                   # Action registry & benefits realization tracker
│   └── reporting/                 # Multi-format report builder (PPTX, PDF, Excel, MD)
├── pages/                         # Streamlit multi-page UI (Stages 01 through 12)
├── sample_data/                   # 5 Multi-sector synthetic datasets
└── tests/                         # Comprehensive pytest test suite (130 tests passing)
```

---

*Authored and architected by **Daramola Omoyele**.*
