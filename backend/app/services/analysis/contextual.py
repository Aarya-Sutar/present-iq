from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.analysis.prompt_parser import (
    PromptSections,
    build_prompt_brief,
    parse_prompt_sections,
)


DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "operations": (
        "operations",
        "process",
        "workflow",
        "efficiency",
        "turnaround",
        "logistics",
        "supply chain",
        "complaint",
        "hospital",
        "inventory",
        "service delivery",
    ),
    "startup": (
        "startup",
        "pitch",
        "product",
        "venture",
        "founder",
        "solution",
        "investor",
        "scalable",
        "monetization",
        "business model",
    ),
    "marketing": (
        "marketing",
        "brand",
        "campaign",
        "customer acquisition",
        "promotion",
        "segmentation",
        "positioning",
        "conversion",
    ),
    "finance": (
        "finance",
        "financial",
        "budget",
        "cost",
        "revenue",
        "funding",
        "profit",
        "roi",
        "unit economics",
        "valuation",
    ),
    "strategy": (
        "strategy",
        "growth",
        "expansion",
        "positioning",
        "competitive",
        "transformation",
        "execution plan",
    ),
}


DOMAIN_EXPECTATIONS: dict[str, dict[str, list[str]]] = {
    "operations": {
        "categories": [
            "Problem Statement",
            "Operations",
            "Strategy",
            "Roadmap",
            "Conclusion",
        ],
        "frameworks": [
            "Value Chain Analysis",
            "KPI Dashboard",
            "Customer Journey Mapping",
        ],
    },
    "startup": {
        "categories": [
            "Introduction",
            "Problem Statement",
            "Market Analysis",
            "Competitor Analysis",
            "Strategy",
            "Roadmap",
            "Financials",
            "Conclusion",
        ],
        "frameworks": [
            "Business Model Canvas",
            "Go-To-Market Strategy",
            "Financial Model",
            "Competitor Analysis",
            "SWOT Analysis",
        ],
    },
    "marketing": {
        "categories": [
            "Problem Statement",
            "Market Analysis",
            "Strategy",
            "Roadmap",
            "Conclusion",
        ],
        "frameworks": [
            "STP Framework",
            "4Ps Marketing",
            "Market Segmentation",
            "Customer Journey Mapping",
            "Competitor Analysis",
        ],
    },
    "finance": {
        "categories": [
            "Problem Statement",
            "Financials",
            "Strategy",
            "Roadmap",
            "Conclusion",
        ],
        "frameworks": [
            "Financial Model",
            "KPI Dashboard",
            "Business Model Canvas",
        ],
    },
    "strategy": {
        "categories": [
            "Problem Statement",
            "Market Analysis",
            "Competitor Analysis",
            "Strategy",
            "Roadmap",
            "Conclusion",
        ],
        "frameworks": [
            "SWOT Analysis",
            "Porter's Five Forces",
            "PESTEL Analysis",
            "Value Chain Analysis",
            "Competitor Analysis",
        ],
    },
    "general": {
        "categories": [
            "Problem Statement",
            "Market Analysis",
            "Strategy",
            "Roadmap",
            "Conclusion",
        ],
        "frameworks": [
            "SWOT Analysis",
            "Competitor Analysis",
            "Business Model Canvas",
        ],
    },
}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("\u2014", " ").replace("\u2013", " ")
    return " ".join(text.split()).strip()


def infer_domain_type(case_prompt: str, explicit_domain_type: str | None = None) -> str:
    if explicit_domain_type:
        domain = explicit_domain_type.strip().lower()
        if domain in DOMAIN_EXPECTATIONS:
            return domain

    prompt = normalize_text(case_prompt)
    if not prompt:
        return "general"

    scores = {domain: 0 for domain in DOMAIN_KEYWORDS}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in prompt:
                scores[domain] += 1

    best_domain = max(scores, key=scores.get)
    if scores[best_domain] == 0:
        return "general"

    return best_domain


def parse_rubric_payload(raw_rubric: Any) -> dict[str, Any]:
    if raw_rubric is None:
        return {}

    if isinstance(raw_rubric, dict):
        return raw_rubric

    if isinstance(raw_rubric, list):
        return {"items": raw_rubric}

    if isinstance(raw_rubric, str):
        text = raw_rubric.strip()
        if not text:
            return {}

        try:
            parsed = __import__("json").loads(text)
            if isinstance(parsed, dict):
                return parsed
            return {"items": parsed}
        except Exception:
            return {"raw": text}

    return {"raw": str(raw_rubric)}


def extract_rubric_topics(rubric: dict[str, Any]) -> list[str]:
    topics: list[str] = []

    if not rubric:
        return topics

    if isinstance(rubric.get("criteria"), list):
        for item in rubric["criteria"]:
            if isinstance(item, dict) and item.get("name"):
                topics.append(str(item["name"]))
            elif isinstance(item, str):
                topics.append(item)

    if isinstance(rubric.get("items"), list):
        for item in rubric["items"]:
            if isinstance(item, dict) and item.get("name"):
                topics.append(str(item["name"]))
            elif isinstance(item, str):
                topics.append(item)

    raw = rubric.get("raw")
    if isinstance(raw, str):
        for line in raw.splitlines():
            cleaned = line.strip("-• \t")
            if cleaned:
                topics.append(cleaned)

    seen = set()
    unique_topics: list[str] = []
    for topic in topics:
        topic = topic.strip()
        if not topic or topic.lower() in seen:
            continue
        seen.add(topic.lower())
        unique_topics.append(topic)

    return unique_topics


def map_focus_area_to_categories(focus_area: str) -> list[str]:
    area = normalize_text(focus_area)
    categories: list[str] = []

    if any(term in area for term in ["problem", "pain point", "challenge", "issue", "problem understanding"]):
        categories.append("Problem Statement")

    if any(term in area for term in ["usp", "unique selling proposition", "value proposition", "differentiation"]):
        categories.append("Strategy")

    if any(term in area for term in ["market", "tam", "sam", "som", "segmentation", "target users", "market understanding"]):
        categories.append("Market Analysis")

    if any(term in area for term in ["competitor", "competition", "benchmark", "positioning", "alternative"]):
        categories.append("Competitor Analysis")

    if any(term in area for term in ["roadmap", "execution", "milestone", "timeline", "rollout"]):
        categories.append("Roadmap")

    if any(term in area for term in ["monetization", "pricing", "revenue", "funding", "cac", "ltv", "unit economics", "financial"]):
        categories.append("Financials")

    if any(term in area for term in ["gtm", "go-to-market", "acquisition", "launch", "distribution"]):
        categories.append("Strategy")

    if any(term in area for term in ["operations", "workflow", "process", "kpi", "dashboard", "logistics", "efficiency"]):
        categories.append("Operations")

    if any(term in area for term in ["product", "solution", "product-market fit", "scalability"]):
        categories.append("Strategy")

    return categories


def map_focus_area_to_frameworks(focus_area: str) -> list[str]:
    area = normalize_text(focus_area)
    frameworks: list[str] = []

    if any(term in area for term in ["market", "segment", "target users", "persona"]):
        frameworks.append("Market Segmentation")

    if any(term in area for term in ["competitor", "competition", "benchmark", "positioning"]):
        frameworks.append("Competitor Analysis")

    if any(term in area for term in ["usp", "value proposition", "product", "solution"]):
        frameworks.append("Business Model Canvas")

    if any(term in area for term in ["monetization", "pricing", "revenue", "funding", "cac", "ltv", "unit economics"]):
        frameworks.append("Financial Model")

    if any(term in area for term in ["gtm", "go-to-market", "launch", "acquisition"]):
        frameworks.append("Go-To-Market Strategy")

    if any(term in area for term in ["operations", "workflow", "process", "logistics", "efficiency"]):
        frameworks.append("Value Chain Analysis")

    if any(term in area for term in ["kpi", "dashboard", "metric", "performance"]):
        frameworks.append("KPI Dashboard")

    if any(term in area for term in ["strategy", "growth", "turnaround", "rebuild"]):
        frameworks.append("SWOT Analysis")

    return frameworks


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


@dataclass(frozen=True)
class EvaluationContext:
    case_prompt: str
    domain_type: str
    evaluation_rubric: dict[str, Any]
    expected_categories: list[str]
    expected_frameworks: list[str]
    rubric_topics: list[str]
    prompt_sections: PromptSections
    problem_statement: str
    expected_focus_areas: list[str]
    evaluation_criteria: list[str]
    prompt_brief: str


def build_evaluation_context(
    case_prompt: str,
    explicit_domain_type: str | None = None,
    raw_rubric: Any = None,
) -> EvaluationContext:
    rubric = parse_rubric_payload(raw_rubric)
    prompt_sections = parse_prompt_sections(case_prompt)
    domain_type = infer_domain_type(prompt_sections.problem_statement or case_prompt, explicit_domain_type)
    domain_config = DOMAIN_EXPECTATIONS.get(domain_type, DOMAIN_EXPECTATIONS["general"])

    rubric_topics = extract_rubric_topics(rubric)

    focus_area_categories: list[str] = []
    focus_area_frameworks: list[str] = []
    for focus_area in prompt_sections.expected_focus_areas:
        focus_area_categories.extend(map_focus_area_to_categories(focus_area))
        focus_area_frameworks.extend(map_focus_area_to_frameworks(focus_area))

    rubric_categories: list[str] = []
    rubric_frameworks: list[str] = []
    for topic in rubric_topics:
        rubric_categories.extend(map_focus_area_to_categories(topic))
        rubric_frameworks.extend(map_focus_area_to_frameworks(topic))

    expected_categories = dedupe_preserve_order(
        domain_config["categories"] + focus_area_categories + rubric_categories
    )
    expected_frameworks = dedupe_preserve_order(
        domain_config["frameworks"] + focus_area_frameworks + rubric_frameworks
    )

    prompt_brief = build_prompt_brief(prompt_sections)

    return EvaluationContext(
        case_prompt=prompt_sections.problem_statement or case_prompt.strip(),
        domain_type=domain_type,
        evaluation_rubric=rubric,
        expected_categories=expected_categories,
        expected_frameworks=expected_frameworks,
        rubric_topics=rubric_topics,
        prompt_sections=prompt_sections,
        problem_statement=prompt_sections.problem_statement,
        expected_focus_areas=prompt_sections.expected_focus_areas,
        evaluation_criteria=prompt_sections.evaluation_criteria,
        prompt_brief=prompt_brief,
    )