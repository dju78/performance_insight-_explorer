# Performance Insight Explorer

**Operational Performance • Data Quality • Analysis • Insight**  
*Production-Quality, Schema-Flexible Operational Decision-Support Application*

**Author:** DARAMOLA OMOYELE  
**Version:** 1.0.0  
**License:** MIT / Internal Performance Assessment

---

## 🌟 Overview & Purpose

**Performance Insight Explorer** is a schema-flexible, offline-first operational analytics application built in Python and Streamlit. It is engineered specifically to accept unfamiliar operational datasets (CSV, XLS, XLSX) with arbitrary column names, automatically profile structural properties, execute a rigorous 6-dimension data quality scan, facilitate user-confirmed role mapping, calculate guarded performance KPIs, identify trends and anomalies, and export executive PowerPoint presentations, PDF briefings, and multi-tab Excel workbooks.

---

## 📋 Practical Assessment Workflow

The application supports multi-dataset ingestion, assessment brief extraction, relationship joins, and automated benchmark verification:

### 14-Step User Workflow

1. **Upload `Question1.docx` as Assessment Brief** (Page 01: extracted as business requirements, never profiled as tabular data).
2. **Upload `performance.xlsx` as Primary Analysis Dataset** (Page 01: select sheet `Performance Data`).
3. **Upload `Users.xlsx` as Reference / Master Dataset** (Page 01: select sheet `Users`).
4. **Confirm Performance granularity:** `Periodic Snapshot (1 row = 1 User for 1 Reporting Month)`.
5. **Confirm Users granularity:** `Reference / Master Record (1 row = 1 User)`.
6. **Create relationship:** `performance.User -> Users.User` (Left Join).
7. **Confirm 100% relationship QA:** Validate match coverage, unmatched rows, and duplicate keys.
8. **Review Data Quality** (Page 02: structural & semantic checks).
9. **Confirm Column Mapping** (Page 03: semantic roles and target directionality).
10. **Review Performance Overview** (Page 04: scorecard metrics).
11. **Review Trends and Comparisons** (Pages 05 & 06: longitudinal and cohort variance).
12. **Review Insights and Recommendations** (Pages 08 & 09: diagnostic findings and action matrix).
13. **Open Interview View** (Page 10: Q1–Q5 verification, prompt cards, and executive memo).
14. **Export required outputs** (Page 11: PowerPoint, PDF briefing, Excel pack, and Text memo).

### Verified Assessment Benchmarks (Regression Baseline)

| Metric / Checkpoint | Expected Assessment Value | Verified Model Result |
| :--- | :--- | :--- |
| **Performance Dataset Rows** | `2,539` | `2,539` |
| **Users Reference Dataset Rows** | `309` | `309` |
| **Relationship Match Coverage** | `100.0%` | `100.0%` (2,539 / 2,539 rows) |
| **Unmatched / Orphan Users** | `0` | `0` |
| **Duplicate Master Keys** | `0` | `0` |
| **Q3 Condition** | `Service == "Service A" & Band == 3` | Evaluated (856 matches / 33.7%) |
| **Q4 Valid Observations** | `796` (2025, Service B, Band 3 & 5) | `796` |
| **Q4 Average Availability %** | `≈ 78.91%` | `78.9079%` (`78.91%`) |
| **Q4 Median Availability %** | `≈ 85.05%` | `85.0513%` (`85.05%`) |
| **Q5 Jan 2025 Availability %** | `≈ 75.93%` (Service B, Band 3) | `75.9288%` (`75.93%`) |
| **Q5 Feb 2025 Availability %** | `≈ 84.26%` (Service B, Band 3) | `84.2556%` (`84.26%`) |

---

## 🔑 Key Engineering Principles

1. **Schema Flexibility (Zero Hard-Coding):** Works on conceptual analytical roles (`record_id`, `date`, `team`, `actual`, `target`, `received`, `completed`, `opening_backlog`, `closing_backlog`, `fte`, `hours_used`, `hours_available`, `processing_time`, etc.) rather than rigid column names.
2. **Non-Destructive Data Preservation:** The pristine raw uploaded dataset is preserved untouched. Observations are never silently mutated, deleted, or fabricated.
3. **Safe Mathematical Guardrails:** All metric calculations are protected against division-by-zero (`safe_divide`), returning `NaN` or controlled representations.
4. **Transparent Calculation Tracing:** Every metric card displays its explicit mathematical formula, interpretation guidelines, and denominator origin. Estimated flow measures (e.g. Net Flow) are clearly flagged.
5. **No False Causation:** Statistical associations (Pearson & Spearman correlations) include prominent disclaimers emphasizing that correlation does not establish causation.
6. **100% Offline-First Privacy:** All file ingestion, profiling, chart rendering, and presentation generation execute locally without external cloud APIs.

---

## 🚀 Quick Start (Windows)

### Option 1: One-Click Setup & Launch
1. Run **`setup_windows.bat`** to create the virtual environment and install all dependencies:
   ```cmd
   setup_windows.bat
   ```
2. Launch the application using **`run_windows.bat`**:
   ```cmd
   run_windows.bat
   ```

### Option 2: Manual Terminal Commands
```powershell
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Streamlit
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

---

## 📁 Project Architecture & Directory Structure

```text
performance_insight_explorer/
│
├── app.py                         # Main Streamlit landing & orchestrator
├── requirements.txt               # Pinned Python package dependencies
├── README.md                      # Complete system documentation
├── CHANGELOG.md                   # Chronological version changelog
├── USER_GUIDE.md                  # Step-by-step user and assessment guide
├── setup_windows.bat              # Automated Windows setup script
├── run_windows.bat                # Automated Windows launch script
│
├── pages/                         # Streamlit multi-page interface (12 pages)
│   ├── 01_upload_profile.py       # File ingestion, multi-dataset hub & relationships
│   ├── 02_data_quality.py         # 6-dimension QA scan & issue tracker
│   ├── 03_column_mapping.py       # AI-assisted role mapping interface
│   ├── 04_performance_overview.py # Headline KPI dashboard & gauge
│   ├── 05_trends.py               # Time-series dynamics & trajectories
│   ├── 06_comparisons.py          # Ranked segment comparisons & normalisation
│   ├── 07_root_cause.py           # 5-Pillar workspace & correlation matrix
│   ├── 08_insights.py             # 6-part structured insight cards
│   ├── 09_recommendations.py      # Action plan & Governance registers
│   ├── 10_interview_view.py       # Q1-Q5 verification & oral briefing mode
│   ├── 11_export.py               # PowerPoint, PDF & Excel export generators
│   └── 12_audit_trail.py          # Real-time session event logger
│
├── src/                           # Reusable core analytical engine
│   ├── __init__.py                # Package root
│   ├── brief_extractor.py         # Assessment brief requirements extractor
│   ├── relationships.py           # Multi-dataset join & relationship QA engine
│   ├── ingestion.py               # Safe CSV/XLS/XLSX file loader
│   ├── profiling.py               # Structural statistics & type inference
│   ├── quality.py                 # Multi-dimensional Data Quality engine
│   ├── mapping.py                 # Keyword heuristics & role catalogue
│   ├── metrics.py                 # Guarded mathematical KPI calculations
│   ├── trends.py                  # Chronological time-series engine
│   ├── comparisons.py             # Cross-group aggregation & rate calculator
│   ├── root_cause.py              # 5-Pillar diagnostics & correlations
│   ├── insights.py                # Traceable 6-part structured insight cards
│   ├── recommendations.py         # Action matrix, Assumptions & Limitations
│   ├── visualisations.py          # Publication-ready Plotly chart builders
│   ├── powerpoint.py              # 6-slide python-pptx presentation deck
│   ├── pdf_report.py              # ReportLab PDF executive brief generator
│   ├── reporting.py               # Multi-worksheet openpyxl Excel exporter
│   ├── audit.py                   # Thread-safe audit event logger
│   └── state.py                   # Streamlit session state controller
│
├── config/                        # Declarative system configurations
│   ├── metric_definitions.yaml    # KPI formulas, units, and interpretations
│   ├── mapping_patterns.yaml      # Synonym keywords & role metadata
│   └── settings.yaml              # Application thresholds and settings
│
├── sample_data/                   # Realistic synthetic test datasets
│   ├── dataset_a_team_month.csv   # Aggregated team-month operational data
│   ├── dataset_a_team_month.xlsx  # Multi-sheet Excel version of Dataset A
│   ├── dataset_b_case_level.csv   # Granular case-level operational registry
│   ├── dataset_b_case_level.xlsx  # Excel version of Dataset B
│   ├── dataset_c_poor_quality.csv # Deliberately faulty data for QA testing
│   └── dataset_c_poor_quality.xlsx# Excel version of Dataset C
│
├── tests/                         # Comprehensive Pytest automated test suite
│   ├── test_ingestion.py          # Tests for CSV, XLSX, encoding handling
│   ├── test_profiling.py          # Tests for structural type inference
│   ├── test_mapping.py            # Tests for heuristic mapping & validation
│   ├── test_quality.py            # Tests for QA anomaly detection
│   ├── test_metrics.py            # Tests for guarded KPI formulas & zero-div
│   ├── test_trends.py             # Tests for time-series diffs & directions
│   ├── test_comparisons.py        # Tests for group ranking & sample size flags
│   ├── test_powerpoint.py         # Tests for 6-slide PPTX generation
│   ├── test_reporting.py          # Tests for multi-worksheet Excel workbook
│   ├── test_edge_cases.py         # Tests for empty, single-row, zero-denom data
│   ├── test_audit_and_insights.py # Tests for audit logger, root cause, insights
│   ├── test_multi_dataset_relationships.py # Multi-dataset & relationship QA tests
│   └── test_all_pages_execution.py# Compilation and page execution verification
│
├── docs/                          # Controlling project documentation
└── outputs/                       # Destination for generated deliverables
    ├── presentations/             # Generated .pptx presentation decks
    ├── reports/                   # Generated .xlsx summary workbooks
    ├── briefs/                    # Generated .pdf executive briefings
    ├── charts/                    # Exported chart assets
    └── audit/                     # Exported session audit logs
```

---

## 🧪 Automated Testing & Verification

Run the full automated test suite using `pytest`:
```bash
python -m pytest -v
```

All 110 unit, integration, edge-case, relationship, and end-to-end pipeline tests run locally without network dependencies.

---

## 📊 Deliverables & Export Locations

- **PowerPoint Decks:** Saved to `outputs/presentations/`
- **PDF Briefings:** Saved to `outputs/briefs/`
- **Excel Summaries:** Saved to `outputs/reports/`
- **Audit Trails:** Saved to `outputs/audit/` or downloaded directly via the UI.

---

## 👤 Product Owner & Author
**DARAMOLA OMOYELE**  
*Performance Insight Explorer v1.0.0*
