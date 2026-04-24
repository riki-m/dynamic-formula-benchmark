using System.Data;
using Microsoft.Data.SqlClient;
using DynamicFormulaBenchmark.Models;

namespace DynamicFormulaBenchmark;

public sealed class DatabaseService
{
    private const int BatchSize = 5000;
    private readonly string _connectionString;
    private readonly FormulaEngine _formulaEngine = new();

    public DatabaseService()
    {
        _connectionString =
            Environment.GetEnvironmentVariable("SQLSERVER_SQLCLIENT_CONNECTION_STRING")
            ?? "Server=localhost\\SQLEXPRESS;Database=DynamicFormulaBenchmark;Integrated Security=true;TrustServerCertificate=true;";
    }

    public string MethodName => "csharp_engine";

    public async Task RunBenchmarkAsync(CancellationToken cancellationToken = default)
    {
        var formulas = await LoadFormulasAsync(cancellationToken);
        if (formulas.Count == 0)
        {
            throw new InvalidOperationException("No formulas were found in t_targil.");
        }

        if (!await TableHasRowsAsync("t_data", cancellationToken))
        {
            throw new InvalidOperationException("t_data is empty. Seed SQL Server data first.");
        }

        await ResetMethodResultsAsync(cancellationToken);

        Console.WriteLine($"Loaded {formulas.Count} formulas from SQL Server");
        Console.WriteLine($"Running with batch size {BatchSize:N0}");

        var nextResultId = await GetNextIdAsync("t_results", "result_id", cancellationToken);
        var nextLogId = await GetNextIdAsync("t_log", "log_id", cancellationToken);

        foreach (var formula in formulas)
        {
            var prepared = _formulaEngine.Prepare(formula);
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            var processed = 0;

            Console.WriteLine($"Running formula {formula.Id}: {formula.Expression}");

            await foreach (var batch in LoadDataBatchesAsync(BatchSize, cancellationToken))
            {
                var resultTable = BuildResultTable();
                foreach (var row in batch)
                {
                    var result = _formulaEngine.Evaluate(prepared, row);
                    resultTable.Rows.Add(nextResultId, row.DataId, formula.Id, MethodName, result);
                    nextResultId++;
                    processed++;
                }

                await BulkInsertResultsAsync(resultTable, cancellationToken);
            }

            stopwatch.Stop();
            await InsertLogAsync(nextLogId, formula.Id, stopwatch.Elapsed.TotalSeconds, processed, cancellationToken);
            nextLogId++;
            Console.WriteLine($"Finished formula {formula.Id} in {stopwatch.Elapsed.TotalSeconds:F3} seconds for {processed:N0} rows");
        }
    }

    private async Task<List<FormulaDefinition>> LoadFormulasAsync(CancellationToken cancellationToken)
    {
        var formulas = new List<FormulaDefinition>();

        await using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        await using var command = new SqlCommand(
            """
            SELECT targil_id, targil, tnai, targil_false
            FROM t_targil
            ORDER BY targil_id
            """,
            connection
        );

        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            formulas.Add(
                new FormulaDefinition
                {
                    Id = reader.GetInt32(0),
                    Expression = reader.GetString(1),
                    Condition = reader.IsDBNull(2) ? null : reader.GetString(2),
                    FalseExpression = reader.IsDBNull(3) ? null : reader.GetString(3),
                }
            );
        }

        return formulas;
    }

    private async IAsyncEnumerable<List<DataRecord>> LoadDataBatchesAsync(int batchSize, [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken cancellationToken)
    {
        await using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        await using var command = new SqlCommand(
            """
            SELECT data_id, a, b, c, d
            FROM t_data
            ORDER BY data_id
            """,
            connection
        );

        await using var reader = await command.ExecuteReaderAsync(CommandBehavior.SequentialAccess, cancellationToken);
        var batch = new List<DataRecord>(batchSize);

        while (await reader.ReadAsync(cancellationToken))
        {
            batch.Add(
                new DataRecord
                {
                    DataId = reader.GetInt32(0),
                    A = Convert.ToDouble(reader.GetValue(1)),
                    B = Convert.ToDouble(reader.GetValue(2)),
                    C = Convert.ToDouble(reader.GetValue(3)),
                    D = Convert.ToDouble(reader.GetValue(4)),
                }
            );

            if (batch.Count == batchSize)
            {
                yield return batch;
                batch = new List<DataRecord>(batchSize);
            }
        }

        if (batch.Count > 0)
        {
            yield return batch;
        }
    }

    private async Task<bool> TableHasRowsAsync(string tableName, CancellationToken cancellationToken)
    {
        await using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        await using var command = new SqlCommand($"SELECT TOP 1 1 FROM {tableName}", connection);
        var result = await command.ExecuteScalarAsync(cancellationToken);
        return result is not null;
    }

    private async Task ResetMethodResultsAsync(CancellationToken cancellationToken)
    {
        await using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        await using var command = new SqlCommand(
            """
            DELETE FROM t_results WHERE method = @method;
            DELETE FROM t_log WHERE method = @method;
            """,
            connection
        );
        command.Parameters.AddWithValue("@method", MethodName);
        await command.ExecuteNonQueryAsync(cancellationToken);
    }

    private async Task<long> GetNextIdAsync(string tableName, string columnName, CancellationToken cancellationToken)
    {
        await using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        await using var command = new SqlCommand($"SELECT ISNULL(MAX({columnName}), 0) + 1 FROM {tableName}", connection);
        var value = await command.ExecuteScalarAsync(cancellationToken);
        return Convert.ToInt64(value);
    }

    private static DataTable BuildResultTable()
    {
        var table = new DataTable();
        table.Columns.Add("result_id", typeof(long));
        table.Columns.Add("data_id", typeof(int));
        table.Columns.Add("targil_id", typeof(int));
        table.Columns.Add("method", typeof(string));
        table.Columns.Add("result", typeof(double));
        return table;
    }

    private async Task BulkInsertResultsAsync(DataTable table, CancellationToken cancellationToken)
    {
        await using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        using var bulkCopy = new SqlBulkCopy(connection)
        {
            DestinationTableName = "t_results",
            BatchSize = table.Rows.Count,
        };

        bulkCopy.ColumnMappings.Add("result_id", "result_id");
        bulkCopy.ColumnMappings.Add("data_id", "data_id");
        bulkCopy.ColumnMappings.Add("targil_id", "targil_id");
        bulkCopy.ColumnMappings.Add("method", "method");
        bulkCopy.ColumnMappings.Add("result", "result");

        await bulkCopy.WriteToServerAsync(table, cancellationToken);
    }

    private async Task InsertLogAsync(long logId, int formulaId, double runtimeSeconds, int recordsProcessed, CancellationToken cancellationToken)
    {
        await using var connection = new SqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        await using var command = new SqlCommand(
            """
            INSERT INTO t_log (log_id, targil_id, method, run_time, records_processed)
            VALUES (@logId, @formulaId, @method, @runtime, @recordsProcessed)
            """,
            connection
        );

        command.Parameters.AddWithValue("@logId", logId);
        command.Parameters.AddWithValue("@formulaId", formulaId);
        command.Parameters.AddWithValue("@method", MethodName);
        command.Parameters.AddWithValue("@runtime", runtimeSeconds);
        command.Parameters.AddWithValue("@recordsProcessed", recordsProcessed);

        await command.ExecuteNonQueryAsync(cancellationToken);
    }
}
