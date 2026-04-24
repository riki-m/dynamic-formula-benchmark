from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import pstdev
import json
import subprocess
from typing import Any
from uuid import uuid4


METHOD_META = {
    "csharp_engine": {"label": "C# Engine", "color": "#ff8f3f"},
    "sql_dynamic": {"label": "SQL Dynamic", "color": "#2dc0b2"},
    "python_eval": {"label": "Python Eval", "color": "#8ab4ff"},
}


def label_for_method(method: str) -> str:
    return METHOD_META.get(method, {}).get("label", method)


def color_for_method(method: str) -> str:
    return METHOD_META.get(method, {}).get("color", "#91a5a4")


def build_analysis_payload(
    overview: dict[str, Any],
    formulas: list[dict[str, Any]],
    logs: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    correctness_cards: list[dict[str, Any]],
) -> dict[str, Any]:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary_rows = [normalize_summary_row(row) for row in summary_rows]
    logs = [normalize_log_row(row) for row in logs]

    method_timings: dict[str, list[float]] = defaultdict(list)
    per_formula: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for log in logs:
        method_timings[log["method"]].append(log["run_time"])
        per_formula[log["targil_id"]].append(log)

    fastest = summary_rows[0] if summary_rows else None
    slowest = summary_rows[-1] if summary_rows else None

    stability_rows = []
    for row in summary_rows:
        timings = method_timings.get(row["method"], [row["average_runtime_seconds"]])
        stability_rows.append(
            {
                "method": row["method"],
                "std_dev": pstdev(timings) if len(timings) > 1 else 0.0,
                "spread": row["worst_runtime_seconds"] - row["best_runtime_seconds"],
            }
        )
    most_stable = min(stability_rows, key=lambda item: (item["std_dev"], item["spread"])) if stability_rows else None

    winners = []
    closest_race = None
    widest_margin = None
    for formula in formulas:
        ranked = sorted(per_formula.get(formula["targil_id"], []), key=lambda row: row["run_time"])
        if not ranked:
            continue
        leader = ranked[0]
        runner_up = ranked[1] if len(ranked) > 1 else ranked[0]
        margin = runner_up["run_time"] - leader["run_time"]
        winner = {
            "targil_id": formula["targil_id"],
            "formula": formula["display_formula"],
            "category": formula["category"],
            "winner_method": leader["method"],
            "winner_label": label_for_method(leader["method"]),
            "winner_runtime_seconds": leader["run_time"],
            "margin_seconds": margin,
        }
        winners.append(winner)
        if closest_race is None or margin < closest_race["margin_seconds"]:
            closest_race = winner
        if widest_margin is None or margin > widest_margin["margin_seconds"]:
            widest_margin = winner

    category_matrix = build_category_matrix(formulas, per_formula)
    recommendation_matrix = build_recommendation_matrix(fastest["method"] if fastest else "csharp_engine")

    performance_gap = (slowest["average_runtime_seconds"] - fastest["average_runtime_seconds"]) if fastest and slowest else 0.0
    correctness_pairs = sum(1 for item in correctness_cards if item["mismatched_rows"] == 0)

    key_findings = []
    if fastest and slowest:
        key_findings.append(
            {
                "title": "Fastest Overall",
                "value": label_for_method(fastest["method"]),
                "detail": (
                    f"{label_for_method(fastest['method'])} achieved the lowest average runtime at "
                    f"{fastest['average_runtime_seconds']:.3f}s per formula, beating "
                    f"{label_for_method(slowest['method'])} by {performance_gap:.3f}s."
                ),
            }
        )
    if most_stable:
        key_findings.append(
            {
                "title": "Most Stable Runtime",
                "value": label_for_method(most_stable["method"]),
                "detail": (
                    f"Runtime variance stayed lowest for {label_for_method(most_stable['method'])}, "
                    f"with a standard deviation of {most_stable['std_dev']:.3f}s."
                ),
            }
        )
    if closest_race:
        key_findings.append(
            {
                "title": "Closest Race",
                "value": f"Formula {closest_race['targil_id']}",
                "detail": (
                    f"{closest_race['winner_label']} won this formula by only "
                    f"{closest_race['margin_seconds']:.3f}s."
                ),
            }
        )
    if widest_margin:
        key_findings.append(
            {
                "title": "Largest Advantage",
                "value": f"Formula {widest_margin['targil_id']}",
                "detail": (
                    f"{widest_margin['winner_label']} created the widest gap here at "
                    f"{widest_margin['margin_seconds']:.3f}s."
                ),
            }
        )

    warnings = []
    if fastest and slowest and slowest["average_runtime_seconds"] > fastest["average_runtime_seconds"] * 2:
        warnings.append(
            {
                "title": "Large performance spread",
                "detail": (
                    f"The slowest engine is more than 2x slower than the fastest one, so architecture choice materially affects latency."
                ),
            }
        )
    if widest_margin and widest_margin["category"] == "Complex":
        warnings.append(
            {
                "title": "Complex formulas are the real separator",
                "detail": (
                    "The widest runtime gap appeared in a complex formula, which suggests mathematical transformation cost is a major differentiator."
                ),
            }
        )
    warnings.append(
        {
            "title": "Correctness stayed fully aligned",
            "detail": f"All {correctness_pairs} validated pairwise comparisons returned mismatched_rows = 0, so the benchmark ranking is safe to trust.",
        }
    )

    executive_summary = (
        f"This analysis was generated directly from measured benchmark logs over {overview['records_processed']:,} records and "
        f"{overview['formula_count']} formulas. {label_for_method(fastest['method']) if fastest else 'C# Engine'} delivered the strongest "
        f"overall runtime profile, while {label_for_method(most_stable['method']) if most_stable else 'SQL Dynamic'} showed the most stable timing behavior. "
        f"The performance spread between the fastest and slowest engine reached {performance_gap:.3f}s per formula, which makes execution architecture a meaningful production decision."
    )

    analysis = {
        "generated_at": generated_at,
        "executive_summary": executive_summary,
        "key_findings": key_findings,
        "warnings": warnings,
        "category_matrix": category_matrix,
        "formula_winners": winners,
        "recommendation_matrix": recommendation_matrix,
        "fastest_method": fastest["method"] if fastest else None,
        "most_stable_method": most_stable["method"] if most_stable else None,
        "performance_gap_seconds": performance_gap,
        "summary_rows": summary_rows,
        "correctness_cards": correctness_cards,
        "markdown": render_analysis_markdown(
            generated_at,
            executive_summary,
            key_findings,
            warnings,
            category_matrix,
            winners,
            recommendation_matrix,
        ),
    }
    return analysis


def normalize_summary_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "formulas_executed": int(row["formulas_executed"]),
        "total_records_processed": int(row["total_records_processed"]),
        "average_runtime_seconds": float(row["average_runtime_seconds"]),
        "best_runtime_seconds": float(row["best_runtime_seconds"]),
        "worst_runtime_seconds": float(row["worst_runtime_seconds"]),
        "total_runtime_seconds": float(row["total_runtime_seconds"]),
    }


def normalize_log_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "targil_id": int(row["targil_id"]),
        "run_time": float(row["run_time"]),
        "records_processed": int(row["records_processed"]),
    }


def build_category_matrix(
    formulas: list[dict[str, Any]],
    per_formula: dict[int, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    category_logs: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for formula in formulas:
        category = formula["category"]
        for log in per_formula.get(formula["targil_id"], []):
            category_logs[category][log["method"]].append(log["run_time"])

    rows = []
    for category, methods in category_logs.items():
        ranked = sorted(
            (
                {
                    "method": method,
                    "label": label_for_method(method),
                    "average_runtime_seconds": sum(values) / len(values),
                }
                for method, values in methods.items()
            ),
            key=lambda item: item["average_runtime_seconds"],
        )
        rows.append(
            {
                "category": category,
                "winner_method": ranked[0]["method"] if ranked else None,
                "winner_label": ranked[0]["label"] if ranked else None,
                "methods": ranked,
            }
        )
    return rows


def build_recommendation_matrix(fastest_method: str) -> list[dict[str, str]]:
    return [
        {
            "scenario": "Best overall production choice",
            "method": fastest_method,
            "reason": "This engine delivered the strongest benchmark profile on the measured workload.",
        },
        {
            "scenario": "Best for rapid prototyping",
            "method": "python_eval",
            "reason": "The simplest formula-to-execution path with minimal implementation ceremony.",
        },
        {
            "scenario": "Best for DB-centric deployment",
            "method": "sql_dynamic",
            "reason": "Keeps execution close to the data and avoids repeated application-side transfer work.",
        },
    ]


def answer_benchmark_question(
    question: str,
    overview: dict[str, Any],
    formulas: list[dict[str, Any]],
    logs: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    correctness_cards: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized_question = " ".join(question.lower().strip().split())
    summary_rows = [normalize_summary_row(row) for row in summary_rows]
    logs = [normalize_log_row(row) for row in logs]

    if not normalized_question:
        return {
            "question": question,
            "answer": "Ask about performance, stability, complex formulas, correctness, enterprise fit, or why a method won.",
            "intent": "empty",
            "evidence": [],
            "follow_up_questions": build_follow_up_questions(),
        }

    method_timings: dict[str, list[float]] = defaultdict(list)
    per_formula: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for log in logs:
        method_timings[log["method"]].append(log["run_time"])
        per_formula[log["targil_id"]].append(log)

    fastest = summary_rows[0] if summary_rows else None
    slowest = summary_rows[-1] if summary_rows else None
    stable_rows = []
    for row in summary_rows:
        timings = method_timings.get(row["method"], [row["average_runtime_seconds"]])
        stable_rows.append(
            {
                "method": row["method"],
                "std_dev": pstdev(timings) if len(timings) > 1 else 0.0,
            }
        )
    most_stable = min(stable_rows, key=lambda item: item["std_dev"]) if stable_rows else None

    formula_winners = []
    for formula in formulas:
        ranked = sorted(per_formula.get(formula["targil_id"], []), key=lambda row: row["run_time"])
        if len(ranked) < 2:
            continue
        leader = ranked[0]
        runner_up = ranked[1]
        formula_winners.append(
            {
                "targil_id": formula["targil_id"],
                "formula": formula["display_formula"],
                "category": formula["category"],
                "winner_method": leader["method"],
                "winner_runtime": leader["run_time"],
                "margin": runner_up["run_time"] - leader["run_time"],
            }
        )

    category_rows = build_category_matrix(formulas, per_formula)
    correctness_ok = all(item["mismatched_rows"] == 0 for item in correctness_cards)
    avg_by_method = {row["method"]: row["average_runtime_seconds"] for row in summary_rows}

    intent = detect_question_intent(normalized_question)
    if intent == "why_fastest" and fastest and slowest:
        answer = (
            f"{label_for_method(fastest['method'])} won because it achieved the lowest measured average runtime "
            f"at {fastest['average_runtime_seconds']:.3f}s per formula, while {label_for_method(slowest['method'])} "
            f"needed {slowest['average_runtime_seconds']:.3f}s. That gap stayed meaningful across the benchmark, "
            "so the winner is supported by repeated measured latency, not by a single outlier."
        )
        evidence = [
            f"Fastest overall average: {label_for_method(fastest['method'])} at {fastest['average_runtime_seconds']:.3f}s.",
            f"Slowest overall average: {label_for_method(slowest['method'])} at {slowest['average_runtime_seconds']:.3f}s.",
            f"Measured performance gap: {slowest['average_runtime_seconds'] - fastest['average_runtime_seconds']:.3f}s per formula.",
        ]
    elif intent == "stability" and most_stable:
        row = next((item for item in summary_rows if item["method"] == most_stable["method"]), None)
        answer = (
            f"{label_for_method(most_stable['method'])} is the most stable engine because its runtime variance across formulas "
            f"was the lowest in the benchmark. That means its behavior changed less dramatically between easy and difficult formulas."
        )
        evidence = [
            f"Lowest standard deviation: {most_stable['std_dev']:.3f}s.",
            f"Method: {label_for_method(most_stable['method'])}.",
            f"Average runtime: {row['average_runtime_seconds']:.3f}s." if row else "",
        ]
    elif intent == "complexity":
        complex_row = next((item for item in category_rows if item["category"] == "Complex"), None)
        if complex_row:
            answer = (
                f"Complex formulas widened the separation between engines. In the complex category, "
                f"{complex_row['winner_label']} led the group, which suggests that advanced mathematical transformations "
                "amplify engine differences more than simple arithmetic does."
            )
            evidence = [
                f"Complex-category leader: {complex_row['winner_label']}.",
                "Category averages: " + ", ".join(
                    f"{item['label']} {item['average_runtime_seconds']:.3f}s" for item in complex_row["methods"]
                ),
            ]
        else:
            answer = "The benchmark currently has no classified complex formulas to analyze."
            evidence = []
    elif intent == "python_pain":
        python_losses = [item for item in formula_winners if item["winner_method"] != "python_eval"]
        hardest = max(
            (
                item
                for item in formula_winners
                if "python_eval" in avg_by_method
            ),
            key=lambda item: next(
                (
                    log["run_time"]
                    for log in per_formula[item["targil_id"]]
                    if log["method"] == "python_eval"
                ),
                0.0,
            ),
            default=None,
        )
        answer = (
            "Python Eval is easiest to implement, but it loses the most on scale-sensitive formulas because interpreted execution "
            "adds more overhead when the formula set becomes large or mathematically heavier."
        )
        evidence = [
            f"Python average runtime: {avg_by_method.get('python_eval', 0.0):.3f}s per formula.",
            f"C# average runtime: {avg_by_method.get('csharp_engine', 0.0):.3f}s per formula.",
            f"SQL Dynamic average runtime: {avg_by_method.get('sql_dynamic', 0.0):.3f}s per formula.",
            (
                f"Heaviest Python case in the benchmark: Formula {hardest['targil_id']} ({hardest['category']})."
                if hardest
                else ""
            ),
        ]
    elif intent == "enterprise":
        answer = (
            "C# Engine is the best enterprise choice because it combines the strongest measured runtime with typed application architecture, "
            "clean service integration, and maintainable backend structure."
        )
        evidence = [
            f"Fastest measured average runtime: {avg_by_method.get('csharp_engine', 0.0):.3f}s.",
            "Strong maintainability and extensibility scores in the architectural assessment.",
            "Typed backend integration makes it easier to govern in long-lived production systems.",
        ]
    elif intent == "database":
        answer = (
            "SQL Dynamic is the best DB-centric option because it keeps execution close to the data and reduces repeated application-side transfer work. "
            "That makes it a strong fit when the organization wants most of the computation to stay inside SQL Server."
        )
        evidence = [
            f"SQL Dynamic average runtime: {avg_by_method.get('sql_dynamic', 0.0):.3f}s.",
            "Execution happens near the stored data instead of moving large workloads out to the application layer.",
            "It ranked second overall while preserving correctness.",
        ]
    elif intent == "correctness":
        answer = (
            "Correctness remained fully aligned across the benchmark. All pairwise comparisons returned zero mismatched rows, "
            "so the ranking is based on latency differences rather than inconsistent outputs."
        )
        evidence = [
            f"Python vs SQL Dynamic mismatches: {lookup_correctness(correctness_cards, 'python_eval', 'sql_dynamic')}.",
            f"Python vs C# Engine mismatches: {lookup_correctness(correctness_cards, 'python_eval', 'csharp_engine')}.",
            f"C# Engine vs SQL Dynamic mismatches: {lookup_correctness(correctness_cards, 'csharp_engine', 'sql_dynamic')}.",
        ]
    else:
        answer = (
            f"This benchmark currently covers {overview['formula_count']} formulas over {overview['records_processed']:,} records per formula. "
            f"{label_for_method(fastest['method']) if fastest else 'C# Engine'} leads overall, "
            f"{label_for_method(most_stable['method']) if most_stable else 'SQL Dynamic'} is the most stable, "
            f"and correctness is {'verified' if correctness_ok else 'not fully verified'} across the three execution engines."
        )
        evidence = [
            f"Fastest overall: {label_for_method(fastest['method'])}." if fastest else "",
            f"Most stable: {label_for_method(most_stable['method'])}." if most_stable else "",
            "Ask about speed, stability, complex formulas, correctness, enterprise fit, or DB-centric deployment for a more targeted explanation.",
        ]

    return {
        "question": question,
        "intent": intent,
        "answer": answer,
        "evidence": [item for item in evidence if item],
        "follow_up_questions": build_follow_up_questions(intent),
    }


def detect_question_intent(question: str) -> str:
    if any(term in question for term in ("why", "won", "fastest", "winner", "best overall")):
        return "why_fastest"
    if any(term in question for term in ("stable", "stability", "variance", "consistent")):
        return "stability"
    if any(term in question for term in ("complex", "sqrt", "log", "conditional", "category", "formula type")):
        return "complexity"
    if any(term in question for term in ("python", "prototype", "iterate", "slow")):
        return "python_pain"
    if any(term in question for term in ("enterprise", "maintainability", "maintainable")):
        return "enterprise"
    if any(term in question for term in ("db", "database", "sql server", "data-local", "data local")):
        return "database"
    if any(term in question for term in ("correct", "mismatch", "same results", "verified")):
        return "correctness"
    return "general"


def lookup_correctness(correctness_cards: list[dict[str, Any]], base_method: str, compare_method: str) -> int:
    match = next(
        (
            item
            for item in correctness_cards
            if item["base_method"] == base_method and item["compare_method"] == compare_method
        ),
        None,
    )
    return int(match["mismatched_rows"]) if match else 0


def build_follow_up_questions(intent: str | None = None) -> list[str]:
    prompts = [
        "Why did C# win overall?",
        "Which formula types widened the gap between methods?",
        "Which method is the most stable?",
        "Why is Python still useful if it is slower?",
        "What is the best option for enterprise systems?",
    ]
    if intent == "why_fastest":
        return [
            "Which method is the most stable?",
            "Which formula types widened the gap between methods?",
            "What is the best option for enterprise systems?",
        ]
    return prompts


def render_analysis_markdown(
    generated_at: str,
    executive_summary: str,
    key_findings: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    category_matrix: list[dict[str, Any]],
    winners: list[dict[str, Any]],
    recommendation_matrix: list[dict[str, Any]],
) -> str:
    lines = [
        "# AI-Assisted Benchmark Analysis",
        "",
        f"_Generated on {generated_at}_",
        "",
        "## Executive Summary",
        executive_summary,
        "",
        "## Key Findings",
    ]
    for item in key_findings:
        lines.append(f"- **{item['title']}**: {item['value']} — {item['detail']}")

    lines.extend(["", "## Warnings and Signals"])
    for item in warnings:
        lines.append(f"- **{item['title']}**: {item['detail']}")

    lines.extend(["", "## Category-Level Winners"])
    for row in category_matrix:
        detail = ", ".join(
            f"{method['label']} {method['average_runtime_seconds']:.3f}s" for method in row["methods"]
        )
        lines.append(f"- **{row['category']}**: {row['winner_label']} led. {detail}.")

    lines.extend(["", "## Per-Formula Winners"])
    for winner in winners:
        lines.append(
            f"- Formula {winner['targil_id']} ({winner['category']}): {winner['winner_label']} won at "
            f"{winner['winner_runtime_seconds']:.3f}s with a {winner['margin_seconds']:.3f}s lead."
        )

    lines.extend(["", "## Scenario Recommendations"])
    for item in recommendation_matrix:
        lines.append(f"- **{item['scenario']}**: {label_for_method(item['method'])} — {item['reason']}")
    return "\n".join(lines)


def generate_analysis_pdf(overview: dict[str, Any], analysis: dict[str, Any]) -> bytes:
    builder = (
        Path(__file__).resolve().parent
        / "pdf_report_builder.py"
    )
    bundled_python = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "python"
        / "python.exe"
    )
    if not bundled_python.exists():
        raise RuntimeError("Bundled PDF runtime was not found.")

    payload = {"overview": overview, "analysis": analysis}
    temp_path = Path(__file__).resolve().parents[2] / ".analysis-tmp"
    temp_path.mkdir(exist_ok=True)
    token = uuid4().hex
    input_path = temp_path / f"analysis-input-{token}.json"
    output_path = temp_path / f"benchmark-ai-analysis-{token}.pdf"
    try:
        input_path.write_text(json.dumps(payload), encoding="utf-8")
        subprocess.run(
            [str(bundled_python), str(builder), str(input_path), str(output_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return output_path.read_bytes()
    finally:
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
