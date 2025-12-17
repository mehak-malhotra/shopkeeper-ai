import sys
from pathlib import Path
from typing import Dict

import re

# Add parent directory so we can import enhanced_conversation_state and bulk order processor
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pytesseract
    from PIL import Image
except Exception as _e:  # soft dependency; documented in README
    pytesseract = None
    Image = None

from bulk_order.processor import process_bulk_order_input


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image using pytesseract.
    Returns the raw extracted text. Raises a ValueError if OCR backend missing.
    """
    if pytesseract is None or Image is None:
        raise ValueError("OCR dependencies missing. Install with: pip install pytesseract pillow")
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text


def normalize_ocr_text_to_list(ocr_text: str) -> str:
    """
    Normalize OCR text into a comma-separated list compatible with parse_bulk_list.
    Heuristics:
      - Split lines, remove empty/noise lines
      - Join with ", " to feed existing parser
      - Preserve numbers and units where possible
    """
    if not ocr_text:
        return ""
    lines = [ln.strip() for ln in ocr_text.splitlines()]
    # Remove obviously empty or noise-only lines
    cleaned = [ln for ln in lines if ln and re.search(r"[a-zA-Z0-9]", ln)]
    # Common join; parser already recognizes "-" and unit patterns
    joined = ", ".join(cleaned)
    return joined


def process_image_order(image_path: str, customer_phone: str, customer_name: str = "") -> Dict:
    """
    End-to-end: OCR -> normalize -> reuse bulk order pipeline.
    Returns the same structure as process_bulk_order_input: { parsed, matched, missing, order }
    """
    raw_text = extract_text_from_image(image_path)
    normalized = normalize_ocr_text_to_list(raw_text)
    return process_bulk_order_input(normalized, customer_phone, customer_name)


