# Dynamic Formula Calculation Benchmark

## Suggested Repository Names

Choose one of these for GitHub:

1. `dynamic-formula-benchmark`
2. `payment-formula-engine-benchmark`
3. `runtime-formula-evaluation-lab`
4. `dynamic-calculation-engine`
5. `formula-execution-performance-comparison`

Recommended project title:

`Dynamic Formula Calculation Benchmark`

Recommended subtitle:

`A comparative benchmark of dynamic formula execution methods over large-scale payment data`

## Execution Plan

### Phase 1 - Foundation

1. Create the database.
2. Create the tables `t_data`, `t_targil`, `t_results`, `t_log`.
3. Verify primary keys and foreign keys.
4. Decide which DB engine you will use for the final submission.

### Phase 2 - Seed Data

1. Write a script that inserts 1,000,000 rows into `t_data`.
2. Generate random values for `a`, `b`, `c`, `d`.
3. Insert 8-12 formulas into `t_targil`.
4. Make sure the formulas include:
   - Simple arithmetic
   - Complex math
   - At least 1-2 conditional formulas

### Phase 3 - First Working Method

1. Implement one end-to-end method in Python.
2. For each formula:
   - Read formula metadata from `t_targil`
   - Iterate through all rows in `t_data`
   - Calculate the result
   - Save the result to `t_results`
   - Measure execution time
   - Save execution time to `t_log`
3. Verify that the process works correctly on a small data sample first.

### Phase 4 - Add More Methods

Implement at least 2 additional approaches:

1. `python_eval`
2. `python_ast`
3. `sql_dynamic`

Recommended order:

1. `python_eval`
2. `sql_dynamic`
3. `python_ast`

### Phase 5 - Validation

1. Write a comparison script.
2. Compare output values between methods.
3. Confirm the same `data_id` and `targil_id` produce the same result.
4. Handle floating point comparison with tolerance.

### Phase 6 - Reporting

1. Build a simple report screen.
2. Present:
   - Runtime per method
   - Runtime per formula
   - Best overall method
   - Notes on accuracy and tradeoffs
3. Add screenshots for DB tables and report screen.

### Phase 7 - Submission Package

Prepare:

1. Source code
2. SQL scripts
3. Data generation script
4. Result comparison script
5. Screenshots
6. Short summary report
7. GitHub repository link

## What Matters Most

1. Correctness before performance
2. Clear separation between formulas and code
3. Reproducible benchmark process
4. Professional structure and naming
5. Clear comparison and conclusion

## Recommended Technologies

### Best balanced stack

- Backend language: `Python`
- Database: `PostgreSQL` or `SQL Server`
- Reporting UI: `React`
- Charts: `Recharts` or `Chart.js`

### If you want the easiest path

- Backend language: `Python`
- Database: `PostgreSQL`
- Report UI: `React`

## Recommended Method Names

Use these method names consistently in DB and code:

- `python_eval`
- `python_ast`
- `sql_dynamic`

## Recommended Folder Names

- `database`
- `scripts`
- `src`
- `report-ui`
- `docs`
- `tests`

## Practical First Start

Start in this exact order:

1. Run the SQL schema script.
2. Add sample formulas.
3. Write the data generator.
4. Test with 1,000 rows.
5. Implement `python_eval`.
6. Save results and timing.
7. Only then scale to 1,000,000 rows.
