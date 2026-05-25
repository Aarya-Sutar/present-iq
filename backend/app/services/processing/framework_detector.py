from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from functools import lru_cache

import numpy as np

from app.services.processing.embeddings import build_faiss_index, embed_texts, faiss
from app.services.processing.framework_catalog import FRAMEWORKS, FrameworkDefinition


@dataclass(frozen=True)
class FrameworkReference:
    framework: str
    text: str


@dataclass(frozen=True)
class FrameworkMatch:
    framework: str
    score: float
    semantic_score: float
    keyword_score: float
    title_score: float
    method: str
    evidence: list[str]
    reference_text: str | None = None


DOMAIN_FRAMEWORK_PRIORS: dict[str, dict[str, float]] = {
    "startup": {
        "Business Model Canvas": 0.08,
        "Go-To-Market Strategy": 0.10,
        "Financial Model": 0.08,
        "Competitor Analysis": 0.06,
        "SWOT Analysis": 0.05,
        "Market Segmentation": 0.05,
    },
    "operations": {
        "Value Chain Analysis": 0.10,
        "KPI Dashboard": 0.10,
        "Customer Journey Mapping": 0.08,
        "SWOT Analysis": 0.05,
    },
    "marketing": {
        "STP Framework": 0.10,
        "4Ps Marketing": 0.10,
        "Market Segmentation": 0.08,
        "Customer Journey Mapping": 0.08,
        "Competitor Analysis": 0.05,
    },
    "finance": {
        "Financial Model": 0.12,
        "KPI Dashboard": 0.08,
        "Business Model Canvas": 0.06,
    },
    "strategy": {
        "SWOT Analysis": 0.10,
        "Porter's Five Forces": 0.08,
        "PESTEL Analysis": 0.08,
        "Competitor Analysis": 0.10,
        "Value Chain Analysis": 0.05,
    },
    "general": {},
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


def _build_reference_text(framework: FrameworkDefinition, reference: str) -> str:
    return f"{framework.name}. {framework.description}. {reference}"


@lru_cache
def get_reference_rows() -> tuple[FrameworkReference, ...]:
    rows: list[FrameworkReference] = []

    for framework in FRAMEWORKS:
        for reference in framework.references:
            rows.append(
                FrameworkReference(
                    framework=framework.name,
                    text=_build_reference_text(framework, reference),
                )
            )

    return tuple(rows)


@lru_cache
def get_reference_embeddings() -> np.ndarray:
    rows = get_reference_rows()
    texts = [row.text for row in rows]
    return embed_texts(texts)


@lru_cache
def get_reference_index():
    embeddings = get_reference_embeddings()
    return build_faiss_index(embeddings)


def _get_semantic_scores(slide_embedding: np.ndarray) -> dict[int, float]:
    rows = get_reference_rows()
    embeddings = get_reference_embeddings()

    if faiss is not None:
        index = get_reference_index()
        if index is not None:
            top_k = min(25, len(rows))
            distances, indices = index.search(slide_embedding.reshape(1, -1), top_k)
            scores: dict[int, float] = {}
            for position, reference_index in enumerate(indices[0].tolist()):
                if reference_index >= 0:
                    scores[reference_index] = float(distances[0][position])
            return scores

    similarities = embeddings @ slide_embedding
    return {index: float(score) for index, score in enumerate(similarities)}


def detect_frameworks(
    slide_text: str,
    slide_title: str | None = None,
    top_k: int = 3,
    threshold: float = 0.24,
    context_hint: dict | None = None,
) -> list[FrameworkMatch]:
    context_hint = context_hint or {}
    domain_type = str(context_hint.get("domain_type", "general")).lower()
    expected_frameworks = set(context_hint.get("expected_frameworks", []))

    combined_text = " ".join(
        part for part in [slide_title or "", slide_title or "", slide_text or ""] if part.strip()
    )

    if not combined_text.strip():
        return []

    normalized_text = normalize_for_matching(combined_text)
    normalized_title = normalize_for_matching(slide_title or "")
    slide_embedding = embed_texts([combined_text])[0]

    reference_rows = get_reference_rows()
    semantic_scores = _get_semantic_scores(slide_embedding)

    best_per_framework: dict[str, dict[str, object]] = {}

    for index, reference in enumerate(reference_rows):
        state = best_per_framework.setdefault(
            reference.framework,
            {"best_semantic": 0.0, "best_reference": None},
        )

        semantic_score = max(0.0, semantic_scores.get(index, 0.0))
        if semantic_score > float(state["best_semantic"]):
            state["best_semantic"] = semantic_score
            state["best_reference"] = reference.text

    matches: list[FrameworkMatch] = []

    for framework in FRAMEWORKS:
        state = best_per_framework.get(
            framework.framework if hasattr(framework, "framework") else framework.name,
            {"best_semantic": 0.0, "best_reference": None},
        )

        semantic_score = min(1.0, float(state["best_semantic"]))
        keyword_score, keyword_evidence = score_keywords(normalized_text, framework.keywords)
        title_score, title_evidence = score_keywords(normalized_title, framework.keywords)

        name_boost = 0.0
        if framework.name.lower() in normalized_title:
            name_boost += 0.14

        domain_prior = DOMAIN_FRAMEWORK_PRIORS.get(domain_type, {}).get(framework.name, 0.0)
        expected_boost = 0.08 if framework.name in expected_frameworks else 0.0

        final_score = round(
            (semantic_score * 0.60)
            + (keyword_score * 0.22)
            + (title_score * 0.10)
            + name_boost
            + domain_prior
            + expected_boost,
            4,
        )

        effective_threshold = threshold - 0.04 if framework.name in expected_frameworks else threshold + 0.01
        if final_score < effective_threshold:
            continue

        evidence: list[str] = []
        if keyword_evidence:
            evidence.append(f"keywords: {', '.join(keyword_evidence[:4])}")
        if title_evidence or name_boost > 0:
            evidence.append(f"title: {', '.join(title_evidence[:3]) or framework.name}")
        if state["best_reference"]:
            evidence.append(f"semantic: {str(state['best_reference'])[:120]}")

        if semantic_score > 0 and (keyword_score > 0 or title_score > 0):
            method = "hybrid"
        elif semantic_score > 0:
            method = "semantic"
        else:
            method = "keyword"

        matches.append(
            FrameworkMatch(
                framework=framework.name,
                score=final_score,
                semantic_score=round(semantic_score, 4),
                keyword_score=round(keyword_score, 4),
                title_score=round(title_score, 4),
                method=method,
                evidence=evidence,
                reference_text=str(state["best_reference"]) if state["best_reference"] else None,
            )
        )

    matches.sort(key=lambda item: item.score, reverse=True)
    return matches[:top_k]


def framework_matches_to_dicts(matches: list[FrameworkMatch]) -> list[dict]:
    return [asdict(match) for match in matches]