from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PresentationResponse(BaseModel):
    id: int
    user_id: int | None
    case_prompt: str
    domain_type: str
    evaluation_rubric: dict

    original_filename: str
    stored_filename: str
    file_path: str
    file_type: str
    file_size_bytes: int | None
    processing_status: str

    analysis_status: str | None = None
    report_status: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PresentationListResponse(BaseModel):
    presentations: list[PresentationResponse] = Field(default_factory=list)