# Performance Insight Explorer

**Operational Performance • Data Quality • Analysis • Insight**  
*Production-Quality, Schema-Flexible Operational Decision-Support Application*

**Author:** DARAMOLA OMOYELE  
**Version:** 1.0.0  
**License:** MIT / Internal Performance Assessment

---

## 🌟 Overview & Purpose

**Performance Insight Explorer** is a schema-flexible, offline-first operational analytics application built in Python and Streamlit. It is engineered specifically to accept unfamiliar operational datasets (CSV, XLS, XLSX) with arbitrary column names, automatically profile structural properties, execute a rigorous 6-dimension data quality scan, facilitate user-confirmed role mapping, calculate guarded performance KPIs, identify trends and anomalies, and export executive 6-slide PowerPoint presentations and multi-tab Excel workbooks.

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
│   ├── 01_upload_profile.py       # File ingestion & structural profile
│   ├── 02_data_quality.py         # 6-dimension QA scan & issue tracker
│   ├── 03_column_mapping.py       # AI-assisted role mapping interface
│   ├── 04_performance_overview.py # Headline KPI dashboard & gauge
│   ├── 05_trends.py               # Time-series dynamics & trajectories
│   ├── 06_comparisons.py          # Ranked segment comparisons & normalisation
│   ├── 07_root_cause.py           # 5-Pillar workspace & correlation matrix
│   ├── 08_insights.py             # 6-part structured insight cards
│   ├── 09_recommendations.py      # Action plan & Governance registers
│   ├── 10_interview_view.py       # Concise 1-page oral briefing mode
│   ├── 11_export.py               # PowerPoint & Excel export generators
│   └── 12_audit_trail.py          # Real-time session event logger
│
├── src/                           # Reusable core analytical engine
│   ├── __init__.py                # Package root
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
│   └── test_end_to_end.py         # Full integration workflow pipeline test
│
├── docs/                          # Controlling project documentation
└── outputs/                       # Destination for generated deliverables
    ├── presentations/             # Generated .pptx presentation decks
    ├── reports/                   # Generated .xlsx summary workbooks
    ├── charts/                    # Exported chart assets
    └── audit/                     # Exported session audit logs
```

---

## 🧪 Automated Testing & Verification

Run the full automated test suite using `pytest`:
```bash
python -m pytest -v
```

All unit, integration, edge-case, and end-to-end pipeline tests run locally without network dependencies.

---

## 📊 Deliverables & Export Locations

- **PowerPoint Decks:** Saved to `outputs/presentations/performance_insight_YYYYMMDD_HHMMSS.pptx`
- **Excel Summaries:** Saved to `outputs/reports/performance_analysis_summary_YYYYMMDD_HHMMSS.xlsx`
- **Audit Trails:** Saved to `outputs/audit/` or downloaded directly via the UI.

---

## 👤 Product Owner & Author
**DARAMOLA OMOYELE**  
*Performance Insight Explorer v1.0.0*
