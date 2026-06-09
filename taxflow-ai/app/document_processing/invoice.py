"""Invoice extraction from PDFs, Excel, and images."""

import json
import re
from datetime import datetime
from typing import Any, Optional

from app.document_processing.utils import (
    extract_text_from_pdf,
    extract_text_from_xlsx,
)
from app.config import settings


def extract_invoice_data(file_path: str, filename: str, document_id: str, ollama_client=None) -> dict[str, Any]:
    """Extract invoice data from a document.

    Uses direct extraction for common formats, and AI-powered extraction
    for complex/ambiguous fields.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    raw_text = ""
    structured_data = {}

    if ext == "pdf":
        raw_text = extract_text_from_pdf(file_path)
    elif ext in ("xlsx", "xls"):
        xlsx_data = extract_text_from_xlsx(file_path)
        raw_text = json.dumps(xlsx_data, indent=2)
        structured_data = xlsx_data
    elif ext == "csv":
        from app.document_processing.utils import extract_text_from_csv
        csv_data = extract_text_from_csv(file_path)
        raw_text = json.dumps(csv_data, indent=2)
        structured_data = {"rows": csv_data}
    else:
        # Try reading as text
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
        except Exception:
            raw_text = ""

    # Basic regex-based extraction for common GST invoice fields
    basic_data = _basic_invoice_extraction(raw_text)

    # If Ollama is available, enhance with AI extraction
    ai_data = {}
    if ollama_client and raw_text:
        try:
            ai_data = _ai_invoice_extraction(ollama_client, raw_text, filename)
        except Exception:
            pass

    # Merge: AI overrides basic, but basic serves as fallback
    merged = {**basic_data, **ai_data}

    # Ensure all required fields
    result = {
        "document_id": document_id,
        "invoice_number": merged.get("invoice_number", ""),
        "invoice_date": merged.get("invoice_date"),
        "seller_name": merged.get("seller_name", ""),
        "seller_gstin": merged.get("seller_gstin", ""),
        "buyer_name": merged.get("buyer_name", ""),
        "buyer_gstin": merged.get("buyer_gstin", ""),
        "hsn_codes": merged.get("hsn_codes", []),
        "taxable_amount": float(merged.get("taxable_amount", 0)),
        "cgst_rate": float(merged.get("cgst_rate", 0)),
        "cgst_amount": float(merged.get("cgst_amount", 0)),
        "sgst_rate": float(merged.get("sgst_rate", 0)),
        "sgst_amount": float(merged.get("sgst_amount", 0)),
        "igst_rate": float(merged.get("igst_rate", 0)),
        "igst_amount": float(merged.get("igst_amount", 0)),
        "cess_amount": float(merged.get("cess_amount", 0)),
        "total_amount": float(merged.get("total_amount", 0)),
        "reverse_charge": merged.get("reverse_charge", False),
        "place_of_supply": merged.get("place_of_supply", ""),
        "irn": merged.get("irn"),
        "raw_data": {
            "raw_text_preview": raw_text[:2000],
            "extraction_method": "ai" if ai_data else "regex",
        },
    }
    return result


def _basic_invoice_extraction(text: str) -> dict[str, Any]:
    """Extract common invoice fields using regex patterns."""
    data = {}

    # Invoice Number patterns
    patterns = [
        r"(?:Invoice\s*(?:No|Number|#)[:\s]*)([A-Za-z0-9/\-]+)",
        r"(?:INV\s*[:\-]\s*)([A-Za-z0-9/\-]+)",
        r"(?:GST\s*Invoice\s*[:\s]*)([A-Za-z0-9/\-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["invoice_number"] = match.group(1).strip()
            break

    # GSTIN patterns
    gstin_pattern = r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}"
    matches = re.findall(gstin_pattern, text)
    if len(matches) >= 2:
        data["seller_gstin"] = matches[0]
        data["buyer_gstin"] = matches[1]
    elif len(matches) == 1:
        data["seller_gstin"] = matches[0]

    # Date patterns
    date_patterns = [
        r"(\d{2}[-/]\d{2}[-/]\d{4})",
        r"(\d{4}[-/]\d{2}[-/]\d{2})",
        r"(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                date_str = match.group(1)
                for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"]:
                    try:
                        data["invoice_date"] = datetime.strptime(date_str, fmt).isoformat()
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
            if "invoice_date" in data:
                break

    # Total Amount
    total_patterns = [
        r"(?:Total\s*(?:Amount|Invoice\s*Amount)[:\s]*₹?\s*([\d,]+\.?\d*))",
        r"(?:Grand\s*Total[:\s]*₹?\s*([\d,]+\.?\d*))",
        r"(?:Amount\s*Payable[:\s]*₹?\s*([\d,]+\.?\d*))",
    ]
    for pattern in total_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                data["total_amount"] = float(match.group(1).replace(",", ""))
                break
            except ValueError:
                pass

    return data


def _ai_invoice_extraction(ollama_client, text: str, filename: str) -> dict[str, Any]:
    """Use AI to extract structured invoice data from raw text."""
    from app.prompts import get_prompt

    system_prompt = get_prompt("invoice_extraction")
    user_prompt = f"""Extract the following invoice data from this document.

Filename: {filename}

Document Text:
{text[:8000]}

Return ONLY valid JSON with these fields: invoice_number, invoice_date (ISO format), seller_name, seller_gstin, buyer_name, buyer_gstin, hsn_codes (array of {{code, description, quantity, rate, amount}}), taxable_amount, cgst_rate, cgst_amount, sgst_rate, sgst_amount, igst_rate, igst_amount, cess_amount, total_amount, reverse_charge (boolean), place_of_supply, irn. Use empty string for unknown fields, 0 for amounts."""

    response = ollama_client.invoke(
        system=system_prompt,
        prompt=user_prompt,
        temperature=0.05,
    )

    # Try to parse JSON from response
    try:
        # Find JSON in response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, Exception):
        pass

    return {}
