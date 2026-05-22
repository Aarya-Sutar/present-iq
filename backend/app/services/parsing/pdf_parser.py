import fitz

from app.services.parsing.common import build_slide_asset_dir, save_binary_asset
from app.services.parsing.ocr import ocr_image_bytes
from app.utils.text_cleaning import extract_title_from_text, normalize_text


def parse_pdf(file_path: str, presentation_id: int) -> list[dict]:
    document = fitz.open(file_path)
    results: list[dict] = []

    for page_index, page in enumerate(document, start=1):
        asset_dir = build_slide_asset_dir(presentation_id, page_index)

        extracted_text = normalize_text(page.get_text("text"))
        image_paths: list[str] = []
        ocr_parts: list[str] = []

        for image_index, image_info in enumerate(page.get_images(full=True), start=1):
            xref = image_info[0]
            image_data = document.extract_image(xref)

            image_bytes = image_data["image"]
            image_ext = image_data["ext"]

            image_path = save_binary_asset(
                asset_dir=asset_dir,
                stem=f"image_{image_index}",
                ext=image_ext,
                blob=image_bytes,
            )
            image_paths.append(image_path)

            if not extracted_text:
                ocr_text = ocr_image_bytes(image_bytes)
                if ocr_text:
                    ocr_parts.append(ocr_text)

        ocr_text = normalize_text("\n".join(ocr_parts))
        slide_title = extract_title_from_text(extracted_text or ocr_text)

        results.append(
            {
                "slide_number": page_index,
                "slide_title": slide_title,
                "extracted_text": extracted_text,
                "ocr_text": ocr_text,
                "image_paths": image_paths,
                "slide_metadata": {
                    "source_type": "pdf",
                    "image_count": len(image_paths),
                    "text_length": len(extracted_text),
                    "ocr_length": len(ocr_text),
                },
            }
        )

    return results