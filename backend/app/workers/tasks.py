from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.presentation import Presentation
from app.services.analysis.pipeline import generate_presentation_analysis
from app.services.processing.pipeline import process_presentation
from app.services.reporting.report_service import generate_presentation_report
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


@celery_app.task(name="app.workers.tasks.generate_analysis_task")
def generate_analysis_task(presentation_id: int) -> dict:
    db: Session = SessionLocal()

    try:
        presentation = db.get(Presentation, presentation_id)

        if not presentation:
            return {
                "status": "not_found",
                "presentation_id": presentation_id,
            }

        analysis = generate_presentation_analysis(db, presentation)

        return {
            "status": analysis.analysis_status,
            "presentation_id": presentation_id,
            "analysis_id": analysis.id,
        }

    except Exception as exc:
        logger.exception("Failed to generate analysis for presentation %s", presentation_id)

        return {
            "status": "failed",
            "presentation_id": presentation_id,
            "error": str(exc),
        }

    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.generate_report_task")
def generate_report_task(presentation_id: int) -> dict:
    db: Session = SessionLocal()

    try:
        presentation = db.get(Presentation, presentation_id)

        if not presentation:
            return {
                "status": "not_found",
                "presentation_id": presentation_id,
            }

        report = generate_presentation_report(db, presentation)

        return {
            "status": report.report_status,
            "presentation_id": presentation_id,
            "report_id": report.id,
        }

    except Exception as exc:
        logger.exception("Failed to generate report for presentation %s", presentation_id)

        return {
            "status": "failed",
            "presentation_id": presentation_id,
            "error": str(exc),
        }

    finally:
        db.close()