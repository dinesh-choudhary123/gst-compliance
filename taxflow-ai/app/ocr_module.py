"""OCR Module for scanned document processing.

Provides OCR capabilities for scanned invoices and documents.
Uses Tesseract when available, with graceful fallback to basic text extraction.
Supports Hindi and English language OCR.
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Any, Optional

from app.config import settings

# Try imports gracefully
try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    pytesseract = None
    Image = None


def check_tesseract_available() -> bool:
    """Check if Tesseract OCR is installed and available."""
    if not HAS_TESSERACT:
        return False
    try:
        version = pytesseract.get_tesseract_version()
        return version is not None
    except Exception:
        return False


def get_available_languages() -> list[str]:
    """Get list of available Tesseract language packs."""
    if not check_tesseract_available():
        return []
    try:
        langs = pytesseract.get_languages()
        return langs
    except Exception:
        return ["eng"]  # Default to English if can't detect


def ocr_image(image_path: str, lang: str = "eng+hin") -> str:
    """Perform OCR on an image file.

    Args:
        image_path: Path to image file (JPG, PNG, etc.)
        lang: Tesseract language codes (default: English + Hindi)

    Returns:
        Extracted text from the image
    """
    if not check_tesseract_available():
        return "[OCR not available. Install Tesseract: brew install tesseract && brew install tesseract-lang]"

    try:
        img = Image.open(image_path)
        # Preprocess for better OCR
        img = img.convert("L")  # Convert to grayscale

        # Try with specified languages first, fallback to English
        try:
            text = pytesseract.image_to_string(img, lang=lang)
        except Exception:
            text = pytesseract.image_to_string(img, lang="eng")

        return text.strip()
    except Exception as e:
        return f"[OCR Error: {str(e)}]"


def ocr_pdf(pdf_path: str, lang: str = "eng+hin") -> str:
    """Convert PDF pages to images and run OCR.

    Uses PyMuPDF to render PDF pages as images, then
    runs Tesseract OCR on each page.

    Args:
        pdf_path: Path to PDF file
        lang: Tesseract language codes

    Returns:
        Extracted text from all pages
    """
    if not check_tesseract_available():
        return "[OCR not available. Install Tesseract for scanned document support.]"

    try:
        import fitz  # PyMuPDF
    except ImportError:
        return ""

    text_parts = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render page to image at 300 DPI
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img_data = pix.tobytes("png")

            # Save to temp file for OCR
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(img_data)
                temp_path = f.name

            try:
                text = ocr_image(temp_path, lang)
                if text and not text.startswith("[OCR"):
                    text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
            finally:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

        doc.close()
    except Exception as e:
        text_parts.append(f"[OCR Error: {str(e)}]")

    return "\n\n".join(text_parts)


def detect_scanned_pdf(pdf_path: str) -> bool:
    """Detect if a PDF is scanned (image-based) vs text-based.

    Checks if the PDF has extractable text content.
    """
    try:
        import fitz  # PyMuPDF
        import pdfplumber

        # Try pdfplumber first
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and len(text.strip()) > 50:
                        return False  # Has extractable text
        except Exception:
            pass

        # Try PyMuPDF
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text = page.get_text()
                if text and len(text.strip()) > 50:
                    doc.close()
                    return False
            doc.close()
        except Exception:
            pass

        # No significant text found - likely scanned
        return True

    except Exception:
        return False


def enhanced_extraction(file_path: str, filename: str) -> dict:
    """Enhanced document extraction with OCR fallback.

    Attempts text extraction first, falls back to OCR if needed.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    result = {
        "text": "",
        "method": "text",
        "ocr_used": False,
        "scanned_detected": False,
    }

    if ext == "pdf":
        # Check if scanned
        is_scanned = detect_scanned_pdf(file_path)
        result["scanned_detected"] = is_scanned

        if is_scanned and check_tesseract_available():
            result["text"] = ocr_pdf(file_path)
            result["method"] = "ocr"
            result["ocr_used"] = True
        else:
            # Regular text extraction
            try:
                from app.document_processing.utils import extract_text_from_pdf
                result["text"] = extract_text_from_pdf(file_path)
                result["method"] = "pdf_text"
            except Exception as e:
                result["text"] = f"[Extraction error: {str(e)}]"

    elif ext in ("jpg", "jpeg", "png", "tiff", "tif", "bmp"):
        if check_tesseract_available():
            result["text"] = ocr_image(file_path)
            result["method"] = "ocr"
            result["ocr_used"] = True
        else:
            result["text"] = "[Image uploaded. Install Tesseract for OCR.]"

    else:
        # Non-image/non-PDF - use existing extraction
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                result["text"] = f.read()
        except Exception:
            result["text"] = ""

    return result


def install_tesseract_instructions() -> str:
    """Return platform-specific Tesseract installation instructions."""
    return """
    ## Tesseract OCR Installation

    ### macOS
    ```bash
    brew install tesseract
    brew install tesseract-lang  # For Hindi + other languages
    ```

    ### Ubuntu/Debian
    ```bash
    sudo apt-get update
    sudo apt-get install tesseract-ocr
    sudo apt-get install tesseract-ocr-hin  # Hindi
    sudo apt-get install tesseract-ocr-eng  # English
    ```

    ### Windows
    1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    2. Add Tesseract to PATH
    3. Install: pip install pytesseract pillow

    ### Verify Installation
    ```python
    import pytesseract
    print(pytesseract.get_tesseract_version())
    ```

    Then install Python packages:
    ```bash
    pip install pytesseract pillow
    ```
    """
