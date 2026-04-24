# Benchmark Summary

## Benchmark Outcome

The system was implemented and measured using the three required execution methods:

1. `python_eval`
2. `csharp_engine`
3. `sql_dynamic`

Each method processed 1,000,000 records across 11 formulas. All required result sets were saved into `t_results`, and all execution measurements were saved into `t_log`.

## Correctness Validation

Correctness was validated by comparing all method pairs inside SQL Server:

- `python_eval` vs `sql_dynamic`
- `python_eval` vs `csharp_engine`
- `csharp_engine` vs `sql_dynamic`

All comparison runs returned:

`mismatched_rows = 0`

This confirms that all three implementations produced identical calculation results.

## Performance Interpretation

Measured benchmark results showed the following overall ranking:

1. `csharp_engine` was the fastest overall method
2. `sql_dynamic` was the second-fastest method
3. `python_eval` was the slowest method

Average runtime per formula:

- `csharp_engine`: `22.618` seconds
- `sql_dynamic`: `32.547` seconds
- `python_eval`: `61.586` seconds

Total runtime across all 11 formulas:

- `csharp_engine`: `248.794` seconds
- `sql_dynamic`: `358.013` seconds
- `python_eval`: `677.451` seconds

## Architectural Conclusion

The benchmark indicates that `csharp_engine` provides the best overall balance between speed, maintainability, extensibility, and production readiness. `sql_dynamic` performs well and is particularly strong in database-centric architectures, but introduces higher operational and SQL-generation complexity. `python_eval` offers fast implementation and flexibility, but its runtime performance was significantly weaker at the measured scale.

## Dynamic Intelligence Engine

In addition to the required three execution methods, this project includes a local dynamic intelligence engine. This layer does not calculate formulas and does not replace the required engines. Its purpose is to analyze validated benchmark outputs, answer benchmark questions, summarize performance trends, explain architectural trade-offs, and generate a downloadable technical report.

This keeps the solution fully aligned with the assignment while demonstrating a more modern engineering approach: separating execution from analytical interpretation.
