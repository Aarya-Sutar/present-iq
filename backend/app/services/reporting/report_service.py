from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analysis import Analysis
from app.models.presentation import Presentation
from app.models.report import Report
from app.models.slide import Slide
from app.services.reporting.pdf_builder import build_report_pdf

settings = get_settings()


def build_slide_payload(slides: list[Slide]) -> list[dict]:
    payload: list[dict] = []

    for slide in slides:
        payload.append(
            {
                "slide_number": slide.slide_number,
                "slide_title": slide.slide_title,
                "slide_category": slide.slide_category,
                "primary_framework": slide.primary_framework,
                "classification_reason": slide.classification_reason,
                "framework_reason": slide.framework_reason,
                "extracted_text": slide.extracted_text,
                "ocr_text": slide.ocr_text,
            }
        )

    return payload


def generate_presentation_report(db: Session, presentation: Presentation) -> Report:
    analysis = (
        db.query(Analysis)
        .filter(Analysis.presentation_id == presentation.id)
        .one_or_none()
    )

    if not analysis or analysis.analysis_status != "completed":
        raise ValueError("Analysis must be completed before generating a report.")

    slides = (
        db.query(Slide)
        .filter(Slide.presentation_id == presentation.id)
        .order_by(Slide.slide_number.asc())
        .all()
    )

    if not slides:
        raise ValueError("No slides found for this presentation.")

    existing = (
        db.query(Report)
        .filter(Report.presentation_id == presentation.id)
        .one_or_none()
    )

    if existing is None:
        report = Report(
            presentation_id=presentation.id,
            report_status="processing",
        )
        db.add(report)
    else:
        report = existing
        report.report_status = "processing"
        report.error_message = None

    db.commit()
    db.refresh(report)

    report_dir = Path(settings.reports_dir) / str(presentation.id)
    report_dir.mkdir(parents=True, exist_ok=True)

    filename = f"PresentIQ_Report_{presentation.id}_{uuid4().hex[:8]}.pdf"
    output_path = report_dir / filename

    presentation_payload = {
        "id": presentation.id,
        "case_prompt": presentation.case_prompt,
        "domain_type": presentation.domain_type,
        "evaluation_rubric": presentation.evaluation_rubric,
        "original_filename": presentation.original_filename,
    }

    analysis_payload = {
        "analysis_status": analysis.analysis_status,
        "business_logic_score": analysis.business_logic_score,
        "strategy_strength_score": analysis.strategy_strength_score,
        "analytical_depth_score": analysis.analytical_depth_score,
        "financial_soundness_score": analysis.financial_soundness_score,
        "communication_clarity_score": analysis.communication_clarity_score,
        "framework_utilization_score": analysis.framework_utilization_score,
        "overall_presentation_quality_score": analysis.overall_presentation_quality_score,
        "score_breakdown": analysis.score_breakdown or {},
        "strengths": analysis.strengths or [],
        "weaknesses": analysis.weaknesses or [],
        "missing_elements": analysis.missing_elements or [],
        "recommendations": analysis.recommendations or [],
        "investor_questions": analysis.investor_questions or [],
        "executive_summary": analysis.executive_summary,
        "consultant_feedback": analysis.consultant_feedback,
    }

    slides_payload = build_slide_payload(slides)

    build_report_pdf(
        output_path=str(output_path),
        presentation=presentation_payload,
        analysis=analysis_payload,
        slides=slides_payload,
    )

    report.report_status = "completed"
    report.report_filename = filename
    report.report_file_path = str(output_path)
    report.report_summary = analysis.executive_summary
    report.generated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)

    return report