from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()


SYSTEM_PROMPT = """
You are a blunt senior evaluator for an E-Cell induction or consulting-style case review.

Judge the presentation against the provided case brief and rubric, not as a generic deck.
Return STRICT JSON only. No markdown. No prose outside JSON.

The JSON must contain:
{
  "executive_summary": "string",
  "consultant_feedback": "string",
  "strengths": ["string"],
  "weaknesses": ["string"],
  "missing_elements": ["string"],
  "recommendations": ["string"],
  "investor_questions": ["string"]
}

Rules:
- Do not repeat the case brief verbatim.
- Do not copy slide text.
- Focus on reasoning gaps, prompt drift, unsupported claims, and decision quality.
- Keep each bullet short and specific.
"""


def build_user_prompt(context: dict, scorecard: dict, presentation_summary: dict, slides_overview: list[dict]) -> str:
    payload = {
        "case_brief": context.get("prompt_brief", ""),
        "problem_statement": context.get("problem_statement", ""),
        "expected_focus_areas": context.get("expected_focus_areas", []),
        "evaluation_criteria": context.get("evaluation_criteria", []),
        "reasoning_audit": context.get("reasoning_audit", {}),
        "scorecard": scorecard,
        "presentation_summary": presentation_summary,
        "slides_overview": slides_overview,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def build_fallback_feedback(context: dict, scorecard: dict, presentation_summary: dict) -> dict[str, Any]:
    strengths = list(scorecard.get("strengths", []))
    weaknesses = list(scorecard.get("weaknesses", []))
    missing_elements = list(scorecard.get("missing_elements", []))
    recommendations = list(scorecard.get("recommendations", []))
    investor_questions = list(scorecard.get("investor_questions", []))

    case_brief = context.get("prompt_brief", "").strip()
    domain_type = context.get("domain_type", "general")
    reasoning_audit = context.get("reasoning_audit", {})

    executive_summary = (
        f"This deck was reviewed against the case brief for the {domain_type} domain. "
        f"Overall score: {scorecard.get('overall_presentation_quality_score', 0)}."
    )

    consultant_feedback = (
        f"The deck is structurally usable, but it does not yet feel fully case-ready for this prompt: {case_brief or 'N/A'}. "
        "The main issue is whether the story actually solves the assigned problem, not whether it merely looks like a business deck. "
        f"Evidence grounding score: {reasoning_audit.get('evidence_grounding_score', 'N/A')}."
    )

    if not strengths:
        strengths = ["The deck has enough structure to be evaluated."]
    if not weaknesses:
        weaknesses = ["The deck still needs stronger alignment with the actual task."]
    if not missing_elements:
        missing_elements = ["No major missing element detected from the rule-based pass."]
    if not recommendations:
        recommendations = ["Make the argument more task-specific and less generic."]
    if not investor_questions:
        investor_questions = ["What proves this solves the assigned problem better than alternatives?"]

    return {
        "executive_summary": executive_summary,
        "consultant_feedback": consultant_feedback,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missing_elements": missing_elements,
        "recommendations": recommendations,
        "investor_questions": investor_questions,
    }


def call_ollama(
    context: dict,
    scorecard: dict,
    presentation_summary: dict,
    slides_overview: list[dict],
) -> dict[str, Any]:
    user_prompt = build_user_prompt(context, scorecard, presentation_summary, slides_overview)

    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }

    try:
        with httpx.Client(base_url=settings.ollama_base_url, timeout=180.0) as client:
            response = client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "")
        try:
            parsed = json.loads(content)
        except Exception:
            return build_fallback_feedback(context, scorecard, presentation_summary)

        return {
            "executive_summary": str(parsed.get("executive_summary", "")).strip(),
            "consultant_feedback": str(parsed.get("consultant_feedback", "")).strip(),
            "strengths": list(parsed.get("strengths", [])),
            "weaknesses": list(parsed.get("weaknesses", [])),
            "missing_elements": list(parsed.get("missing_elements", [])),
            "recommendations": list(parsed.get("recommendations", [])),
            "investor_questions": list(parsed.get("investor_questions", [])),
        }

    except Exception:
        return build_fallback_feedback(context, scorecard, presentation_summary)