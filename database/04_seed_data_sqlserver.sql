/*
SQL Server seed script for 1,000,000 test rows.
This script populates t_data with random values for a, b, c, d.
*/

SET NOCOUNT ON;

IF OBJECT_ID('tempdb..#numbers') IS NOT NULL
    DROP TABLE #numbers;

WITH numbers AS (
    SELECT TOP (1000000)
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS row_num
    FROM sys.all_objects AS a
    CROSS JOIN sys.all_objects AS b
)
SELECT row_num
INTO #numbers
FROM numbers;

TRUNCATE TABLE t_data;

INSERT INTO t_data (data_id, a, b, c, d)
SELECT
    row_num,
    CAST((ABS(CHECKSUM(NEWID())) % 100000) / 100.0 + 1 AS FLOAT),
    CAST((ABS(CHECKSUM(NEWID())) % 100000) / 100.0 + 1 AS FLOAT),
    CAST((ABS(CHECKSUM(NEWID())) % 100000) / 100.0 + 1 AS FLOAT),
    CAST((ABS(CHECKSUM(NEWID())) % 100000) / 100.0 + 1 AS FLOAT)
FROM #numbers;

DROP TABLE #numbers;
