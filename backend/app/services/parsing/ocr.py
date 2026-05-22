import io

from PIL import Image, UnidentifiedImageError
import pytesseract
from pytesseract import TesseractNotFoundError


def ocr_image_bytes(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
        text = pytesseract.image_to_string(image, config="--psm 6")
        return text.strip()
    except (UnidentifiedImageError, TesseractNotFoundError, OSError):
        return ""
    except Exception:
        return ""