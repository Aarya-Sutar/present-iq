from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.presentation import Presentation
from app.services.processing.pipeline import process_presentation
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="app.workers.tasks.process_presentation_task")
def process_presentation_task(presentation_id: int) -> dict:
    db: Session = SessionLocal()

    try:
        presentation = db.get(Presentation, presentation_id)

        if not presentation:
            return {
                "status": "not_found",
                "presentation_id": presentation_id,
            }

        presentation.processing_status = "processing"
        db.commit()

        slides = process_presentation(db, presentation)

        return {
            "status": "completed",
            "presentation_id": presentation_id,
            "slides_extracted": len(slides),
        }

    except Exception as exc:
        db.rollback()

        presentation = db.get(Presentation, presentation_id)
        if presentation:
            presentation.processing_status = "failed"
            db.commit()

        logger.exception("Failed to process presentation %s", presentation_id)

        return {
            "status": "failed",
            "presentation_id": presentation_id,
            "error": str(exc),
        }

    finally:
        db.close()