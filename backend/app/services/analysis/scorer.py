from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict
import re
from typing import Any

from app.models.slide import Slide
from app.services.analysis.contextual import EvaluationContext, build_evaluation_context


def clamp(score: float) -> float:
    return round(max(0.0, min(100.0, score)), 1)


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s%$.-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_any(text: str, terms: list[str]) -> bool:
    text = normalize(text)
    return any(term in text for term in terms)


def detect_present_categories(slides: list[Slide]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for slide in slides:
        if slide.slide_category:
            counter[slide.slide_category] += 1
    return counter


def detect_present_frameworks(slides: list[Slide]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for slide in slides:
        if slide.primary_framework:
            counter[slide.primary_framework] += 1

        for match in slide.framework_matches or []:
            framework = match.get("framework")
            if framework:
                counter[framework] += 1
    return counter


def build_presentation_summary(
    slides: list[Slide],
    context: EvaluationContext,
) -> dict:
    categories = detect_present_categories(slides)
    frameworks = detect_present_frameworks(slides)

    total_words = 0
    titled_slides = 0

    for slide in slides:
        text = f"{slide.extracted_text or ''} {slide.ocr_text or ''}".strip()
        total_words += len(text.split())
        if slide.slide_title:
            titled_slides += 1

    slide_count = len(slides)
    avg_words_per_slide = round(total_words / slide_count, 1) if slide_count else 0.0

    return {
        "slide_count": slide_count,
        "domain_type": context.domain_type,
        "case_prompt": context.case_prompt,
        "prompt_brief": context.prompt_brief,
        "problem_statement": context.problem_statement,
        "expected_focus_areas": context.expected_focus_areas,
        "evaluation_criteria": context.evaluation_criteria,
        "rubric_topics": context.rubric_topics,
        "categories_present": list(categories.keys()),
        "frameworks_present": list(frameworks.keys()),
        "titled_slides": titled_slides,
        "title_ratio": round(titled_slides / slide_count, 2) if slide_count else 0.0,
        "total_words": total_words,
        "avg_words_per_slide": avg_words_per_slide,
    }


@dataclass
class Scorecard:
    business_logic_score: float
    strategy_strength_score: float
    analytical_depth_score: float
    financial_soundness_score: float
    communication_clarity_score: float
    framework_utilization_score: float
    overall_presentation_quality_score: float
    prompt_alignment_score: float
    score_breakdown: dict
    strengths: list[str]
    weaknesses: list[str]
    missing_elements: list[str]
    recommendations: list[str]
    investor_questions: list[str]
    presentation_summary: dict


def score_overlap(present_items: set[str], expected_items: list[str]) -> float:
    if not expected_items:
        return 0.0
    hits = sum(1 for item in expected_items if item in present_items)
    return hits / len(expected_items)


def compute_scores(
    slides: list[Slide],
    case_prompt: str = "",
    domain_type: str = "general",
    evaluation_rubric: dict | None = None,
    reasoning_audit: Any | None = None,
) -> Scorecard:
    context = build_evaluation_context(
        case_prompt=case_prompt,
        explicit_domain_type=domain_type,
        raw_rubric=evaluation_rubric or {},
    )

    categories = detect_present_categories(slides)
    frameworks = detect_present_frameworks(slides)

    present_categories = set(categories.keys())
    present_frameworks = set(frameworks.keys())

    summary = build_presentation_summary(slides, context)

    prompt_alignment = score_overlap(present_categories, context.expected_categories)
    framework_alignment = score_overlap(present_frameworks, context.expected_frameworks)

    joined_text = " ".join(
        f"{slide.extracted_text or ''} {slide.ocr_text or ''}" for slide in slides
    ).lower()

    has_solution_language = contains_any(
        joined_text,
        [
            "solution",
            "proposed",
            "implementation",
            "workflow",
            "process",
            "plan",
            "approach",
            "execution",
        ],
    )
    has_numbers = contains_any(joined_text, ["%", "$", "rs", "lakh", "crore", "kpi", "metric", "timeline"])
    has_comparison = contains_any(joined_text, ["vs", "competitor", "alternative", "benchmark", "compare"])

    business_logic = 20.0
    business_logic += prompt_alignment * 45.0
    business_logic += 10.0 if "Problem Statement" in present_categories else -4.0
    business_logic += 8.0 if has_solution_language else -2.0
    business_logic += 8.0 if "Roadmap" in present_categories else -2.0
    business_logic += 6.0 if "Conclusion" in present_categories else -2.0

    if context.domain_type in {"startup", "finance"}:
        business_logic += 5.0 if "Financials" in present_categories else -5.0
    if context.domain_type in {"operations", "strategy"}:
        business_logic += 5.0 if "Operations" in present_categories or "Strategy" in present_categories else -5.0

    business_logic = clamp(business_logic)

    strategy = 18.0
    strategy += framework_alignment * 40.0
    strategy += 10.0 if "Strategy" in present_categories else -2.0
    strategy += 8.0 if "Roadmap" in present_categories else -2.0
    strategy += 6.0 if has_comparison else 0.0
    strategy = clamp(strategy)

    analytical_depth = 15.0
    analytical_depth += len(present_categories) * 3.0
    analytical_depth += len(present_frameworks) * 3.0
    analytical_depth += 5.0 if has_numbers else 0.0
    analytical_depth += 5.0 if has_comparison else 0.0
    analytical_depth += min(10.0, len(context.rubric_topics) * 2.0)
    analytical_depth = clamp(analytical_depth)

    financial = 12.0
    financial_terms = [
        "revenue",
        "pricing",
        "subscription",
        "funding",
        "budget",
        "cost",
        "burn",
        "runway",
        "profit",
        "roi",
        "unit economics",
        "cash flow",
    ]
    financial += 20.0 if contains_any(joined_text, financial_terms) else 0.0
    financial += 15.0 if "Financials" in present_categories else -2.0
    financial += 8.0 if "Financial Model" in present_frameworks else 0.0

    if context.domain_type == "operations":
        financial += 5.0 if has_numbers else 0.0
    elif context.domain_type in {"startup", "finance"}:
        financial += 8.0 if has_numbers else 0.0

    financial = clamp(financial)

    slide_count = summary["slide_count"]
    avg_words = summary["avg_words_per_slide"]
    title_ratio = summary["title_ratio"]

    clarity = 60.0
    if slide_count < 4:
        clarity -= 10.0
    if avg_words < 20:
        clarity -= 8.0
    elif avg_words <= 90:
        clarity += 8.0
    elif avg_words <= 140:
        clarity += 2.0
    else:
        clarity -= 10.0

    if title_ratio >= 0.9:
        clarity += 10.0
    elif title_ratio >= 0.7:
        clarity += 5.0
    else:
        clarity -= 8.0

    repeated_categories = sum(count - 1 for count in categories.values() if count > 1)
    if repeated_categories > max(2, slide_count // 3):
        clarity -= 5.0

    clarity = clamp(clarity)

    framework_util = 15.0 + framework_alignment * 55.0
    framework_util += 5.0 if present_frameworks.intersection({"Business Model Canvas", "Go-To-Market Strategy"}) else 0.0
    framework_util += 5.0 if present_frameworks.intersection({"STP Framework", "4Ps Marketing"}) else 0.0
    framework_util += 5.0 if present_frameworks.intersection({"Value Chain Analysis", "KPI Dashboard"}) else 0.0
    framework_util = clamp(framework_util)

    prompt_alignment_score = round(prompt_alignment * 100.0, 1)

    evidence_grounding_score = 0.0
    unsupported_count = 0
    reasoning_gap_count = 0
    if reasoning_audit is not None:
        evidence_grounding_score = float(getattr(reasoning_audit, "evidence_grounding_score", 0.0) or 0.0)
        unsupported_count = len(getattr(reasoning_audit, "unsupported_claims", []) or [])
        reasoning_gap_count = len(getattr(reasoning_audit, "reasoning_gaps", []) or [])

    overall_base = (
        (business_logic * 0.15)
        + (strategy * 0.14)
        + (analytical_depth * 0.13)
        + (financial * 0.10)
        + (clarity * 0.10)
        + (framework_util * 0.10)
        + (prompt_alignment_score * 0.14)
        + (evidence_grounding_score * 0.14)
    )

    reasoning_penalty = (
        (unsupported_count * 2.5)
        + (reasoning_gap_count * 1.2)
        + max(0.0, 70.0 - prompt_alignment_score) * 0.12
        + max(0.0, 70.0 - evidence_grounding_score) * 0.10
    )
    overall = clamp(overall_base - reasoning_penalty)
    if prompt_alignment_score < 55:
        overall = min(overall, 74.0)

    if evidence_grounding_score < 55:
        overall = min(overall, 72.0)

    if len(present_frameworks) >= 5 and framework_util < 70:
        overall -= 3.0

    if slide_count >= 10 and avg_words > 120:
        overall -= 2.5

    overall = clamp(overall)

    if prompt_alignment_score < 60:
        overall = min(overall, 78.0)
    if evidence_grounding_score < 60:
        overall = min(overall, 76.0)

    missing_elements = []
    for required in context.expected_categories:
        if required not in present_categories and required not in missing_elements:
            missing_elements.append(required)

    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []
    investor_questions: list[str] = []

    if prompt_alignment >= 0.7:
        strengths.append("The deck covers most of the task-specific expectations.")
    else:
        weaknesses.append("The deck does not fully align with the actual case prompt.")
        recommendations.append("Tighten the solution so it directly answers the given problem statement.")

    if strategy >= 70:
        strengths.append("The strategy layer is visible and coherent.")
    else:
        weaknesses.append("The strategy layer is too thin or vague.")
        recommendations.append("Add clearer execution logic and a stronger action plan.")

    if financial >= 60 or context.domain_type in {"startup", "finance"}:
        if financial >= 70:
            strengths.append("The financial logic is reasonably grounded.")
        else:
            weaknesses.append("The financial assumptions are weak or unsupported.")
            recommendations.append("Add concrete pricing, cost, and funding assumptions.")

    if clarity >= 70:
        strengths.append("The presentation is easy to follow.")
    else:
        weaknesses.append("The presentation is dense, repetitive, or under-structured.")
        recommendations.append("Reduce repetition and make each slide do one job.")

    if framework_util >= 60:
        strengths.append("The deck uses business frameworks meaningfully.")
    else:
        weaknesses.append("Framework usage is weak or generic.")
        recommendations.append("Use frameworks only where they support the case, not as decoration.")

    if "Problem Statement" not in present_categories:
        investor_questions.append("What exact problem is this deck solving?")
    if "Roadmap" not in present_categories:
        investor_questions.append("What are the milestones and rollout steps?")
    if context.domain_type in {"startup", "finance"} and "Financials" not in present_categories:
        investor_questions.append("How does this become financially viable?")
    if context.domain_type in {"operations", "strategy"} and "Operations" not in present_categories:
        investor_questions.append("What operational mechanism makes this solution work?")
    if not has_comparison:
        investor_questions.append("Why is this better than the current alternative?")

    score_breakdown = {
        "domain_type": context.domain_type,
        "prompt_brief": context.prompt_brief,
        "problem_statement": context.problem_statement,
        "expected_focus_areas": context.expected_focus_areas,
        "evaluation_criteria": context.evaluation_criteria,
        "rubric_topics": context.rubric_topics,
        "categories_present": list(categories.keys()),
        "frameworks_present": list(frameworks.keys()),
        "prompt_alignment_score": prompt_alignment_score,
        "evidence_grounding_score": round(evidence_grounding_score, 1),
        "reasoning_penalty": round(reasoning_penalty, 1),
        "business_logic_score": business_logic,
        "strategy_strength_score": strategy,
        "analytical_depth_score": analytical_depth,
        "financial_soundness_score": financial,
        "communication_clarity_score": clarity,
        "framework_utilization_score": framework_util,
        "overall_presentation_quality_score": overall,
    }

    return Scorecard(
        business_logic_score=business_logic,
        strategy_strength_score=strategy,
        analytical_depth_score=analytical_depth,
        financial_soundness_score=financial,
        communication_clarity_score=clarity,
        framework_utilization_score=framework_util,
        overall_presentation_quality_score=overall,
        prompt_alignment_score=prompt_alignment_score,
        score_breakdown=score_breakdown,
        strengths=strengths,
        weaknesses=weaknesses,
        missing_elements=missing_elements,
        recommendations=recommendations,
        investor_questions=investor_questions,
        presentation_summary=summary,
    )


def scorecard_to_dict(scorecard: Scorecard) -> dict:
    return asdict(scorecard)