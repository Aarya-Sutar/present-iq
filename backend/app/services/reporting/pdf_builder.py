from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import get_settings

settings = get_settings()


def sanitize_pdf_text(text: str | None) -> str:
    if not text:
        return ""
    text = text.replace("\u20b9", "Rs.")
    text = text.replace("₹", "Rs.")
    text = text.replace("—", "-")
    text = text.replace("–", "-")
    text = text.replace("\u00ad", "")
    return text


def truncate(text: str | None, limit: int = 180) -> str:
    cleaned = sanitize_pdf_text(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawString(40, 20, "PresentIQ - Contextual Evaluation Report")
    canvas.drawRightString(
        A4[0] - 40,
        20,
        f"Page {doc.page}",
    )
    canvas.restoreState()


def _score_row(label: str, value: Any) -> list[str]:
    if value is None:
        display = "N/A"
    else:
        display = f"{round(float(value))}"
    return [label, display]


def build_report_pdf(
    output_path: str,
    presentation: dict,
    analysis: dict,
    slides: list[dict],
) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CenterTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            spaceBefore=10,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTiny",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            spaceAfter=4,
        )
    )

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=42,
        bottomMargin=36,
        title="PresentIQ Analysis Report",
        author="PresentIQ",
    )

    story: list[Any] = []

    case_prompt = sanitize_pdf_text(presentation.get("case_prompt", ""))
    domain_type = sanitize_pdf_text(presentation.get("domain_type", "general"))
    file_name = sanitize_pdf_text(presentation.get("original_filename", ""))

    story.append(Paragraph("PresentIQ", styles["CenterTitle"]))
    story.append(Paragraph("Contextual Presentation Evaluation Report", styles["Heading2"]))
    story.append(Spacer(1, 0.15 * inch))

    meta_table = Table(
        [
            ["File", file_name],
            ["Domain", domain_type],
            ["Analysis Status", sanitize_pdf_text(analysis.get("analysis_status", ""))],
        ],
        colWidths=[1.4 * inch, 4.8 * inch],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Case Context", styles["SectionTitle"]))
    story.append(Paragraph(case_prompt or "No case prompt provided.", styles["BodySmall"]))

    rubric = presentation.get("evaluation_rubric") or {}
    story.append(Paragraph("Evaluation Rubric", styles["SectionTitle"]))
    if rubric:
        story.append(Paragraph(sanitize_pdf_text(str(rubric)), styles["BodyTiny"]))
    else:
        story.append(Paragraph("No rubric provided.", styles["BodySmall"]))

    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("Scorecard", styles["SectionTitle"]))
    score_rows = [
        _score_row("Business Logic", analysis.get("business_logic_score")),
        _score_row("Strategy Strength", analysis.get("strategy_strength_score")),
        _score_row("Analytical Depth", analysis.get("analytical_depth_score")),
        _score_row("Financial Soundness", analysis.get("financial_soundness_score")),
        _score_row("Communication Clarity", analysis.get("communication_clarity_score")),
        _score_row("Framework Utilization", analysis.get("framework_utilization_score")),
        _score_row("Overall Quality", analysis.get("overall_presentation_quality_score")),
    ]
    score_table = Table([["Metric", "Score"]] + score_rows, colWidths=[4.2 * inch, 1.0 * inch])
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(score_table)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Executive Summary", styles["SectionTitle"]))
    story.append(
        Paragraph(
            sanitize_pdf_text(analysis.get("executive_summary"))
            or "No executive summary available.",
            styles["BodySmall"],
        )
    )

    story.append(Paragraph("Consultant Feedback", styles["SectionTitle"]))
    story.append(
        Paragraph(
            sanitize_pdf_text(analysis.get("consultant_feedback"))
            or "No consultant feedback available.",
            styles["BodySmall"],
        )
    )

    story.append(Spacer(1, 0.1 * inch))

    def build_bullet_list(title: str, items: list[str]):
        story.append(Paragraph(title, styles["SectionTitle"]))
        if not items:
            story.append(Paragraph("None", styles["BodySmall"]))
            return
        for item in items:
            story.append(Paragraph(f"- {sanitize_pdf_text(item)}", styles["BodySmall"]))

    build_bullet_list("Strengths", analysis.get("strengths", []))
    build_bullet_list("Weaknesses", analysis.get("weaknesses", []))
    build_bullet_list("Missing Elements", analysis.get("missing_elements", []))
    build_bullet_list("Recommendations", analysis.get("recommendations", []))
    build_bullet_list("Investor Questions", analysis.get("investor_questions", []))

    story.append(PageBreak())

    story.append(Paragraph("Slide-by-Slide Summary", styles["SectionTitle"]))
    slide_table_data = [
        [
            "Slide",
            "Title",
            "Category",
            "Framework",
            "Summary",
        ]
    ]

    for slide in slides:
        framework = slide.get("primary_framework") or "None"
        summary_bits = []
        if slide.get("classification_reason"):
            summary_bits.append(f"Category: {slide['classification_reason']}")
        if slide.get("framework_reason"):
            summary_bits.append(f"Framework: {slide['framework_reason']}")

        slide_table_data.append(
            [
                str(slide.get("slide_number", "")),
                sanitize_pdf_text(slide.get("slide_title") or "Untitled"),
                sanitize_pdf_text(slide.get("slide_category") or "Unclassified"),
                sanitize_pdf_text(framework),
                sanitize_pdf_text(" | ".join(summary_bits))[:220],
            ]
        )

    slide_table = Table(
        slide_table_data,
        colWidths=[0.5 * inch, 1.3 * inch, 1.25 * inch, 1.2 * inch, 2.6 * inch],
        repeatRows=1,
    )
    slide_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.8),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ]
        )
    )
    story.append(slide_table)

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Framework Summary", styles["SectionTitle"]))
    framework_counts = analysis.get("score_breakdown", {}).get("frameworks_present", [])
    if framework_counts:
        for item in framework_counts:
            story.append(Paragraph(f"- {sanitize_pdf_text(str(item))}", styles["BodySmall"]))
    else:
        story.append(Paragraph("No framework summary available.", styles["BodySmall"]))

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return str(output)