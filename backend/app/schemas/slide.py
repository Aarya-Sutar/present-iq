from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FrameworkMatchResponse(BaseModel):
    framework: str
    score: float
    semantic_score: float
    keyword_score: float
    title_score: float
    method: str
    evidence: list[str] = Field(default_factory=list)
    reference_text: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SlideResponse(BaseModel):
    id: int
    presentation_id: int
    slide_number: int
    slide_title: str | None
    extracted_text: str
    ocr_text: str
    image_paths: list[str]
    slide_metadata: dict
    slide_category: str | None
    classification_confidence: float | None
    classification_reason: str | None
    primary_framework: str | None
    framework_confidence: float | None
    framework_reason: str | None
    framework_matches: list[FrameworkMatchResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)