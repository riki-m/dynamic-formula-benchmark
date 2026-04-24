import math
from dataclasses import dataclass

from src.syntax_transformer import to_python_expression

ALLOWED_GLOBALS = {
    "__builtins__": {},
    "abs": abs,
    "sqrt": math.sqrt,
    "log": math.log,
    "pow": pow,
}


@dataclass
class FormulaDefinition:
    targil_id: int
    targil: str
    tnai: str | None
    targil_false: str | None


@dataclass
class PreparedFormula:
    targil_id: int
    target_code: object
    condition_code: object | None = None
    false_code: object | None = None


def prepare_formula(formula: FormulaDefinition) -> PreparedFormula:
    if formula.tnai:
        target_expression = to_python_expression(formula.targil)
        false_expression = to_python_expression(formula.targil_false or "0")
        condition_expression = to_python_expression(formula.tnai)
        return PreparedFormula(
            targil_id=formula.targil_id,
            target_code=compile(target_expression, f"formula_{formula.targil_id}_true", "eval"),
            false_code=compile(false_expression, f"formula_{formula.targil_id}_false", "eval"),
            condition_code=compile(condition_expression, f"formula_{formula.targil_id}_condition", "eval"),
        )

    direct_expression = to_python_expression(formula.targil)
    return PreparedFormula(
        targil_id=formula.targil_id,
        target_code=compile(direct_expression, f"formula_{formula.targil_id}", "eval"),
    )


def evaluate_formula(prepared_formula: PreparedFormula, row: dict) -> float:
    if prepared_formula.condition_code is not None:
        condition_result = eval(prepared_formula.condition_code, ALLOWED_GLOBALS, row)
        target_code = prepared_formula.target_code if condition_result else prepared_formula.false_code
        if target_code is None:
            raise ValueError(f"Formula {prepared_formula.targil_id} has no false branch to evaluate")
        return float(eval(target_code, ALLOWED_GLOBALS, row))

    return float(eval(prepared_formula.target_code, ALLOWED_GLOBALS, row))
