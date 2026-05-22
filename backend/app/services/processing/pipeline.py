from pathlib import Path

from sqlalchemy.orm import Session

from app.models.presentation import Presentation
from app.models.slide import Slide
from app.services.parsing.loader import parse_presentation_file


def process_presentation(db: Session, presentation: Presentation) -> list[Slide]:
    presentation.processing_status = "processing"
    db.commit()

    try:
        extracted_slides = parse_presentation_file(
            file_path=presentation.file_path,
            presentation_id=presentation.id,
        )

        db.query(Slide).filter(Slide.presentation_id == presentation.id).delete()
        db.commit()

        slides: list[Slide] = []

        for item in extracted_slides:
            slide = Slide(
                presentation_id=presentation.id,
                slide_number=item["slide_number"],
                slide_title=item["slide_title"],
                extracted_text=item["extracted_text"],
                ocr_text=item["ocr_text"],
                image_paths=item["image_paths"],
                slide_metadata=item["metadata"],
            )
            db.add(slide)
            slides.append(slide)

        presentation.processing_status = "completed"
        db.commit()

        for slide in slides:
            db.refresh(slide)

        db.refresh(presentation)
        return slides

    except Exception:
        presentation.processing_status = "failed"
        db.commit()
        raise