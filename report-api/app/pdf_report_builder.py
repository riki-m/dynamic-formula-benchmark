from __future__ import annotations

import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def label_for_method(method: str) -> str:
    return {
        "csharp_engine": "C# Engine",
        "sql_dynamic": "SQL Dynamic",
        "python_eval": "Python Eval",
    }.get(method, method)


def build_pdf(payload: dict, output_path: Path) -> None:
    overview = payload["overview"]
    analysis = payload["analysis"]

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        title="Dynamic Formula Benchmark Intelligence Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#102028"),
        alignment=TA_LEFT,
        spaceAfter=12,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#5b6d69"),
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#102028"),
        spaceBefore=12,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#24343d"),
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body_style,
        leftIndent=10,
        bulletIndent=0,
        spaceAfter=4,
    )

    story = []
    story.append(Paragraph("Dynamic Formula Intelligence Report", title_style))
    story.append(
        Paragraph(
            f"Dynamic Benchmark Intelligence Report generated from measured SQL Server results on {analysis['generated_at']}.",
            subtitle_style,
        )
    )
    story.append(
        Paragraph(
            f"Scope: {overview['records_processed']:,} records per formula · {overview['formula_count']} formulas · {overview['execution_engines']} execution engines.",
            subtitle_style,
        )
    )

    cover_table = Table(
        [
            ["Correctness", "Verified"],
            ["Fastest Overall", label_for_method(analysis["fastest_method"])],
            ["Most Stable", label_for_method(analysis["most_stable_method"])],
            ["Performance Gap", f"{analysis['performance_gap_seconds']:.3f}s per formula"],
        ],
        colWidths=[48 * mm, 110 * mm],
    )
    cover_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef4f1")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#102028")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#d7e2dc")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(cover_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Executive Summary", section_style))
    story.append(Paragraph(analysis["executive_summary"], body_style))

    story.append(Paragraph("Correctness Verification", section_style))
    for item in analysis["correctness_cards"]:
        story.append(
            Paragraph(
                f"- {item['label']}: mismatched_rows = {item['mismatched_rows']}",
                bullet_style,
            )
        )

    story.append(Paragraph("Performance Summary", section_style))
    summary_data = [["Method", "Avg (s)", "Best (s)", "Worst (s)", "Total (s)"]]
    for row in analysis["summary_rows"]:
        summary_data.append(
            [
                label_for_method(row["method"]),
                f"{row['average_runtime_seconds']:.3f}",
                f"{row['best_runtime_seconds']:.3f}",
                f"{row['worst_runtime_seconds']:.3f}",
                f"{row['total_runtime_seconds']:.3f}",
            ]
        )
    summary_table = Table(summary_data, colWidths=[42 * mm, 28 * mm, 28 * mm, 28 * mm, 28 * mm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#102028")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fbf9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d7e2dc")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)

    story.append(Paragraph("Key Findings", section_style))
    for item in analysis["key_findings"]:
        story.append(Paragraph(f"- <b>{item['title']}</b>: {item['detail']}", bullet_style))

    story.append(Paragraph("Warnings and Signals", section_style))
    for item in analysis["warnings"]:
        story.append(Paragraph(f"- <b>{item['title']}</b>: {item['detail']}", bullet_style))

    story.append(Paragraph("Formula-Level Winners", section_style))
    winners_data = [["Formula", "Category", "Winner", "Runtime (s)", "Margin (s)"]]
    for item in analysis["formula_winners"]:
        winners_data.append(
            [
                str(item["targil_id"]),
                item["category"],
                item["winner_label"],
                f"{item['winner_runtime_seconds']:.3f}",
                f"{item['margin_seconds']:.3f}",
            ]
        )
    winners_table = Table(winners_data, colWidths=[18 * mm, 34 * mm, 46 * mm, 26 * mm, 24 * mm])
    winners_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dff0eb")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7e2dc")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(winners_table)

    story.append(Paragraph("Scenario Recommendations", section_style))
    for item in analysis["recommendation_matrix"]:
        story.append(
            Paragraph(
                f"- <b>{item['scenario']}</b>: {label_for_method(item['method'])} - {item['reason']}",
                bullet_style,
            )
        )

    story.append(Paragraph("Dynamic Intelligence Interpretation Layer", section_style))
    story.append(
        Paragraph(
            "This report was generated locally from measured benchmark data. It does not replace Python, C#, or SQL execution, and it does not claim live cloud LLM inference. Its value is in dynamic interpretation, ranking, warning detection, and report-quality narrative generation.",
            body_style,
        )
    )

    doc.build(story)


def main() -> None:
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    build_pdf(payload, output_path)


if __name__ == "__main__":
    main()


