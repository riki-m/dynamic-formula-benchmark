from __future__ import annotations

import re


IF_PATTERN = re.compile(r"^\s*if\s*\((.*)\)\s*$", re.IGNORECASE)
SINGLE_EQUALS_PATTERN = re.compile(r"(?<![<>=!])=(?!=)")


def normalize_condition_operators(expression: str) -> str:
    return SINGLE_EQUALS_PATTERN.sub("==", expression)


def normalize_common_syntax(expression: str) -> str:
    normalized = expression.strip()
    normalized = normalized.replace("^", "**")
    normalized = normalize_condition_operators(normalized)
    return normalized


def split_top_level_arguments(argument_source: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0

    for character in argument_source:
        if character == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue

        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1

        current.append(character)

    if current:
        parts.append("".join(current).strip())

    return parts


def db_if_to_python(expression: str) -> str:
    match = IF_PATTERN.match(expression)
    if not match:
        return normalize_common_syntax(expression)

    arguments = split_top_level_arguments(match.group(1))
    if len(arguments) != 3:
        raise ValueError(f"Unsupported IF expression format: {expression}")

    condition, when_true, when_false = arguments
    return (
        f"({normalize_common_syntax(when_true)}) "
        f"if ({normalize_common_syntax(condition)}) "
        f"else ({normalize_common_syntax(when_false)})"
    )


def to_python_expression(expression: str) -> str:
    expression = expression.strip()
    if expression.lower().startswith("if(") or expression.lower().startswith("if ("):
        return db_if_to_python(expression)
    return normalize_common_syntax(expression)
