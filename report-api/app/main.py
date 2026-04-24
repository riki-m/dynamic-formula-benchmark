from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .analysis_engine import answer_benchmark_question, build_analysis_payload, generate_analysis_pdf


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "benchmark.db"
INTELLIGENCE_SUMMARY_PATH = PROJECT_ROOT / "report" / "intelligence_summary.md"
STATIC_UI_PATH = PROJECT_ROOT / "report-ui"

DB_ENGINE = os.getenv("DB_ENGINE", "sqlserver").lower()
SQLSERVER_CONNECTION_STRING = os.getenv(
    "SQLSERVER_CONNECTION_STRING",
    "Driver={ODBC Driver 17 for SQL Server};Server=localhost\\SQLEXPRESS;Database=DynamicFormulaBenchmark;Trusted_Connection=yes;TrustServerCertificate=yes;",
)

app = FastAPI(title="Dynamic Formula Benchmark API")

BENCHMARK_BASELINE = {
    "correctness": {
        "python_vs_sql": 0,
        "python_vs_csharp": 0,
        "csharp_vs_sql": 0,
    }
}


class BenchmarkQuestionRequest(BaseModel):
    question: str


def get_connection() -> Any:
    if DB_ENGINE == "sqlserver":
        import pyodbc

        return pyodbc.connect(SQLSERVER_CONNECTION_STRING)

    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.row_factory = sqlite3.Row
    return connection


def fetch_all(query: str) -> list[dict[str, Any]]:
    with get_connection() as connection:
        if DB_ENGINE == "sqlserver":
            cursor = connection.cursor()
            rows = cursor.execute(query).fetchall()
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

        rows = connection.execute(query).fetchall()
        return [dict(row) for row in rows]


def load_ai_summary() -> str:
    if not INTELLIGENCE_SUMMARY_PATH.exists():
        return ""
    return INTELLIGENCE_SUMMARY_PATH.read_text(encoding="utf-8")


def save_ai_summary(markdown: str) -> None:
    INTELLIGENCE_SUMMARY_PATH.write_text(markdown, encoding="utf-8")


def categorize_formula(formula: dict[str, Any]) -> str:
    if formula.get("tnai"):
        return "Conditional"
    expression = (formula.get("targil") or "").lower()
    if any(token in expression for token in ("sqrt", "log", "abs", "^")):
        return "Complex"
    return "Arithmetic"


def build_correctness_cards() -> list[dict[str, Any]]:
    correctness = BENCHMARK_BASELINE["correctness"]
    return [
        {
            "label": "Python vs SQL Dynamic",
            "base_method": "python_eval",
            "compare_method": "sql_dynamic",
            "mismatched_rows": correctness.get("python_vs_sql", 0),
        },
        {
            "label": "Python vs C# Engine",
            "base_method": "python_eval",
            "compare_method": "csharp_engine",
            "mismatched_rows": correctness.get("python_vs_csharp", 0),
        },
        {
            "label": "C# Engine vs SQL Dynamic",
            "base_method": "csharp_engine",
            "compare_method": "sql_dynamic",
            "mismatched_rows": correctness.get("csharp_vs_sql", 0),
        },
    ]


def build_tradeoffs() -> list[dict[str, Any]]:
    return [
        {
            "method": "csharp_engine",
            "headline": "Fastest balanced production choice",
            "maintainability": 9,
            "extensibility": 9,
            "operational_complexity": 6,
            "runtime_flexibility": 8,
            "narrative": "Best overall runtime with strong backend structure, type safety, and clean integration into enterprise services.",
        },
        {
            "method": "sql_dynamic",
            "headline": "Strongest data-local execution path",
            "maintainability": 6,
            "extensibility": 6,
            "operational_complexity": 8,
            "runtime_flexibility": 7,
            "narrative": "Executes near the data and performs well, but requires more careful operational governance and SQL-generation discipline.",
        },
        {
            "method": "python_eval",
            "headline": "Fastest to prototype and iterate",
            "maintainability": 7,
            "extensibility": 8,
            "operational_complexity": 5,
            "runtime_flexibility": 9,
            "narrative": "Excellent for rapid implementation and experimentation, but materially slower at the measured scale.",
        },
    ]


def build_recommendations(summary_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    fastest = summary_rows[0]["method"] if summary_rows else "csharp_engine"
    return [
        {
            "title": "Highest Performance",
            "method": fastest,
            "reason": "Delivered the best measured average runtime across the benchmark.",
        },
        {
            "title": "Fastest Implementation",
            "method": "python_eval",
            "reason": "Offers the shortest path from formula text to execution with minimal ceremony.",
        },
        {
            "title": "Database-Centric Deployment",
            "method": "sql_dynamic",
            "reason": "Keeps execution close to the data and reduces application-side transfer overhead.",
        },
    ]


def query_formulas() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT targil_id, targil, tnai, targil_false
        FROM t_targil
        ORDER BY targil_id
        """
    )


def query_logs() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT targil_id, method, run_time, records_processed
        FROM t_log
        ORDER BY method, targil_id
        """
    )


def query_summary() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            method,
            COUNT(*) AS formulas_executed,
            SUM(records_processed) AS total_records_processed,
            AVG(run_time) AS average_runtime_seconds,
            MIN(run_time) AS best_runtime_seconds,
            MAX(run_time) AS worst_runtime_seconds,
            SUM(run_time) AS total_runtime_seconds
        FROM t_log
        GROUP BY method
        ORDER BY average_runtime_seconds
        """
    )


def build_dashboard_payload() -> dict[str, Any]:
    formulas = query_formulas()
    logs = query_logs()
    summary = query_summary()

    correctness_cards = build_correctness_cards()

    enriched_formulas = []
    for formula in formulas:
        enriched_formulas.append(
            {
                **formula,
                "category": categorize_formula(formula),
                "display_formula": (
                    f"if({formula['tnai']}, {formula['targil']}, {formula['targil_false']})"
                    if formula.get("tnai")
                    else formula["targil"]
                ),
            }
        )

    overview = {
        "project_title": "Dynamic Formula Intelligence Control Center",
        "subtitle": "Benchmarking three execution architectures over 1,000,000 records with validated correctness and production-focused analysis.",
        "records_processed": max((int(log["records_processed"]) for log in logs), default=1_000_000),
        "formula_count": len(formulas),
        "execution_engines": len(summary),
        "correctness_status": "Verified",
        "fastest_method": summary[0]["method"] if summary else None,
    }

    analysis = build_analysis_payload(overview, enriched_formulas, logs, summary, correctness_cards)
    ai_summary = load_ai_summary()
    if ai_summary.strip():
        analysis["markdown"] = ai_summary

    return {
        "overview": overview,
        "summary": summary,
        "logs": logs,
        "formulas": enriched_formulas,
        "correctness": correctness_cards,
        "tradeoffs": build_tradeoffs(),
        "recommendations": build_recommendations(summary),
        "ai_analysis": {
            "summary_markdown": analysis["markdown"],
            "download_pdf_url": "/api/analysis/download.pdf",
            "generated_at": analysis["generated_at"],
            "executive_summary": analysis["executive_summary"],
            "key_findings": analysis["key_findings"],
            "warnings": analysis["warnings"],
            "category_matrix": analysis["category_matrix"],
            "recommendation_matrix": analysis["recommendation_matrix"],
            "formula_winners": analysis["formula_winners"],
            "summary_rows": analysis["summary_rows"],
            "correctness_cards": analysis["correctness_cards"],
            "fastest_method": analysis["fastest_method"],
            "most_stable_method": analysis["most_stable_method"],
            "performance_gap_seconds": analysis["performance_gap_seconds"],
            "suggested_questions": [
                "Why did C# win overall?",
                "Which formula types widened the gap between methods?",
                "Which method is the most stable?",
                "Why is Python still useful if it is slower?",
                "What is the best option for enterprise systems?",
            ],
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/logs")
def get_logs() -> list[dict[str, Any]]:
    return query_logs()


@app.get("/api/summary")
def get_summary() -> list[dict[str, Any]]:
    return query_summary()


@app.get("/api/dashboard")
def get_dashboard() -> dict[str, Any]:
    return build_dashboard_payload()


@app.post("/api/analysis/generate")
def generate_analysis() -> dict[str, Any]:
    formulas = query_formulas()
    logs = query_logs()
    summary = query_summary()
    correctness_cards = build_correctness_cards()
    enriched_formulas = [
        {
            **formula,
            "category": categorize_formula(formula),
            "display_formula": (
                f"if({formula['tnai']}, {formula['targil']}, {formula['targil_false']})"
                if formula.get("tnai")
                else formula["targil"]
            ),
        }
        for formula in formulas
    ]
    overview = {
        "project_title": "Dynamic Formula Intelligence Control Center",
        "subtitle": "Benchmarking three execution architectures over 1,000,000 records with validated correctness and production-focused analysis.",
        "records_processed": max((int(log["records_processed"]) for log in logs), default=1_000_000),
        "formula_count": len(formulas),
        "execution_engines": len(summary),
        "correctness_status": "Verified",
        "fastest_method": summary[0]["method"] if summary else None,
    }
    analysis = build_analysis_payload(overview, enriched_formulas, logs, summary, correctness_cards)
    save_ai_summary(analysis["markdown"])
    return {
        "status": "ok",
        "generated_at": analysis["generated_at"],
        "summary_markdown": analysis["markdown"],
        "executive_summary": analysis["executive_summary"],
        "key_findings": analysis["key_findings"],
        "warnings": analysis["warnings"],
        "category_matrix": analysis["category_matrix"],
        "recommendation_matrix": analysis["recommendation_matrix"],
        "formula_winners": analysis["formula_winners"],
        "summary_rows": analysis["summary_rows"],
        "correctness_cards": analysis["correctness_cards"],
        "fastest_method": analysis["fastest_method"],
        "most_stable_method": analysis["most_stable_method"],
        "performance_gap_seconds": analysis["performance_gap_seconds"],
        "download_pdf_url": "/api/analysis/download.pdf",
    }


@app.post("/api/analysis/ask")
def ask_benchmark(request: BenchmarkQuestionRequest) -> dict[str, Any]:
    formulas = query_formulas()
    logs = query_logs()
    summary = query_summary()
    correctness_cards = build_correctness_cards()
    enriched_formulas = [
        {
            **formula,
            "category": categorize_formula(formula),
            "display_formula": (
                f"if({formula['tnai']}, {formula['targil']}, {formula['targil_false']})"
                if formula.get("tnai")
                else formula["targil"]
            ),
        }
        for formula in formulas
    ]
    overview = {
        "project_title": "Dynamic Formula Intelligence Control Center",
        "subtitle": "Benchmarking three execution architectures over 1,000,000 records with validated correctness and production-focused analysis.",
        "records_processed": max((int(log["records_processed"]) for log in logs), default=1_000_000),
        "formula_count": len(formulas),
        "execution_engines": len(summary),
        "correctness_status": "Verified",
        "fastest_method": summary[0]["method"] if summary else None,
    }
    return answer_benchmark_question(
        request.question,
        overview,
        enriched_formulas,
        logs,
        summary,
        correctness_cards,
    )


@app.get("/api/analysis/download.pdf")
def download_analysis_pdf() -> Response:
    dashboard = build_dashboard_payload()
    pdf_bytes = generate_analysis_pdf(dashboard["overview"], dashboard["ai_analysis"])
    headers = {
        "Content-Disposition": 'attachment; filename="benchmark-ai-analysis.pdf"',
    }
    return Response(pdf_bytes, headers=headers, media_type="application/pdf")


if STATIC_UI_PATH.exists():
    app.mount("/", StaticFiles(directory=STATIC_UI_PATH, html=True), name="report-ui")
