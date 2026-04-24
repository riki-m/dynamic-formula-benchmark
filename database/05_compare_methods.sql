/*
Compare two execution methods inside SQL Server.

Usage example:
DECLARE @base_method VARCHAR(50) = 'python_eval';
DECLARE @compare_method VARCHAR(50) = 'sql_dynamic';
*/

DECLARE @base_method VARCHAR(50) = 'python_eval';
DECLARE @compare_method VARCHAR(50) = 'sql_dynamic';
DECLARE @tolerance FLOAT = 0.000000001;

SELECT
    base.data_id,
    base.targil_id,
    base.result AS base_result,
    candidate.result AS compare_result,
    ABS(base.result - candidate.result) AS absolute_diff
FROM t_results AS base
LEFT JOIN t_results AS candidate
    ON candidate.data_id = base.data_id
   AND candidate.targil_id = base.targil_id
   AND candidate.method = @compare_method
WHERE base.method = @base_method
  AND (
      candidate.result IS NULL
      OR ABS(base.result - candidate.result) > @tolerance
  )
ORDER BY base.targil_id, base.data_id;

SELECT
    @base_method AS base_method,
    @compare_method AS compare_method,
    COUNT(*) AS mismatched_rows
FROM t_results AS base
LEFT JOIN t_results AS candidate
    ON candidate.data_id = base.data_id
   AND candidate.targil_id = base.targil_id
   AND candidate.method = @compare_method
WHERE base.method = @base_method
  AND (
      candidate.result IS NULL
      OR ABS(base.result - candidate.result) > @tolerance
  );
