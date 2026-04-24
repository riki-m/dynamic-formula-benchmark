# SQL Solution

This folder contains the third required execution implementation:

- `sql_dynamic`

The file [03_dynamic_sql.sql](C:/Users/Mitelman/Documents/Codex/dynamic-formula-benchmark/sql-solution/03_dynamic_sql.sql) creates the SQL Server stored procedure that:

- reads formulas from `t_targil`
- executes them dynamically inside SQL Server
- writes full benchmark results into `t_results`
- writes timing metrics into `t_log`

Why this folder exists:

- to make the SQL implementation visually parallel to `python-solution` and `csharp-solution`
- to present the third execution engine as a first-class implementation in the repository
- to keep the project structure clearer for reviewers
