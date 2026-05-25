from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from app.models.slide import Slide
from app.services.analysis.contextual import EvaluationContext


CLAIM_VERBS = {
    "will",
    "can",
    "should",
    "would",
    "could",
    "increase",
    "decrease",
    "reduce",
    "improve",
    "extend",
    "grow",
    "launch",
    "build",
    "scale",
    "boost",
    "optimize",
    "rebuild",
    "re-align",
    "realign",
    "clarify",
    "revive",
    "create",
    "drive",
}

EVIDENCE_MARKERS = {
    "source",
    "according to",
    "based on",
    "survey",
    "report",
    "research",
    "data",
    "metric",
    "kpi",
    "analysis",
    "estimate",
    "approx",
    "around",
    "about",
    "roughly",
    "imarc",
    "mckinsey",
    "google trends",
    "annual report",
    "financials",
    "user feedback",
    "customer feedback",
    "interview",
    "study",
    "case study",
}

PROMISE_MARKERS = {
    "will",
    "guarantee",
    "ensure",
    "always",
    "never",
    "definitely",
    "best",
    "perfect",
    "easy",
    "instant",
    "huge",
    "massive",
}

NUMBER_PATTERN = re.compile(r"(\d+(\.\d+)?%?|\$\d+|\₹\d+|\brs\.?\b|\blakh\b|\bcrore\b)", re.IGNORECASE)
GENERIC_TITLES = {
    "grow",
    "overview",
    "summary",
    "plan",
    "strategy",
    "analysis",
    "execution",
    "roadmap",
    "mission",
    "fund",
    "customer",
    "mvp",
    "section",
    "target users",
    "go-to-market",
}


@dataclass
class SlideInsight:
    slide_number: int
    slide_title: str | None
    slide_category: str | None
    key_claim: str
    evidence_status: str
    evidence_markers: list[str]
    risk_flags: list[str]
    reasoning_note: str


@dataclass
class ReasoningAudit:
    evidence_grounding_score: float
    prompt_alignment_score: float
    unsupported_claims: list[str]
    reasoning_gaps: list[str]
    slide_insights: list[dict]


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def extract_key_claim(text: str) -> str:
    sentences = split_sentences(text)

    for sentence in sentences:
        normalized = normalize(sentence)
        words = normalized.split()
        if len(words) < 5:
            continue
        if normalized in GENERIC_TITLES:
            continue
        if any(verb in words for verb in CLAIM_VERBS):
            return sentence[:240]

    for sentence in sentences:
        normalized = normalize(sentence)
        words = normalized.split()
        if len(words) >= 5 and normalized not in GENERIC_TITLES:
            return sentence[:240]

    return text[:240].strip()


def detect_evidence_markers(text: str) -> list[str]:
    normalized = normalize(text)
    hits: list[str] = []

    for marker in EVIDENCE_MARKERS:
        if marker in normalized:
            hits.append(marker)

    if NUMBER_PATTERN.search(text):
        hits.append("quantified_claim")

    return sorted(set(hits))


def is_unsupported_assertion(text: str) -> bool:
    normalized = normalize(text)
    words = normalized.split()
    has_promise = any(marker in words for marker in PROMISE_MARKERS)
    has_evidence = bool(detect_evidence_markers(text))
    has_number = bool(NUMBER_PATTERN.search(text))

    if has_promise and not has_evidence and not has_number:
        return True

    if "will" in words and not has_evidence and not has_number:
        return True

    return False


def _evidence_strength(text: str, slide_category: str | None) -> float:
    markers = detect_evidence_markers(text)
    has_number = "quantified_claim" in markers
    has_source = any(marker != "quantified_claim" for marker in markers)

    if has_source and has_number:
        return 1.0
    if has_source:
        return 0.88
    if has_number and len(text.split()) >= 14:
        return 0.68
    if has_number:
        return 0.48

    if slide_category in {"Introduction", "Conclusion"}:
        return 0.22
    if slide_category in {"Roadmap", "Strategy", "Operations"}:
        return 0.32

    return 0.16


def build_reasoning_audit(slides: list[Slide], context: EvaluationContext) -> ReasoningAudit:
    slide_insights: list[SlideInsight] = []
    unsupported_claims: list[str] = []
    reasoning_gaps: list[str] = []

    grounded_sum = 0.0
    aligned_count = 0

    expected_categories = set(context.expected_categories)

    for slide in slides:
        text = " ".join(
            part for part in [slide.slide_title or "", slide.extracted_text or "", slide.ocr_text or ""] if part.strip()
        )

        key_claim = extract_key_claim(text)
        evidence_markers = detect_evidence_markers(text)
        unsupported = is_unsupported_assertion(text)
        grounding = _evidence_strength(text, slide.slide_category)

        risk_flags: list[str] = []

        if unsupported:
            risk_flags.append("unsupported_assertion")
            unsupported_claims.append(f"Slide {slide.slide_number}: {key_claim}")

        if slide.slide_category and slide.slide_category not in expected_categories:
            risk_flags.append("possible_task_drift")

        if not slide.slide_category:
            risk_flags.append("unclassified_slide")

        if grounding < 0.5:
            risk_flags.append("weak_evidence")

        grounded_sum += grounding

        if slide.slide_category in expected_categories:
            aligned_count += 1

        if unsupported and grounding < 0.5:
            reasoning_gaps.append(
                f"Slide {slide.slide_number} makes a claim without enough supporting evidence."
            )

        if slide.slide_category and slide.slide_category not in expected_categories:
            reasoning_gaps.append(
                f"Slide {slide.slide_number} may be drifting away from the expected task."
            )

        if not slide.extracted_text.strip() and not slide.ocr_text.strip():
            reasoning_gaps.append(
                f"Slide {slide.slide_number} has no usable extracted text."
            )

        evidence_status = "grounded" if grounding >= 0.75 else "partially_grounded" if grounding >= 0.45 else "weakly_grounded"

        reasoning_note = (
            f"Claim: {key_claim}. "
            f"Evidence markers: {', '.join(evidence_markers) if evidence_markers else 'none'}. "
            f"Grounding: {round(grounding * 100)}%. "
            f"Flags: {', '.join(risk_flags) if risk_flags else 'none'}."
        )

        slide_insights.append(
            SlideInsight(
                slide_number=slide.slide_number,
                slide_title=slide.slide_title,
                slide_category=slide.slide_category,
                key_claim=key_claim,
                evidence_status=evidence_status,
                evidence_markers=evidence_markers,
                risk_flags=risk_flags,
                reasoning_note=reasoning_note,
            )
        )

    slide_count = len(slides) or 1
    prompt_alignment_score = round((aligned_count / slide_count) * 100.0, 1)
    evidence_grounding_score = round((grounded_sum / slide_count) * 100.0, 1)

    if unsupported_claims and "weak evidence across slides" not in reasoning_gaps:
        reasoning_gaps.append("Weak evidence across one or more slides.")

    return ReasoningAudit(
        evidence_grounding_score=evidence_grounding_score,
        prompt_alignment_score=prompt_alignment_score,
        unsupported_claims=unsupported_claims,
        reasoning_gaps=reasoning_gaps,
        slide_insights=[asdict(item) for item in slide_insights],
    )