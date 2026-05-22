from pathlib import Path

from app.services.parsing.pdf_parser import parse_pdf
from app.services.parsing.ppt_converter import convert_ppt_to_pptx
from app.services.parsing.pptx_parser import parse_pptx


def parse_presentation_file(file_path: str, presentation_id: int) -> list[dict]:
    extension = Path(file_path).suffix.lower()

    if extension == ".ppt":
        converted_path = convert_ppt_to_pptx(file_path)
        return parse_pptx(converted_path, presentation_id)

    if extension == ".pptx":
        return parse_pptx(file_path, presentation_id)

    if extension == ".pdf":
        return parse_pdf(file_path, presentation_id)

    raise ValueError(f"Unsupported file type: {extension}")