/*
SQL Server dynamic formula execution method with batching.
Primary SQL implementation folder for the third required execution engine.
Keeps full compliance with the assignment:
- 1,000,000 rows
- full write to t_results
- logging to t_log
*/

CREATE OR ALTER PROCEDURE dbo.usp_run_sql_dynamic_benchmark
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE
        @targil_id INT,
        @targil NVARCHAR(255),
        @tnai NVARCHAR(255),
        @targil_false NVARCHAR(255),
        @expression NVARCHAR(MAX),
        @true_expression NVARCHAR(MAX),
        @false_expression NVARCHAR(MAX),
        @condition_expression NVARCHAR(MAX),
        @sql NVARCHAR(MAX),
        @start_time DATETIME2(7),
        @end_time DATETIME2(7),
        @run_time_seconds FLOAT,
        @records_processed INT,
        @next_result_id BIGINT,
        @next_log_id INT,
        @batch_size INT = 5000,
        @batch_start INT,
        @batch_end INT,
        @max_data_id INT;

    DELETE FROM t_results WHERE method = 'sql_dynamic';
    DELETE FROM t_log WHERE method = 'sql_dynamic';

    SELECT @max_data_id = MAX(data_id) FROM t_data;

    DECLARE formula_cursor CURSOR FAST_FORWARD FOR
        SELECT targil_id, targil, tnai, targil_false
        FROM t_targil
        ORDER BY targil_id;

    OPEN formula_cursor;
    FETCH NEXT FROM formula_cursor INTO @targil_id, @targil, @tnai, @targil_false;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @start_time = SYSUTCDATETIME();
        SET @records_processed = 0;
        SET @batch_start = 1;

        WHILE @batch_start <= @max_data_id
        BEGIN
            SET @batch_end = @batch_start + @batch_size - 1;

            SET @true_expression = @targil;
            SET @false_expression = ISNULL(@targil_false, '0');
            SET @condition_expression = @tnai;

            SET @true_expression = REPLACE(@true_expression, 'sqrt(c^2 + d^2)', 'SQRT(POWER(c, 2) + POWER(d, 2))');
            SET @true_expression = REPLACE(@true_expression, 'log(', 'LOG(');
            SET @true_expression = REPLACE(@true_expression, 'abs(', 'ABS(');

            SET @false_expression = REPLACE(@false_expression, 'sqrt(c^2 + d^2)', 'SQRT(POWER(c, 2) + POWER(d, 2))');
            SET @false_expression = REPLACE(@false_expression, 'log(', 'LOG(');
            SET @false_expression = REPLACE(@false_expression, 'abs(', 'ABS(');

            IF @condition_expression IS NOT NULL
            BEGIN
                SET @condition_expression = REPLACE(@condition_expression, '==', '=');
                SET @expression =
                    N'CASE WHEN ' + @condition_expression +
                    N' THEN ' + @true_expression +
                    N' ELSE ' + @false_expression + N' END';
            END
            ELSE
            BEGIN
                SET @expression = @true_expression;
            END

            SELECT @next_result_id = ISNULL(MAX(result_id), 0) + 1
            FROM t_results;

            SET @sql = N'
                INSERT INTO t_results (result_id, data_id, targil_id, method, result)
                SELECT
                    ROW_NUMBER() OVER (ORDER BY data_id) + ' + CAST(@next_result_id - 1 AS NVARCHAR(30)) + N',
                    data_id,
                    ' + CAST(@targil_id AS NVARCHAR(20)) + N',
                    ''sql_dynamic'',
                    CAST(' + @expression + N' AS FLOAT)
                FROM t_data
                WHERE data_id BETWEEN ' + CAST(@batch_start AS NVARCHAR(20)) +
                N' AND ' + CAST(@batch_end AS NVARCHAR(20)) + N';
            ';

            EXEC sp_executesql @sql;
            SET @records_processed = @records_processed + @@ROWCOUNT;

            CHECKPOINT;

            SET @batch_start = @batch_end + 1;
        END

        SET @end_time = SYSUTCDATETIME();
        SET @run_time_seconds = DATEDIFF(MILLISECOND, @start_time, @end_time) / 1000.0;

        SELECT @next_log_id = ISNULL(MAX(log_id), 0) + 1
        FROM t_log;

        INSERT INTO t_log (log_id, targil_id, method, run_time, records_processed)
        VALUES (@next_log_id, @targil_id, 'sql_dynamic', @run_time_seconds, @records_processed);

        FETCH NEXT FROM formula_cursor INTO @targil_id, @targil, @tnai, @targil_false;
    END

    CLOSE formula_cursor;
    DEALLOCATE formula_cursor;
END;
GO
