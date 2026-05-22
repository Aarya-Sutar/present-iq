from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings

settings = get_settings()
EXTRACTED_DIR = Path(settings.uploads_dir) / "extracted"
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)


def build_slide_asset_dir(presentation_id: int, slide_number: int) -> Path:
    path = EXTRACTED_DIR / str(presentation_id) / f"slide_{slide_number}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_binary_asset(asset_dir: Path, stem: str, ext: str, blob: bytes) -> str:
    filename = f"{stem}_{uuid4().hex}.{ext}"
    path = asset_dir / filename
    path.write_bytes(blob)
    return str(path)