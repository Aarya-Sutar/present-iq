from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


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


@dataclass(frozen=True)
class EvaluationContext:
    case_prompt: str
    domain_type: str
    evaluation_rubric: dict[str, Any]
    expected_categories: list[str]
    expected_frameworks: list[str]
    rubric_topics: list[str]


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s%$.-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


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
            parsed = json.loads(text)
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


def build_evaluation_context(
    case_prompt: str,
    explicit_domain_type: str | None = None,
    raw_rubric: Any = None,
) -> EvaluationContext:
    rubric = parse_rubric_payload(raw_rubric)
    domain_type = infer_domain_type(case_prompt, explicit_domain_type)
    domain_config = DOMAIN_EXPECTATIONS.get(domain_type, DOMAIN_EXPECTATIONS["general"])

    rubric_topics = extract_rubric_topics(rubric)

    return EvaluationContext(
        case_prompt=case_prompt.strip(),
        domain_type=domain_type,
        evaluation_rubric=rubric,
        expected_categories=domain_config["categories"] + rubric_topics,
        expected_frameworks=domain_config["frameworks"],
        rubric_topics=rubric_topics,
    )