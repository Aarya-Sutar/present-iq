from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    id: int
    presentation_id: int
    report_status: str
    report_filename: str | None
    report_file_path: str | None
    report_summary: str | None
    error_message: str | None
    generated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)