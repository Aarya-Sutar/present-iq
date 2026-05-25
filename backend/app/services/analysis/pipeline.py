from dataclasses import asdict
import json

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analysis import Analysis
from app.models.presentation import Presentation
from app.models.slide import Slide
from app.services.analysis.contextual import build_evaluation_context
from app.services.analysis.llm_feedback import call_ollama
from app.services.analysis.reasoner import build_reasoning_audit
from app.services.analysis.scorer import compute_scores, scorecard_to_dict
from app.services.processing.classifier import classify_slide_text
from app.services.processing.framework_detector import detect_frameworks


settings = get_settings()


def build_slide_overview(slides: list[Slide], slide_insights_by_number: dict[int, dict]) -> list[dict]:
    overview = []
    for slide in slides:
        insight = slide_insights_by_number.get(slide.slide_number, {})
        overview.append(
            {
                "slide_number": slide.slide_number,
                "slide_title": slide.slide_title,
                "slide_category": slide.slide_category,
                "primary_framework": slide.primary_framework,
                "key_claim": insight.get("key_claim"),
                "evidence_status": insight.get("evidence_status"),
                "risk_flags": insight.get("risk_flags", []),
                "reasoning_note": insight.get("reasoning_note"),
                "classification_reason": slide.classification_reason,
                "framework_reason": slide.framework_reason,
            }
        )
    return overview


def process_presentation(db: Session, presentation: Presentation) -> list[Slide]:
    presentation.processing_status = "processing"
    db.commit()

    try:
        context = build_evaluation_context(
            case_prompt=presentation.case_prompt,
            explicit_domain_type=presentation.domain_type,
            raw_rubric=presentation.evaluation_rubric,
        )

        from app.services.parsing.loader import parse_presentation_file

        extracted_slides = parse_presentation_file(
            file_path=presentation.file_path,
            presentation_id=presentation.id,
        )

        db.query(Slide).filter(Slide.presentation_id == presentation.id).delete()
        db.commit()

        slides: list[Slide] = []
        total_slides = len(extracted_slides)

        for item in extracted_slides:
            combined_text = "\n".join(
                part for part in [item["extracted_text"], item["ocr_text"]] if part
            )

            classification = classify_slide_text(
                slide_text=combined_text,
                slide_title=item["slide_title"],
                slide_number=item["slide_number"],
                total_slides=total_slides,
                context_hint={
                    "domain_type": context.domain_type,
                    "expected_categories": context.expected_categories,
                    "expected_focus_areas": context.expected_focus_areas,
                    "expected_frameworks": context.expected_frameworks,
                    "prompt_brief": context.prompt_brief,
                },
            )

            framework_matches = detect_frameworks(
                slide_text=combined_text,
                slide_title=item["slide_title"],
                top_k=3,
                threshold=0.24,
                context_hint={
                    "domain_type": context.domain_type,
                    "expected_frameworks": context.expected_frameworks,
                    "prompt_brief": context.prompt_brief,
                },
            )

            slide = Slide(
                presentation_id=presentation.id,
                slide_number=item["slide_number"],
                slide_title=item["slide_title"],
                extracted_text=item["extracted_text"],
                ocr_text=item["ocr_text"],
                image_paths=item["image_paths"],
                slide_metadata=item["slide_metadata"],
                slide_category=classification.category,
                classification_confidence=classification.confidence,
                classification_reason=classification.reason,
                primary_framework=framework_matches[0].framework if framework_matches else None,
                framework_confidence=framework_matches[0].score if framework_matches else None,
                framework_reason=(
                    ", ".join(framework_matches[0].evidence)
                    if framework_matches
                    else None
                ),
                framework_matches=[asdict(match) for match in framework_matches],
            )
            db.add(slide)
            slides.append(slide)

        presentation.processing_status = "completed"
        db.commit()

        for slide in slides:
            db.refresh(slide)

        db.refresh(presentation)
        return slides

    except Exception:
        presentation.processing_status = "failed"
        db.commit()
        raise


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

    context = build_evaluation_context(
        case_prompt=presentation.case_prompt,
        explicit_domain_type=presentation.domain_type,
        raw_rubric=presentation.evaluation_rubric,
    )

    reasoning_audit = build_reasoning_audit(slides, context)

    scorecard = compute_scores(
        slides,
        case_prompt=presentation.case_prompt,
        domain_type=presentation.domain_type,
        evaluation_rubric=presentation.evaluation_rubric,
        reasoning_audit=reasoning_audit,
    )
    scorecard_dict = scorecard_to_dict(scorecard)
    slide_insights_by_number = {
        item["slide_number"]: item for item in reasoning_audit.slide_insights
    }
    slides_overview = build_slide_overview(slides, slide_insights_by_number)

    llm_result = call_ollama(
        context={
            "domain_type": presentation.domain_type,
            "problem_statement": context.problem_statement,
            "prompt_brief": context.prompt_brief,
            "expected_focus_areas": context.expected_focus_areas,
            "evaluation_criteria": context.evaluation_criteria,
            "reasoning_audit": {
                "prompt_alignment_score": reasoning_audit.prompt_alignment_score,
                "evidence_grounding_score": reasoning_audit.evidence_grounding_score,
                "unsupported_claims": reasoning_audit.unsupported_claims,
                "reasoning_gaps": reasoning_audit.reasoning_gaps,
            },
        },
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

    analysis.prompt_alignment_score = reasoning_audit.prompt_alignment_score
    analysis.evidence_grounding_score = reasoning_audit.evidence_grounding_score

    analysis.score_breakdown = scorecard.score_breakdown
    analysis.slide_insights = reasoning_audit.slide_insights
    analysis.unsupported_claims = reasoning_audit.unsupported_claims
    analysis.reasoning_gaps = reasoning_audit.reasoning_gaps

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