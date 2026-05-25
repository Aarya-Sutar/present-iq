from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.presentation import Presentation
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportResponse
from app.workers.tasks import generate_report_task

router = APIRouter(prefix="/presentations/{presentation_id}/report", tags=["Reports"])


@router.post("/generate")
def queue_report_generation(
    presentation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    presentation = db.get(Presentation, presentation_id)

    if not presentation or presentation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Presentation not found")

    analysis = db.query(Analysis).filter(Analysis.presentation_id == presentation_id).one_or_none()
    if not analysis or analysis.analysis_status != "completed":
        raise HTTPException(status_code=400, detail="Complete analysis first before generating report")

    report = db.query(Report).filter(Report.presentation_id == presentation_id).one_or_none()

    if report is None:
        report = Report(
            presentation_id=presentation_id,
            report_status="queued",
        )
        db.add(report)
    else:
        report.report_status = "queued"
        report.error_message = None

    db.commit()
    db.refresh(report)

    generate_report_task.delay(presentation_id)

    return {
        "message": "Report queued",
        "presentation_id": presentation_id,
        "report_status": report.report_status,
    }


@router.get("", response_model=ReportResponse)
def get_report(
    presentation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    presentation = db.get(Presentation, presentation_id)

    if not presentation or presentation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Presentation not found")

    report = db.query(Report).filter(Report.presentation_id == presentation_id).one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report


@router.get("/download")
def download_report(
    presentation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    presentation = db.get(Presentation, presentation_id)

    if not presentation or presentation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Presentation not found")

    report = db.query(Report).filter(Report.presentation_id == presentation_id).one_or_none()

    if not report or report.report_status != "completed" or not report.report_file_path:
        raise HTTPException(status_code=404, detail="Report file not available")

    return FileResponse(
        path=report.report_file_path,
        filename=report.report_filename or "DeckLens_Report.pdf",
        media_type="application/pdf",
    )