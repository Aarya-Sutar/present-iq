import json

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analysis import Analysis
from app.models.presentation import Presentation
from app.models.slide import Slide
from app.services.analysis.llm_feedback import call_ollama
from app.services.analysis.scorer import compute_scores, scorecard_to_dict


settings = get_settings()


def build_slide_overview(slides: list[Slide]) -> list[dict]:
    overview = []
    for slide in slides:
        overview.append(
            {
                "slide_number": slide.slide_number,
                "slide_title": slide.slide_title,
                "slide_category": slide.slide_category,
                "primary_framework": slide.primary_framework,
                "classification_reason": slide.classification_reason,
                "framework_reason": slide.framework_reason,
            }
        )
    return overview


def generate_presentation_analysis(db: Session, presentation: Presentation) -> Analysis:
    slides = (
        db.query(Slide)
        .filter(Slide.presentation_id == presentation.id)
        .order_by(Slide.slide_number.asc())
        .all()
    )

    if not slides:
        raise ValueError("No extracted slides found. Run slide extraction first.")

    existing = (
        db.query(Analysis)
        .filter(Analysis.presentation_id == presentation.id)
        .one_or_none()
    )

    if existing is None:
        analysis = Analysis(
            presentation_id=presentation.id,
            analysis_status="processing",
        )
        db.add(analysis)
    else:
        analysis = existing
        analysis.analysis_status = "processing"

    db.commit()
    db.refresh(analysis)

    scorecard = compute_scores(
        slides,
        case_prompt=presentation.case_prompt,
        domain_type=presentation.domain_type,
        evaluation_rubric=presentation.evaluation_rubric,
    )
    scorecard_dict = scorecard_to_dict(scorecard)
    slides_overview = build_slide_overview(slides)

    context = {
        "case_prompt": presentation.case_prompt,
        "domain_type": presentation.domain_type,
        "evaluation_rubric": presentation.evaluation_rubric,
    }

    llm_result = call_ollama(
        context=context,
        scorecard=scorecard_dict,
        presentation_summary=scorecard.presentation_summary,
        slides_overview=slides_overview,
    )

    analysis.analysis_status = "completed"
    analysis.business_logic_score = scorecard.business_logic_score
    analysis.strategy_strength_score = scorecard.strategy_strength_score
    analysis.analytical_depth_score = scorecard.analytical_depth_score
    analysis.financial_soundness_score = scorecard.financial_soundness_score
    analysis.communication_clarity_score = scorecard.communication_clarity_score
    analysis.framework_utilization_score = scorecard.framework_utilization_score
    analysis.overall_presentation_quality_score = scorecard.overall_presentation_quality_score

    analysis.score_breakdown = scorecard.score_breakdown
    analysis.strengths = list(llm_result.get("strengths", scorecard.strengths))
    analysis.weaknesses = list(llm_result.get("weaknesses", scorecard.weaknesses))
    analysis.missing_elements = list(llm_result.get("missing_elements", scorecard.missing_elements))
    analysis.recommendations = list(llm_result.get("recommendations", scorecard.recommendations))
    analysis.investor_questions = list(llm_result.get("investor_questions", scorecard.investor_questions))
    analysis.executive_summary = llm_result.get("executive_summary")
    analysis.consultant_feedback = llm_result.get("consultant_feedback")
    analysis.raw_llm_output = json.dumps(llm_result, ensure_ascii=False)
    analysis.model_name = settings.ollama_model

    db.commit()
    db.refresh(analysis)
    return analysis