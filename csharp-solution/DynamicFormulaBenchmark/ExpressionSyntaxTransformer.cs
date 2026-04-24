using System.Text;
using System.Text.RegularExpressions;

namespace DynamicFormulaBenchmark;

public static class ExpressionSyntaxTransformer
{
    private static readonly Regex IfPattern = new(@"^\s*if\s*\((.*)\)\s*$", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex SingleEqualsPattern = new(@"(?<![<>=!])=(?!=)", RegexOptions.Compiled);
    private static readonly Regex PowerPattern = new(@"([A-Za-z0-9_\.]+)\s*\^\s*([A-Za-z0-9_\.]+)", RegexOptions.Compiled);

    public static string ToCSharpExpression(string expression)
    {
        expression = NormalizeCommonSyntax(expression);
        var match = IfPattern.Match(expression);
        if (!match.Success)
        {
            return expression;
        }

        var arguments = SplitTopLevelArguments(match.Groups[1].Value);
        if (arguments.Count != 3)
        {
            throw new InvalidOperationException($"Unsupported IF expression: {expression}");
        }

        var condition = NormalizeCommonSyntax(arguments[0]);
        var whenTrue = NormalizeCommonSyntax(arguments[1]);
        var whenFalse = NormalizeCommonSyntax(arguments[2]);

        return $"({condition}) ? ({whenTrue}) : ({whenFalse})";
    }

    public static string NormalizeCommonSyntax(string expression)
    {
        var normalized = expression.Trim();
        normalized = SingleEqualsPattern.Replace(normalized, "==");
        normalized = normalized.Replace("sqrt(", "Math.Sqrt(", StringComparison.OrdinalIgnoreCase);
        normalized = normalized.Replace("log(", "Math.Log(", StringComparison.OrdinalIgnoreCase);
        normalized = normalized.Replace("abs(", "Math.Abs(", StringComparison.OrdinalIgnoreCase);
        normalized = ReplacePowerSyntax(normalized);
        return normalized;
    }

    private static string ReplacePowerSyntax(string expression)
    {
        var rewritten = expression;
        while (PowerPattern.IsMatch(rewritten))
        {
            rewritten = PowerPattern.Replace(rewritten, "Math.Pow($1, $2)");
        }

        return rewritten;
    }

    private static List<string> SplitTopLevelArguments(string source)
    {
        var parts = new List<string>();
        var builder = new StringBuilder();
        var depth = 0;

        foreach (var character in source)
        {
            if (character == ',' && depth == 0)
            {
                parts.Add(builder.ToString().Trim());
                builder.Clear();
                continue;
            }

            if (character == '(')
            {
                depth++;
            }
            else if (character == ')')
            {
                depth--;
            }

            builder.Append(character);
        }

        if (builder.Length > 0)
        {
            parts.Add(builder.ToString().Trim());
        }

        return parts;
    }
}
