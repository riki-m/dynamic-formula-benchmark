# Dynamic Intelligence Engine

## Purpose

This project follows the assignment by implementing the three required execution methods:

1. Python application-level processing
2. C#/.NET application-level processing
3. SQL Server dynamic execution

On top of those required engines, the project now includes a **dynamic local intelligence engine**. This layer does not execute formulas and does not replace any required method. Its job is to interpret measured benchmark outputs, answer benchmark questions, and generate report-quality analytical content.

## What The Intelligence Engine Reads

The intelligence engine works from the current measured benchmark data:

- formula metadata from `t_targil`
- measured runtime logs from `t_log`
- validated correctness status from the final pairwise comparison baseline

## What The Intelligence Engine Computes

The engine derives structured insights such as:

- fastest method overall
- slowest method overall
- performance spread between methods
- most stable method
- per-formula winners
- closest race and widest margin
- category-level winners for arithmetic, complex, and conditional formulas
- scenario-based recommendation matrix
- warning signals and interpretation notes
- question-specific answers through the `Ask the Benchmark` flow

## What The Intelligence Engine Produces

The final outputs are:

- an executive summary inside the dashboard
- generated intelligence cards
- warning and signal blocks
- category-level runtime interpretation
- scenario recommendations
- interactive benchmark Q&A
- a downloadable PDF report
- a persisted intelligence summary in `report/intelligence_summary.md`

## Why This Still Matches The Assignment

The assignment requires three concrete execution approaches and a comparison between them.

This design remains fully compliant because:

- the three required engines remain unchanged
- correctness is still measured from real executions
- performance is still measured from `t_log`
- the intelligence engine is only a reporting and interpretation layer

## Related Files

- [intelligence_summary.md](C:/Users/Mitelman/Documents/Codex/dynamic-formula-benchmark/report/intelligence_summary.md)
- [analysis_engine.py](C:/Users/Mitelman/Documents/Codex/dynamic-formula-benchmark/report-api/app/analysis_engine.py)
- [pdf_report_builder.py](C:/Users/Mitelman/Documents/Codex/dynamic-formula-benchmark/report-api/app/pdf_report_builder.py)
