from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.presentation import Presentation
from app.workers.tasks import process_presentation_task


def queue_presentation_processing(db: Session, presentation: Presentation) -> None:
    presentation.processing_status = "queued"
    db.commit()

    try:
        process_presentation_task.delay(presentation.id)
    except Exception as exc:
        presentation.processing_status = "failed"
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Processing queue is unavailable",
        ) from exc