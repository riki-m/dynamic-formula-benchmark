# Formula Evaluation Model

## Main Principle

The formulas are stored as data in `t_targil`, not hardcoded in source code. This allows the system to execute new formulas without rebuilding the application.

## Important Precision

The system is not a universal mathematical compiler.

What it does support:

- any formula that is valid for the selected runtime engine
- any formula that can be translated from the database syntax into the engine syntax
- new formulas added to the database without changing application source code

What it does not guarantee automatically:

- every possible expression language in the world
- arbitrary custom functions unless they are exposed by the target engine
- incompatible syntax without a translation layer

## Python

In the Python solution, the runtime evaluator is `eval()`.

Flow:

1. Read formula text from `t_targil`.
2. Transform DB syntax into Python syntax.
3. Normalize operators such as `^` to `**` and `=` to `==` in conditions.
4. Translate `if(condition, x, y)` into `x if condition else y`.
5. Compile the transformed expression once for the current formula.
6. Expose row variables `a`, `b`, `c`, `d` as locals.
7. Execute the prepared expression through `eval()`.

Conditional formulas are supported by combining:

- `tnai`
- `targil`
- `targil_false`

This means the database stores the conditional parts as structured fields, and Python selects the correct branch at runtime.

The current Python worker also processes `t_data` in batches instead of loading the entire dataset for every formula at once.

## C#

In the C# implementation, the runtime evaluator is `DynamicExpresso`.

Flow:

1. Read formula text from `t_targil`.
2. Transform DB syntax into C# expression syntax.
3. Convert `if(condition, x, y)` into `condition ? x : y`.
4. Map functions like `sqrt`, `log`, `abs` into `Math.Sqrt`, `Math.Log`, `Math.Abs`.
5. Parse the expression once into a reusable lambda.
6. Invoke the lambda for each row in the current batch.

This approach is a closer match to the assignment than building a custom compiler, because it uses an existing runtime expression engine.

## SQL Server

In the SQL solution, the runtime evaluator is the SQL Server engine itself via `sp_executesql`.

Flow:

1. Read the formula text from `t_targil`.
2. Translate generic syntax into SQL-compatible syntax when needed.
3. Build a dynamic `INSERT ... SELECT` statement.
4. Execute it with `sp_executesql`.
5. Log both runtime and `records_processed`.

For conditional formulas, the SQL solution converts the condition into:

```sql
CASE WHEN <condition> THEN <true_expression> ELSE <false_expression> END
```

## Why This Matches The Assignment

The assignment asks for a system that can learn or execute new formulas at runtime from external sources such as database tables.

This design satisfies that requirement because:

- formulas are inserted into the database
- the application loads them dynamically
- the execution engine interprets them at runtime
- no source code change is required for each new formula
