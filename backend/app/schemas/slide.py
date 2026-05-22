from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SlideResponse(BaseModel):
    id: int
    presentation_id: int
    slide_number: int
    slide_title: str | None
    extracted_text: str
    ocr_text: str
    image_paths: list[str]
    slide_metadata: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)