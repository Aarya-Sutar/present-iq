from __future__ import annotations

import re
from dataclasses import dataclass


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


DOMAIN_PRIORS: dict[str, dict[str, float]] = {
    "startup": {
        "Introduction": 0.4,
        "Problem Statement": 0.8,
        "Market Analysis": 0.8,
        "Competitor Analysis": 0.8,
        "Strategy": 0.9,
        "Roadmap": 0.9,
        "Financials": 0.7,
        "Business Model Canvas": 0.8,
        "SWOT Analysis": 0.6,
        "Conclusion": 0.5,
    },
    "operations": {
        "Problem Statement": 0.8,
        "Operations": 1.0,
        "Strategy": 0.8,
        "Roadmap": 0.9,
        "Conclusion": 0.5,
        "KPI Dashboard": 0.8,
        "Value Chain Analysis": 0.8,
    },
    "marketing": {
        "Problem Statement": 0.6,
        "Market Analysis": 0.9,
        "Strategy": 0.9,
        "4Ps Marketing": 0.9,
        "STP Framework": 0.9,
        "Roadmap": 0.7,
        "Conclusion": 0.4,
    },
    "finance": {
        "Problem Statement": 0.5,
        "Financials": 1.0,
        "Strategy": 0.7,
        "Roadmap": 0.6,
        "Business Model Canvas": 0.7,
        "KPI Dashboard": 0.7,
        "Conclusion": 0.4,
    },
    "strategy": {
        "Problem Statement": 0.7,
        "Market Analysis": 0.8,
        "Competitor Analysis": 1.0,
        "Strategy": 1.0,
        "Roadmap": 0.9,
        "SWOT Analysis": 0.8,
        "Conclusion": 0.5,
    },
    "general": {
        "Introduction": 0.3,
        "Problem Statement": 0.7,
        "Market Analysis": 0.5,
        "Strategy": 0.7,
        "Roadmap": 0.7,
        "Conclusion": 0.4,
    },
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


def score_keywords(text: str, keywords: tuple[str, ...]) -> tuple[float, list[str]]:
    score = 0.0
    evidence: list[str] = []

    for keyword in keywords:
        hits = count_phrase_hits(text, keyword)
        if hits > 0:
            evidence.append(keyword)
            weight = 1.5 if len(keyword.split()) > 1 else 1.0
            score += weight * hits

    return min(score / 4.0, 1.0), evidence


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    reason: str


def _keyword_hit_count(text: str, keywords: list[tuple[str, float]]) -> int:
    count = 0
    for phrase, _weight in keywords:
        if count_phrase_hits(text, phrase) > 0:
            count += 1
    return count

def score_category(text: str, category: str) -> tuple[float, list[str]]:
    keywords = CATEGORY_RULES.get(category, [])

    score = 0.0
    hits: list[str] = []

    for phrase, weight in keywords:
        phrase_hits = count_phrase_hits(text, phrase)

        if phrase_hits > 0:
            hits.append(phrase)
            score += phrase_hits * weight

    normalized_score = min(score / 8.0, 1.0)

    return normalized_score, hits

def classify_slide_text(
    slide_text: str,
    slide_title: str | None = None,
    slide_number: int | None = None,
    total_slides: int | None = None,
    context_hint: dict | None = None,
) -> ClassificationResult:
    context_hint = context_hint or {}
    expected_categories = set(context_hint.get("expected_categories", []))
    domain_type = str(context_hint.get("domain_type", "general")).lower()

    combined = " ".join(
        part for part in [slide_title or "", slide_text or ""] if part.strip()
    )
    normalized = normalize_for_matching(combined)
    normalized_title = normalize_for_matching(slide_title or "")

    raw_scores: dict[str, tuple[float, list[str]]] = {}
    for category in CATEGORIES:
        raw_scores[category] = score_category(normalized, category)

    best_category = "Introduction"
    best_score = -1.0
    best_hits: list[str] = []

    for category, (score, hits) in raw_scores.items():
        title_boost = 0.0
        if normalized_title and category.lower() in normalized_title:
            title_boost += 1.5

        expected_boost = 0.0
        if category in expected_categories:
            expected_boost += 1.2

        domain_boost = DOMAIN_PRIORS.get(domain_type, {}).get(category, 0.0)

        special_boost = 0.0
        if category == "SWOT Analysis":
            swot_hits = _keyword_hit_count(normalized, CATEGORY_RULES[category])
            if "swot" in normalized_title or swot_hits >= 2:
                special_boost += 1.0
            else:
                special_boost -= 1.0

        if category == "4Ps Marketing":
            marketing_hits = _keyword_hit_count(normalized, CATEGORY_RULES[category])
            if "marketing mix" in normalized or marketing_hits >= 2:
                special_boost += 0.8
            else:
                special_boost -= 0.6

        if category == "Introduction":
            if slide_number == 1:
                special_boost += 1.0
            elif any(term in normalized for term in ["overview", "executive summary", "about us"]):
                special_boost += 0.8
            else:
                special_boost -= 0.6

        if category == "Conclusion":
            if total_slides is not None and slide_number == total_slides:
                special_boost += 1.0
            elif any(term in normalized for term in ["thank you", "q&a", "questions"]):
                special_boost += 0.8
            else:
                special_boost -= 0.5

        total_score = score + title_boost + expected_boost + domain_boost + special_boost

        if total_score > best_score:
            best_category = category
            best_score = total_score
            best_hits = hits[:]

    if best_score <= 0.0:
        if slide_number == 1:
            best_category = "Introduction"
            best_hits = ["first slide heuristic"]
        elif total_slides is not None and slide_number == total_slides:
            best_category = "Conclusion"
            best_hits = ["last slide heuristic"]
        else:
            best_category = "Introduction"
            best_hits = ["default fallback"]

    confidence = round(min(0.95, best_score / (best_score + 6.5)), 2)
    if confidence < 0.12 and best_category not in {"Introduction", "Conclusion"}:
        confidence = round(min(0.25, confidence + 0.08), 2)

    reason = ", ".join(best_hits[:5]) if best_hits else "no strong keyword match"

    return ClassificationResult(
        category=best_category,
        confidence=confidence,
        reason=reason,
    )