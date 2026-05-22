import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from app.core.config import get_settings

settings = get_settings()


def convert_ppt_to_pptx(source_path: str) -> str:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise HTTPException(
            status_code=400,
            detail="Legacy .ppt files require LibreOffice conversion. Install LibreOffice or convert the file to .pptx first.",
        )

    source = Path(source_path)
    output_dir = Path(settings.uploads_dir) / "converted"
    output_dir.mkdir(parents=True, exist_ok=True)

    out_name = f"{source.stem}_{uuid4().hex}.pptx"
    out_path = output_dir / out_name

    result = subprocess.run(
        [
            soffice,
            "--headless",
            "--convert-to",
            "pptx",
            "--outdir",
            str(output_dir),
            str(source),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert .ppt file: {result.stderr.strip() or result.stdout.strip()}",
        )

    # LibreOffice usually outputs with the same stem name, so locate the file.
    converted_candidates = list(output_dir.glob(f"{source.stem}*.pptx"))
    if not converted_candidates:
        raise HTTPException(
            status_code=500,
            detail="PPT conversion succeeded but no PPTX output was found",
        )

    converted = converted_candidates[0]
    out_path.write_bytes(converted.read_bytes())
    return str(out_path)