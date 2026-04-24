namespace DynamicFormulaBenchmark.Models;

public sealed class FormulaDefinition
{
    public int Id { get; init; }
    public string Expression { get; init; } = string.Empty;
    public string? Condition { get; init; }
    public string? FalseExpression { get; init; }
}
