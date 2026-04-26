# Repository Structure

This document mirrors the current repository layout and explains where each required submission artifact is located.

## Current Structure

```text
dynamic-formula-benchmark/
|-- csharp-solution/
|   |-- DynamicFormulaBenchmark.sln
|   `-- DynamicFormulaBenchmark/
|       |-- DynamicFormulaBenchmark.csproj
|       |-- Program.cs
|       |-- FormulaEngine.cs
|       |-- DatabaseService.cs
|       |-- ExpressionSyntaxTransformer.cs
|       `-- Models/
|           |-- FormulaDefinition.cs
|           `-- DataRecord.cs
|-- database/
|   |-- 01_schema.sql
|   |-- 02_seed_formulas.sql
|   |-- 04_seed_data_sqlserver.sql
|   `-- 05_compare_methods.sql
|-- docs/
|   |-- FORMULA_EVALUATION.md
|   |-- INTELLIGENCE_ENGINE.md
|   `-- SQL_SERVER_RUNBOOK.md
|-- python-solution/
|   |-- scripts/
|   |   |-- seed_data.py
|   |   |-- run_python_eval.py
|   |   |-- run_python_eval_sqlserver.py
|   |   `-- compare_results.py
|   `-- src/
|       |-- config.py
|       |-- db.py
|       |-- sqlserver_db.py
|       |-- formula_runtime.py
|       `-- syntax_transformer.py
|-- report/
|   |-- benchmark-ai-analysis.pdf
|   |-- intelligence_summary.md
|   |-- summary.md
|   `-- screenshots/
|       |-- t_data.jpg
|       |-- t_targil.jpg
|       |-- t_results.jpg
|       |-- t_log.jpg
|       |-- landing-navigation-dashboard.jpg
|       |-- overview-dashboard.jpg
|       |-- correctness-dashboard.jpg
|       |-- performance-dashboard.jpg
|       |-- formula-analysis-dashboard.jpg
|       |-- tradeoff-dashboard.jpg
|       |-- recommendation-dashboard.jpg
|       `-- intelligence-dashboard.jpg
|-- report-api/
|   |-- app/
|   |   |-- analysis_engine.py
|   |   |-- main.py
|   |   `-- pdf_report_builder.py
|   `-- export_public_snapshot.py
|-- report-ui/
|   |-- assets/
|   |   `-- benchmark-ai-analysis.pdf
|   |-- data/
|   |   `-- dashboard.json
|   |-- .nojekyll
|   |-- app.js
|   |-- index.html
|   `-- styles.css
|-- sql-solution/
|   |-- 03_dynamic_sql.sql
|   `-- README.md
|-- .gitignore
|-- index.html
|-- PROJECT_PLAN.md
|-- README.md
|-- REPOSITORY_STRUCTURE.md
`-- requirements.txt
```

## Folder Responsibilities

### `database`

Contains the shared schema, formula seed scripts, large-scale SQL Server data seed script, and the correctness comparison query.

### `python-solution`

Contains the Python implementation for dynamic formula execution, including data seeding, runtime evaluation through `eval()`, and comparison utilities.

### `csharp-solution`

Contains the .NET implementation that reads the same formulas and data contract and writes results in the same benchmark structure.

### `sql-solution`

Contains the SQL Server dynamic execution implementation and its supporting documentation.

### `docs`

Contains supporting technical explanations for formula translation, SQL Server execution order, and the local intelligence layer.

### `report`

Contains the final summary artifacts required for submission:

- `summary.md` for the written benchmark conclusion
- `intelligence_summary.md` for the analytical interpretation layer
- `benchmark-ai-analysis.pdf` for the generated technical report
- `screenshots/` for database evidence images

### `report-api`

Contains the FastAPI layer, the local benchmark intelligence logic, the PDF builder, and the snapshot exporter used for the static public website.

### `report-ui`

Contains the responsive benchmark dashboard UI and the public static snapshot assets used by GitHub Pages.

