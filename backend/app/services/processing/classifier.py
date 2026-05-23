from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


CATEGORIES = [
    "Introduction",
    "Problem Statement",
    "Market Analysis",
    "SWOT Analysis",
    "Business Model Canvas",
    "4Ps Marketing",
    "Competitor Analysis",
    "Financials",
    "Strategy",
    "Roadmap",
    "Team",
    "Operations",
    "Conclusion",
]

CATEGORY_RULES: dict[str, list[tuple[str, float]]] = {
    "Introduction": [
        ("introduction", 3.0),
        ("overview", 2.5),
        ("agenda", 2.5),
        ("who we are", 3.0),
        ("about us", 2.5),
        ("mission", 2.0),
        ("vision", 2.0),
    ],
    "Problem Statement": [
        ("problem", 3.0),
        ("pain point", 3.0),
        ("challenge", 2.5),
        ("issue", 2.0),
        ("gap", 1.5),
        ("customer pain", 3.0),
    ],
    "Market Analysis": [
        ("market", 3.0),
        ("tam", 3.0),
        ("sam", 3.0),
        ("som", 3.0),
        ("cagr", 2.5),
        ("segment", 2.0),
        ("market size", 3.0),
        ("demand", 1.5),
        ("growth", 1.5),
    ],
    "SWOT Analysis": [
        ("swot", 4.0),
        ("strengths", 3.0),
        ("weaknesses", 3.0),
        ("opportunities", 3.0),
        ("threats", 3.0),
    ],
    "Business Model Canvas": [
        ("business model canvas", 4.0),
        ("value proposition", 3.0),
        ("customer segments", 2.5),
        ("channels", 2.5),
        ("revenue streams", 3.0),
        ("key partners", 2.5),
        ("key activities", 2.5),
        ("key resources", 2.5),
        ("cost structure", 3.0),
    ],
    "4Ps Marketing": [
        ("4ps", 4.0),
        ("product", 1.5),
        ("price", 1.5),
        ("place", 1.5),
        ("promotion", 1.5),
        ("marketing mix", 3.0),
    ],
    "Competitor Analysis": [
        ("competitor", 3.5),
        ("competition", 3.0),
        ("benchmark", 2.5),
        ("differentiation", 3.0),
        ("versus", 2.0),
        ("vs", 1.5),
        ("competitive advantage", 3.0),
    ],
    "Financials": [
        ("financial", 3.0),
        ("revenue", 3.0),
        ("cost", 2.0),
        ("profit", 2.5),
        ("ebitda", 3.5),
        ("burn", 2.5),
        ("cash flow", 3.0),
        ("budget", 2.0),
        ("unit economics", 3.0),
        ("funding", 2.5),
        ("projection", 2.5),
    ],
    "Strategy": [
        ("strategy", 4.0),
        ("go-to-market", 3.5),
        ("gtm", 3.0),
        ("approach", 2.0),
        ("plan", 1.5),
        ("execution", 2.0),
        ("positioning", 2.5),
        ("growth strategy", 3.5),
    ],
    "Roadmap": [
        ("roadmap", 4.0),
        ("timeline", 3.0),
        ("milestone", 3.0),
        ("phase", 2.0),
        ("quarter", 1.5),
        ("next steps", 2.5),
        ("implementation", 2.0),
    ],
    "Team": [
        ("team", 4.0),
        ("founder", 3.0),
        ("founders", 3.0),
        ("leadership", 2.5),
        ("experience", 2.0),
        ("advisors", 2.5),
    ],
    "Operations": [
        ("operations", 4.0),
        ("workflow", 3.0),
        ("process", 2.0),
        ("supply chain", 3.0),
        ("implementation", 2.5),
        ("execution", 2.0),
        ("delivery", 2.0),
        ("logistics", 2.5),
    ],
    "Conclusion": [
        ("conclusion", 4.0),
        ("thank you", 3.0),
        ("thanks", 2.0),
        ("summary", 2.5),
        ("closing", 2.0),
        ("q&a", 3.0),
        ("questions", 2.5),
        ("ask", 2.0),
    ],
}


def normalize_for_matching(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s%$.-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def count_phrase_hits(text: str, phrase: str) -> int:
    if not text or not phrase:
        return 0

    escaped = re.escape(phrase.lower())
    return len(re.findall(rf"\b{escaped}\b", text))


def score_category(text: str, category: str) -> tuple[float, list[str]]:
    score = 0.0
    hits: list[str] = []

    for phrase, weight in CATEGORY_RULES.get(category, []):
        count = count_phrase_hits(text, phrase)
        if count > 0:
            score += weight * count
            hits.append(phrase)

    return score, hits


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    reason: str


def classify_slide_text(
    slide_text: str,
    slide_title: str | None = None,
    slide_number: int | None = None,
    total_slides: int | None = None,
) -> ClassificationResult:
    combined = " ".join(
        part for part in [slide_title or "", slide_text or ""] if part.strip()
    )
    normalized = normalize_for_matching(combined)

    raw_scores: dict[str, tuple[float, list[str]]] = {}
    for category in CATEGORIES:
        raw_scores[category] = score_category(normalized, category)

    best_category = "Introduction"
    best_score = 0.0
    best_hits: list[str] = []

    for category, (score, hits) in raw_scores.items():
        if score > best_score:
            best_category = category
            best_score = score
            best_hits = hits

    if best_score == 0.0:
        if slide_number == 1:
            best_category = "Introduction"
            best_hits = ["first slide heuristic"]
        elif total_slides is not None and slide_number == total_slides:
            best_category = "Conclusion"
            best_hits = ["last slide heuristic"]
        else:
            best_category = "Introduction"
            best_hits = ["default fallback"]

    confidence = min(0.99, round(best_score / 12.0, 2))
    if confidence < 0.15 and best_category not in {"Introduction", "Conclusion"}:
        confidence = round(confidence + 0.1, 2)

    reason = ", ".join(best_hits[:5]) if best_hits else "no strong keyword match"

    return ClassificationResult(
        category=best_category,
        confidence=confidence,
        reason=reason,
    )