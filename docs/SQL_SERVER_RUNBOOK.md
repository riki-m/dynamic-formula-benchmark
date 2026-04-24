# SQL Server Runbook

## Goal

Run the shared benchmark on SQL Server so that:

- `python_eval` reads from SQL Server and writes to `t_results`
- `sql_dynamic` runs directly inside SQL Server
- both methods can be compared on the same tables

## Required Order

1. Create the database in SQL Server.
2. Run [database/01_schema.sql](../database/01_schema.sql).
3. Run [database/02_seed_formulas.sql](../database/02_seed_formulas.sql).
4. Run [database/04_seed_data_sqlserver.sql](../database/04_seed_data_sqlserver.sql).
5. Run the Python worker against SQL Server.
6. Run [sql-solution/03_dynamic_sql.sql](../sql-solution/03_dynamic_sql.sql) to create the stored procedure.
7. Execute `EXEC dbo.usp_run_sql_dynamic_benchmark;`
8. Run [database/05_compare_methods.sql](../database/05_compare_methods.sql).

## Python Worker Against SQL Server

Set environment variables before running:

```powershell
$env:DB_ENGINE="sqlserver"
$env:SQLSERVER_CONNECTION_STRING="Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=DynamicFormulaBenchmark;Trusted_Connection=yes;"
```

Then run:

```powershell
python python-solution/scripts/run_python_eval_sqlserver.py
```

## What To Verify

After running both methods, check:

```sql
SELECT method, COUNT(*) AS total_rows
FROM t_results
GROUP BY method;

SELECT method, targil_id, run_time, records_processed
FROM t_log
ORDER BY method, targil_id;
```

Expected logic:

- `python_eval` and `sql_dynamic` should both produce results for the same `(data_id, targil_id)` pairs.
- `records_processed` should be `1000000` for each formula when the full dataset is loaded.
- [database/05_compare_methods.sql](../database/05_compare_methods.sql) should return zero mismatches.

## Current Limitation In This Workspace

This Codex workspace currently does not have `sqlcmd`, Docker, or a running SQL Server instance, so the SQL Server path was prepared but not executed from this session.
