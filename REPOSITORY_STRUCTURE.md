# Recommended Project Structure

```text
dynamic-formula-benchmark/
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- .github/
|   `-- workflows/
|       `-- deploy-pages.yml
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
`-- report/
    |-- summary.md
    `-- screenshots/
```

## Folder Responsibility

### `database`

Contains the shared schema, seed scripts, and comparison scripts.

### `python-solution`

Contains the first full implementation:

- data generation
- runtime evaluation via `eval`
- result comparison

### `csharp-solution`

Contains the .NET implementation that reads the same tables and writes the same result format.

### `sql-solution`

Contains the third required execution implementation:

- SQL Server dynamic execution
- stored procedure creation script
- dedicated SQL solution documentation

### `docs`

Contains technical explanations that support the submission, especially how formula strings are converted into executable runtime expressions.

### `report-api`

Contains the local API layer and the snapshot export utility used to build the free public GitHub Pages version.

### `report-ui`

Contains the final responsive dashboard that visualizes:

- correctness validation
- performance comparison
- per-formula runtime analysis
- architectural trade-offs
- final recommendation
- AI-assisted benchmark interpretation
- public static snapshot assets for GitHub Pages

### `.github/workflows`

Contains the GitHub Actions workflow that deploys the static showcase dashboard to GitHub Pages.

### `report`

Contains the final benchmark summary, the persisted intelligence summary, and screenshots for submission.

## Recommended README Sections

1. Project overview
2. Problem statement
3. Technologies
4. Project structure
5. How to run
6. Benchmark methods
7. Results
8. Conclusion
