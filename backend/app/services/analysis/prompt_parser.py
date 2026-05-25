from __future__ import annotations

from dataclasses import dataclass
import re


SECTION_HEADER_RE = re.compile(
    r"^(case prompt|problem statement|expected focus areas|focus areas|evaluation criteria|criteria|rubric)\s*:\s*(.*)$",
    re.IGNORECASE,
)

LIST_ITEM_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*(.+?)\s*$")


@dataclass(frozen=True)
class PromptSections:
    raw_prompt: str
    problem_statement: str
    expected_focus_areas: list[str]
    evaluation_criteria: list[str]


def _clean_lines(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return [line.strip() for line in text.split("\n")]


def _strip_label_prefix(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line)
    return line.strip(" ,;\t")


def _split_list_items(text: str) -> list[str]:
    if not text.strip():
        return []

    items: list[str] = []
    lines = _clean_lines(text)

    for line in lines:
        if not line:
            continue

        bullet_match = LIST_ITEM_RE.match(line)
        if bullet_match:
            value = _strip_label_prefix(bullet_match.group(1))
            if value:
                items.append(value)
            continue

        if " - " in line and line.count(" - ") >= 2 and len(line) < 500:
            parts = [part.strip(" ,;") for part in re.split(r"\s+-\s+", line) if part.strip(" ,;")]
            items.extend(parts)
            continue

        if ";" in line and len(line) < 500:
            parts = [part.strip(" ,;") for part in line.split(";") if part.strip(" ,;")]
            if len(parts) > 1:
                items.extend(parts)
                continue

        cleaned = _strip_label_prefix(line)
        if cleaned:
            items.append(cleaned)

    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped


def parse_prompt_sections(raw_prompt: str) -> PromptSections:
    raw_prompt = (raw_prompt or "").strip()
    if not raw_prompt:
        return PromptSections(
            raw_prompt="",
            problem_statement="",
            expected_focus_areas=[],
            evaluation_criteria=[],
        )

    sections = {
        "problem_statement": [],
        "expected_focus_areas": [],
        "evaluation_criteria": [],
    }

    current_section = "problem_statement"

    for line in _clean_lines(raw_prompt):
        if not line:
            continue

        header_match = SECTION_HEADER_RE.match(line)
        if header_match:
            header = header_match.group(1).lower().strip()
            remainder = header_match.group(2).strip()

            if header in {"case prompt", "problem statement"}:
                current_section = "problem_statement"
            elif header in {"expected focus areas", "focus areas"}:
                current_section = "expected_focus_areas"
            elif header in {"evaluation criteria", "criteria", "rubric"}:
                current_section = "evaluation_criteria"

            if remainder:
                sections[current_section].append(remainder)
            continue

        lowered = line.lower()
        if lowered.startswith("domain:"):
            continue

        sections[current_section].append(line)

    problem_statement = " ".join(sections["problem_statement"]).strip()
    expected_focus_areas = _split_list_items("\n".join(sections["expected_focus_areas"]))
    evaluation_criteria = _split_list_items("\n".join(sections["evaluation_criteria"]))

    if not problem_statement:
        problem_statement = raw_prompt

    return PromptSections(
        raw_prompt=raw_prompt,
        problem_statement=problem_statement,
        expected_focus_areas=expected_focus_areas,
        evaluation_criteria=evaluation_criteria,
    )


def build_prompt_brief(sections: PromptSections, max_focus_items: int = 6, max_criteria_items: int = 6) -> str:
    problem = sections.problem_statement.strip()
    focus = sections.expected_focus_areas[:max_focus_items]
    criteria = sections.evaluation_criteria[:max_criteria_items]

    parts: list[str] = []
    if problem:
        parts.append(f"Problem: {problem}")
    if focus:
        parts.append(f"Focus areas: {', '.join(focus)}")
    if criteria:
        parts.append(f"Evaluation criteria: {', '.join(criteria)}")

    return " | ".join(parts).strip()