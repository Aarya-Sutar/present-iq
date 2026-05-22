from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings

settings = get_settings()
UPLOAD_DIR = Path(settings.uploads_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def build_storage_filename(original_filename: str) -> str:
    suffix = Path(original_filename).suffix.lower()
    return f"{uuid4().hex}{suffix}"


def save_file_bytes(file_bytes: bytes, stored_filename: str) -> str:
    file_path = UPLOAD_DIR / stored_filename
    file_path.write_bytes(file_bytes)
    return str(file_path)