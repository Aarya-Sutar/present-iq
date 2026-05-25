from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import get_settings
from app.services.analysis.contextual import build_evaluation_context
from app.services.analysis.reasoner import build_reasoning_audit

def truncate_text(text: str, max_length: int = 100) -> str:
    if not text:
        return ""

    text = text.strip().replace("\n", " ")

    if len(text) <= max_length:
        return text

    return text[:max_length] + "..."

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


def _page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawString(40, 20, "DeckLens - Contextual Evaluation Report")
    page_width = canvas._pagesize[0]
    canvas.drawRightString(page_width - 40, 20, f"Page {doc.page}")
    canvas.restoreState()


def _score_row(label: str, value: Any) -> list[str]:
    if value is None:
        display = "N/A"
    else:
        display = f"{round(float(value))}"
    return [label, display]


def _as_reasoning_slide(slide: dict) -> SimpleNamespace:
    return SimpleNamespace(
        slide_number=slide.get("slide_number", 0),
        slide_title=slide.get("slide_title"),
        extracted_text=slide.get("extracted_text", "") or "",
        ocr_text=slide.get("ocr_text", "") or "",
        slide_category=slide.get("slide_category"),
    )


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
        rightMargin=30,
        leftMargin=30,
        topMargin=42,
        bottomMargin=36,
        title="DeckLens Analysis Report",
        author="DeckLens",
    )

    story: list[Any] = []

    case_prompt = sanitize_pdf_text(presentation.get("case_prompt", ""))
    domain_type = sanitize_pdf_text(presentation.get("domain_type", "general"))
    file_name = sanitize_pdf_text(presentation.get("original_filename", ""))
    reasoning_context = build_evaluation_context(
        case_prompt=presentation.get("case_prompt", ""),
        explicit_domain_type=presentation.get("domain_type"),
        raw_rubric=presentation.get("evaluation_rubric"),
    )
    reasoning_audit = build_reasoning_audit(
        [_as_reasoning_slide(slide) for slide in slides],
        reasoning_context,
    )

    story.append(Paragraph("DeckLens", styles["CenterTitle"]))
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
            sanitize_pdf_text(analysis.get("executive_summary")) or "No executive summary available.",
            styles["BodySmall"],
        )
    )

    story.append(Paragraph("Consultant Feedback", styles["SectionTitle"]))
    story.append(
        Paragraph(
            sanitize_pdf_text(analysis.get("consultant_feedback")) or "No consultant feedback available.",
            styles["BodySmall"],
        )
    )

    story.append(Paragraph("Reasoning Audit", styles["SectionTitle"]))

    def build_bullet_list(title: str, items: list[str], empty_message: str = "None"):
        story.append(Paragraph(title, styles["SectionTitle"]))
        if not items:
            story.append(Paragraph(empty_message, styles["BodySmall"]))
            return
        for item in items:
            story.append(Paragraph(f"- {sanitize_pdf_text(item)}", styles["BodySmall"]))

    build_bullet_list("Reasoning Gaps", reasoning_audit.reasoning_gaps)
    build_bullet_list("Unsupported Claims", reasoning_audit.unsupported_claims)

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return str(output)