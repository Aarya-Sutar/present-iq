from dataclasses import asdict

from sqlalchemy.orm import Session

from app.models.presentation import Presentation
from app.models.slide import Slide
from app.services.parsing.loader import parse_presentation_file
from app.services.processing.classifier import classify_slide_text
from app.services.processing.framework_detector import detect_frameworks


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
        total_slides = len(extracted_slides)

        for item in extracted_slides:
            combined_text = "\n".join(
                part for part in [item["extracted_text"], item["ocr_text"]] if part
            )

            classification = classify_slide_text(
                slide_text=combined_text,
                slide_title=item["slide_title"],
                slide_number=item["slide_number"],
                total_slides=total_slides,
            )

            framework_matches = detect_frameworks(
                slide_text=combined_text,
                slide_title=item["slide_title"],
                top_k=3,
                threshold=0.18,
            )

            slide = Slide(
                presentation_id=presentation.id,
                slide_number=item["slide_number"],
                slide_title=item["slide_title"],
                extracted_text=item["extracted_text"],
                ocr_text=item["ocr_text"],
                image_paths=item["image_paths"],
                slide_metadata=item["slide_metadata"],
                slide_category=classification.category,
                classification_confidence=classification.confidence,
                classification_reason=classification.reason,
                primary_framework=framework_matches[0].framework if framework_matches else None,
                framework_confidence=framework_matches[0].score if framework_matches else None,
                framework_reason=(
                    ", ".join(framework_matches[0].evidence)
                    if framework_matches
                    else None
                ),
                framework_matches=[asdict(match) for match in framework_matches],
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