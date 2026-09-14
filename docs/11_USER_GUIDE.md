# Performance Insight Explorer - User & Assessment Guide

**Author:** DARAMOLA OMOYELE  
**Version:** 1.0.0

---

## 🎯 60-Minute Assessment Workflow Guide

When an unfamiliar assessment dataset arrives, follow this structured 60-minute roadmap:

| Phase | Time | Action | Key Application Page |
|---|---|---|---|
| **1. Understand & Ingest** | 00–10 min | Review mandate, upload file, select sheet, review structural profile. | `01_upload_profile.py` |
| **2. Quality Assurance** | 10–20 min | Inspect Critical & Warning QA issues, check duplicate IDs, note missingness. | `02_data_quality.py` |
| **3. Role Mapping** | 20–25 min | Map source columns to analytical roles, confirm mappings, verify activated KPIs. | `03_column_mapping.py` |
| **4. Performance Baseline** | 25–35 min | Inspect Headline KPIs, target achievement gauge, and calculation traces. | `04_performance_overview.py` |
| **5. Trends & Comparisons** | 35–45 min | Inspect period changes, peaks/troughs, ranked team comparisons & normalised rates. | `05_trends.py` & `06_comparisons.py` |
| **6. Root Cause Diagnostics** | 45–50 min | Inspect 5 operational pillars (Demand, Capacity, Process, Complexity, QA) & correlations. | `07_root_cause.py` |
| **7. Synthesize & Govern** | 50–55 min | Review structured insight cards, action matrix, record assumptions & limitations. | `08_insights.py` & `09_recommendations.py` |
| **8. Present & Export** | 55–60 min | Deliver briefing from Interview View, export 6-slide PowerPoint & Excel workbook. | `10_interview_view.py` & `11_export.py` |

---

## 🗣️ Verbal Interview Answer Structure

When presenting findings to assessors or executive stakeholders, follow the 6-part verbal template:

> **"Purpose → Data Quality & Method → Key Finding → Why It Matters → Recommendation → Limitation & Next Steps"**

### Example Verbal Response:
> *"Our objective was to evaluate operational throughput across the 4 delivery teams. The data quality audit confirmed high reliability (Health Score 92/100) with zero duplicate records. Across the 12-month period, overall target achievement was 102.5%, but we observed significant inter-team variation: Team Alpha delivered 32 cases per FTE while Team Gamma achieved 24 cases per FTE. This variance matters because Team Gamma's backlog has expanded by 45 cases, creating SLA breach risks. We recommend dynamically rebalancing intake demand toward Team Alpha's available capacity while investigating whether Team Gamma handled a higher proportion of complex inspections. As a key analytical caveat, our findings demonstrate association rather than proven causation, so we recommend reviewing case complexity mix before making structural staffing changes."*

---

## 📌 Handling Critical Edge Cases

1. **Missing Backlog Fields:**
   - If Opening and Closing Backlog are absent, map `Cases Received` and `Cases Completed`.
   - The system automatically calculates **Estimated Net Flow Pressure** (`Received - Completed`) and marks it as an estimated measure.
2. **Zero Denominators:**
   - If `Target = 0` or `FTE = 0`, the KPI engine guards the calculation using `safe_divide` and outputs `NaN` with a warning rather than failing or showing infinity.
3. **Small Sample Sizes:**
   - The comparison engine automatically highlights teams or categories with fewer than 5 observations (`is_small_sample: True`) to prevent misleading rankings.

---

## 💾 Deliverables & Output Files

- **PowerPoint:** `outputs/presentations/performance_insight_YYYYMMDD_HHMMSS.pptx`
- **Excel Summary:** `outputs/reports/performance_analysis_summary_YYYYMMDD_HHMMSS.xlsx`
- **Audit Trail:** `outputs/audit/` and downloadable CSV in `12_audit_trail.py`
