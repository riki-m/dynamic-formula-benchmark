using DynamicExpresso;
using DynamicFormulaBenchmark.Models;

namespace DynamicFormulaBenchmark;

public sealed class FormulaEngine
{
    public Lambda Prepare(FormulaDefinition formula)
    {
        var interpreter = new Interpreter()
            .Reference(typeof(Math));

        var expression = BuildExpression(formula);
        return interpreter.Parse(
            expression,
            new Parameter("a", typeof(double)),
            new Parameter("b", typeof(double)),
            new Parameter("c", typeof(double)),
            new Parameter("d", typeof(double))
        );
    }

    public double Evaluate(Lambda lambda, DataRecord row)
    {
        var result = lambda.Invoke(row.A, row.B, row.C, row.D);
        return Convert.ToDouble(result);
    }

    private static string BuildExpression(FormulaDefinition formula)
    {
        if (!string.IsNullOrWhiteSpace(formula.Condition))
        {
            var condition = ExpressionSyntaxTransformer.ToCSharpExpression(formula.Condition!);
            var whenTrue = ExpressionSyntaxTransformer.ToCSharpExpression(formula.Expression);
            var whenFalse = ExpressionSyntaxTransformer.ToCSharpExpression(formula.FalseExpression ?? "0");
            return $"({condition}) ? ({whenTrue}) : ({whenFalse})";
        }

        return ExpressionSyntaxTransformer.ToCSharpExpression(formula.Expression);
    }
}
