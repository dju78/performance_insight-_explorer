# Architectural Decision Log

| Date | Decision | Reason | Alternatives Considered | Impact | Owner |
|---|---|---|---|---|---|
| 2026-09-14 | Schema-flexible role mapping architecture | Live assessment dataset schema is unknown before receipt | Hardcoding fixed BSR column names | Complete adaptability to any operational dataset | Daramola Omoyele |
| 2026-09-14 | Non-destructive data preservation | Ensure transparent evidence audit trail and governance integrity | In-place dataframe cleaning / imputation | Raw data remains untouched; QA flags inform analyst judgement | Daramola Omoyele |
| 2026-09-14 | `safe_divide` zero-denominator protection | Prevent mathematical crashes / infinities on zero-target rows | Unprotected division / try-except skips | Robust handling of inactive periods without application crash | Daramola Omoyele |
| 2026-09-14 | Clear labelling of Estimated Net Flow | Distinguish inferred flow pressure from observed backlog inventory | Presenting net flow as true backlog | Avoids misleading executive stakeholders regarding inventory state | Daramola Omoyele |
| 2026-09-14 | Non-causation disclaimers on correlation | Statistical association does not prove operational causation | Automated causal inference claims | Defensible analytical governance during assessments | Daramola Omoyele |
| 2026-09-14 | 100% Offline-first local execution | Ensure data privacy, zero API reliance, and standalone Windows execution | Cloud-based LLM / API calls | Fully reliable execution in isolated assessment environments | Daramola Omoyele |
