# Dynamic Formula Calculation Benchmark

This repository benchmarks multiple runtime formula execution strategies for payment calculations. The same formulas are stored in the database and executed by three different engines so that correctness and performance can be compared fairly.

## Solutions Included

- `python_eval`: Python dynamic evaluation of formulas loaded from the database
- `csharp_engine`: C# runtime evaluation implementation for the same formulas
- `sql_dynamic`: SQL Server dynamic SQL execution using formulas stored in the database

## Shared Database Contract

All methods use the same tables:

- `t_data`
- `t_targil`
- `t_results`
- `t_log`

This shared contract is what makes the benchmark comparable. Every method reads the same input formulas and data, and writes results in the same structure.

## Repository Structure

```text
dynamic-formula-benchmark/
|-- database/
|   |-- 01_schema.sql
|   |-- 02_seed_formulas.sql
|   |-- 04_seed_data_sqlserver.sql
|   `-- 05_compare_methods.sql
|-- python-solution/
|   |-- scripts/
|   |   |-- seed_data.py
|   |   |-- run_python_eval.py
|   |   `-- compare_results.py
|   `-- src/
|       |-- config.py
|       |-- db.py
|       `-- formula_runtime.py
|-- csharp-solution/
|   |-- DynamicFormulaBenchmark.sln
|   `-- DynamicFormulaBenchmark/
|       |-- DynamicFormulaBenchmark.csproj
|       |-- Program.cs
|       |-- FormulaEngine.cs
|       |-- DatabaseService.cs
|       `-- Models/
|           |-- FormulaDefinition.cs
|           `-- DataRecord.cs
|-- sql-solution/
|   |-- 03_dynamic_sql.sql
|   `-- README.md
|-- docs/
|   |-- FORMULA_EVALUATION.md
|   |-- INTELLIGENCE_ENGINE.md
|   `-- SQL_SERVER_RUNBOOK.md
|-- .github/
|   `-- workflows/
|       `-- deploy-pages.yml
|-- report-api/
|   |-- app/
|   |   `-- main.py
|   `-- export_public_snapshot.py
|-- report-ui/
|   |-- index.html
|   |-- styles.css
|   |-- app.js
|   |-- data/
|   |   `-- dashboard.json
|   `-- assets/
|       `-- benchmark-ai-analysis.pdf
|-- .gitignore
|-- PROJECT_PLAN.md
|-- README.md
|-- REPOSITORY_STRUCTURE.md
`-- requirements.txt
```

## Where Formula Compilation Happens

The project does not build a compiler from scratch. Instead, each solution feeds the formula text into an existing runtime evaluator:

- In Python, `eval()` is the runtime evaluator. A translation layer normalizes syntax such as `^` to `**` and maps `if(condition, x, y)` to Python ternary syntax.
- In C#, `DynamicExpresso` is the runtime evaluator. A translation layer maps DB syntax to a C# expression syntax such as `condition ? x : y`.
- In SQL Server, `sp_executesql` compiles and executes the dynamic statement inside the database engine.

Important precision:

- The system can support any formula that is valid for the target execution engine after syntax translation.
- That does not literally mean every mathematical expression in the world with zero rules.
- It means formulas remain data-driven: when a new valid formula is inserted into `t_targil`, the application can execute it without changing source code or recompiling the application.

More detail is documented in [docs/FORMULA_EVALUATION.md](./docs/FORMULA_EVALUATION.md).

## Python Workflow

Install dependencies:

```bash
pip install -r requirements.txt
```

Seed data:

```bash
python python-solution/scripts/seed_data.py --rows 1000000
```

Run the first benchmark method:

```bash
python python-solution/scripts/run_python_eval.py
```

What the Python worker already does:

- loads formulas from `t_targil`
- transforms DB syntax into Python syntax
- precompiles each transformed expression once per formula
- streams `t_data` in batches
- writes results to `t_results`
- writes runtime and `records_processed` to `t_log`

Compare two methods:

```bash
python python-solution/scripts/compare_results.py --base-method python_eval --compare-method sql_dynamic
```

For a quick local test:

```bash
python python-solution/scripts/seed_data.py --rows 1000
python python-solution/scripts/run_python_eval.py
```

## Database Scripts

- Schema: [database/01_schema.sql](./database/01_schema.sql)
- Sample formulas: [database/02_seed_formulas.sql](./database/02_seed_formulas.sql)
- SQL Server dynamic method: [sql-solution/03_dynamic_sql.sql](./sql-solution/03_dynamic_sql.sql)
- SQL Server 1M seed script: [database/04_seed_data_sqlserver.sql](./database/04_seed_data_sqlserver.sql)
- SQL Server comparison query: [database/05_compare_methods.sql](./database/05_compare_methods.sql)

## SQL Server Execution Guide

The full SQL Server run order is documented in [docs/SQL_SERVER_RUNBOOK.md](./docs/SQL_SERVER_RUNBOOK.md).

This includes:

- schema creation
- formula seeding
- 1M record seeding
- Python worker execution against SQL Server
- stored procedure execution for `sql_dynamic`
- method comparison

## Reporting API

A lightweight FastAPI sample is included at [report-api/app/main.py](./report-api/app/main.py).

Example endpoints:

- `GET /health`
- `GET /api/logs`
- `GET /api/summary`
- `GET /api/dashboard`

## Benchmark Dashboard UI

The final responsive dashboard UI is implemented in:

- [report-ui/index.html](./report-ui/index.html)
- [report-ui/styles.css](./report-ui/styles.css)
- [report-ui/app.js](./report-ui/app.js)

To run the API and UI together against SQL Server:

```bash
$env:DB_ENGINE="sqlserver"
$env:SQLSERVER_CONNECTION_STRING="Driver={ODBC Driver 17 for SQL Server};Server=localhost\SQLEXPRESS;Database=DynamicFormulaBenchmark;Trusted_Connection=yes;TrustServerCertificate=yes;"
python -m uvicorn report-api.app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

The dashboard presents:

- benchmark overview
- correctness validation
- performance comparison
- formula-level analysis
- architectural trade-offs
- final recommendation
- dynamic benchmark intelligence analysis
- generated executive findings and warnings
- downloadable PDF report generated from measured benchmark data

## Free Public Website Deployment

This repository is also prepared for a free public showcase deployment through GitHub Pages.

How it works:

- the live local version uses FastAPI + SQL Server
- the public GitHub Pages version uses a static snapshot generated from the measured benchmark data
- the dashboard still presents the real benchmark outputs, charts, findings, and downloadable PDF report

To refresh the public snapshot before pushing:

```bash
$env:DB_ENGINE="sqlserver"
$env:SQLSERVER_CONNECTION_STRING="Driver={ODBC Driver 17 for SQL Server};Server=localhost\SQLEXPRESS;Database=DynamicFormulaBenchmark;Trusted_Connection=yes;TrustServerCertificate=yes;"
python report-api/export_public_snapshot.py
```

Then push to GitHub. The workflow in [.github/workflows/deploy-pages.yml](./.github/workflows/deploy-pages.yml) deploys the contents of [report-ui](./report-ui) to GitHub Pages.

Important:

- this public site is a showcase deployment, not a live cloud SQL Server environment
- it is intentionally snapshot-based so it can be hosted for free and shared with examiners or reviewers
- the snapshot is generated directly from your measured benchmark data before deployment

## Dynamic Benchmark Intelligence Layer

A local intelligence layer is included for benchmark interpretation, report generation, and presentation polish.

It does not replace any required execution method.
It recomputes analysis directly from measured SQL Server benchmark outputs and generates:

- executive summaries
- ranked findings
- warning signals
- category-level observations
- scenario-based recommendations
- downloadable PDF reports

Files:

- [docs/INTELLIGENCE_ENGINE.md](./docs/INTELLIGENCE_ENGINE.md)
- [report/intelligence_summary.md](./report/intelligence_summary.md)

## Recommended Submission Story

1. Create the schema and seed formulas.
2. Generate the test data.
3. Run `python_eval`.
4. Implement and run `sql_dynamic`.
5. Implement and run `csharp_engine`.
6. Compare all methods using the same result schema.
7. Summarize runtime and correctness in the final report.
