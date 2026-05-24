from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.presentation import Presentation
from app.models.slide import Slide
from app.models.user import User
from app.schemas.analysis import AnalysisResponse
from app.workers.tasks import generate_analysis_task

router = APIRouter(prefix="/presentations/{presentation_id}/analysis", tags=["Analysis"])


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
def queue_analysis(
    presentation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    presentation = db.get(Presentation, presentation_id)

    if not presentation or presentation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Presentation not found")

    slide_count = (
        db.query(Slide)
        .filter(Slide.presentation_id == presentation_id)
        .count()
    )

    if slide_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No extracted slides found. Extract slides first.",
        )

    analysis = db.query(Analysis).filter(Analysis.presentation_id == presentation_id).one_or_none()

    if analysis is None:
        analysis = Analysis(
            presentation_id=presentation_id,
            analysis_status="queued",
        )
        db.add(analysis)
    else:
        analysis.analysis_status = "queued"

    db.commit()
    db.refresh(analysis)

    generate_analysis_task.delay(presentation_id)

    return {
        "message": "Analysis queued",
        "presentation_id": presentation_id,
        "analysis_status": analysis.analysis_status,
    }


@router.get("", response_model=AnalysisResponse)
def get_analysis(
    presentation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    presentation = db.get(Presentation, presentation_id)

    if not presentation or presentation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Presentation not found")

    analysis = db.query(Analysis).filter(Analysis.presentation_id == presentation_id).one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return analysis