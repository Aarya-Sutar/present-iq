from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.presentation import Presentation
from app.models.slide import Slide
from app.models.user import User
from app.schemas.presentation import PresentationResponse
from app.schemas.slide import SlideResponse
from app.services.file_validation import validate_presentation_file
from app.services.processing.pipeline import process_presentation
from app.services.processing.queue import queue_presentation_processing
from app.services.storage import build_storage_filename, save_file_bytes

router = APIRouter(prefix="/presentations", tags=["Presentations"])


@router.post(
    "/upload",
    response_model=PresentationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_presentation(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await file.read()
    file_extension = validate_presentation_file(file.filename, file_bytes)

    stored_filename = build_storage_filename(file.filename)
    file_path = save_file_bytes(file_bytes, stored_filename)

    presentation = Presentation(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_type=file_extension.replace(".", "").upper(),
        file_size_bytes=len(file_bytes),
        processing_status="uploaded",
    )

    db.add(presentation)
    db.commit()
    db.refresh(presentation)

    queue_presentation_processing(db, presentation)
    db.refresh(presentation)

    return presentation


@router.get("", response_model=list[PresentationResponse])
def list_presentations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(Presentation)
        .where(Presentation.user_id == current_user.id)
        .order_by(Presentation.created_at.desc())
    )

    presentations = db.execute(statement).scalars().all()
    return presentations


@router.post("/{presentation_id}/extract")
def extract_presentation(
    presentation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    presentation = db.get(Presentation, presentation_id)

    if not presentation or presentation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Presentation not found")

    queue_presentation_processing(db, presentation)

    return {
        "message": "Presentation queued for processing",
        "presentation_id": presentation.id,
        "status": presentation.processing_status,
    }


@router.get(
    "/{presentation_id}/slides",
    response_model=list[SlideResponse],
)
def get_presentation_slides(
    presentation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    presentation = db.get(Presentation, presentation_id)

    if not presentation or presentation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Presentation not found")

    statement = (
        select(Slide)
        .where(Slide.presentation_id == presentation_id)
        .order_by(Slide.slide_number.asc())
    )

    slides = db.execute(statement).scalars().all()
    return slides