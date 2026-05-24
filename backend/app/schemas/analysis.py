from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AnalysisResponse(BaseModel):
    id: int
    presentation_id: int
    analysis_status: str

    business_logic_score: float | None
    strategy_strength_score: float | None
    analytical_depth_score: float | None
    financial_soundness_score: float | None
    communication_clarity_score: float | None
    framework_utilization_score: float | None
    overall_presentation_quality_score: float | None

    score_breakdown: dict
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_elements: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    investor_questions: list[str] = Field(default_factory=list)

    executive_summary: str | None
    consultant_feedback: str | None
    model_name: str | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)