using DynamicFormulaBenchmark;

Console.WriteLine("Dynamic Formula Benchmark - C# worker");

try
{
    var service = new DatabaseService();
    await service.RunBenchmarkAsync();
    Console.WriteLine("C# benchmark completed successfully.");
}
catch (Exception exception)
{
    Console.Error.WriteLine("C# benchmark failed:");
    Console.Error.WriteLine(exception.Message);
    Environment.ExitCode = 1;
}
