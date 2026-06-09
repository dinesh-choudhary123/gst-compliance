"""Bank statement processing - CSV, PDF, and Excel bank statements."""

import csv
import json
import re
from datetime import datetime
from typing import Any

from app.document_processing.utils import extract_text_from_pdf, extract_text_from_xlsx


def extract_bank_transactions(file_path: str, filename: str, document_id: str, ollama_client=None) -> list[dict[str, Any]]:
    """Extract bank transactions from a statement file."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    transactions = []

    if ext == "csv":
        transactions = _extract_from_csv(file_path)
    elif ext in ("xlsx", "xls"):
        transactions = _extract_from_xlsx(file_path)
    elif ext == "pdf":
        transactions = _extract_from_pdf(file_path, ollama_client)
    elif ext in ("txt", "text"):
        transactions = _extract_from_txt(file_path, ollama_client)

    # Add document_id to each transaction
    for tx in transactions:
        tx["document_id"] = document_id

    return transactions


def _parse_date(date_str: str) -> str:
    """Parse a date string into ISO format."""
    if not date_str:
        return datetime.now().isoformat()
    date_str = date_str.strip()
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d",
        "%d/%m/%y", "%d-%m-%y",
        "%d %b %Y", "%d %B %Y",
        "%b %d, %Y", "%B %d, %Y",
        "%m/%d/%Y", "%m-%d-%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).isoformat()
        except ValueError:
            continue
    return datetime.now().isoformat()


def _parse_amount(val: str) -> float:
    """Parse a currency amount string to float."""
    if not val:
        return 0.0
    val = val.strip().replace(",", "").replace("₹", "").replace(" ", "")
    try:
        return float(val)
    except ValueError:
        return 0.0


def _extract_from_csv(file_path: str) -> list[dict]:
    """Extract transactions from CSV bank statement."""
    transactions = []
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tx = {
                "transaction_date": _parse_date(row.get("Date", row.get("Transaction Date", row.get("Txn Date", "")))),
                "narration": row.get("Narration", row.get("Description", row.get("Particulars", ""))),
                "debit": _parse_amount(row.get("Debit", row.get("Withdrawal", row.get("Dr", "0")))),
                "credit": _parse_amount(row.get("Credit", row.get("Deposit", row.get("Cr", "0")))),
                "balance": _parse_amount(row.get("Balance", "0")),
                "cheque_no": row.get("Cheque No", row.get("Chq No", row.get("Ref No", ""))),
                "reference": row.get("Reference", ""),
                "raw_data": dict(row),
            }
            transactions.append(tx)
    return transactions


def _extract_from_xlsx(file_path: str) -> list[dict]:
    """Extract transactions from Excel bank statement."""
    transactions = []
    xlsx_data = extract_text_from_xlsx(file_path)

    for sheet_name, sheet in xlsx_data.get("sheets", {}).items():
        headers = [h.lower().strip() for h in sheet.get("headers", [])]
        if not headers:
            continue

        # Map common column names
        col_map = {}
        for i, h in enumerate(headers):
            if h in ("date", "transaction date", "txn date", "value date"):
                col_map["date"] = i
            elif h in ("narration", "description", "particulars", "details"):
                col_map["narration"] = i
            elif h in ("debit", "withdrawal", "dr", "debit amount"):
                col_map["debit"] = i
            elif h in ("credit", "deposit", "cr", "credit amount"):
                col_map["credit"] = i
            elif h in ("balance", "closing balance", "available balance"):
                col_map["balance"] = i
            elif h in ("cheque no", "chq no", "cheque number", "ref no"):
                col_map["cheque"] = i

        for row_data in sheet.get("data", []):
            tx = {
                "transaction_date": _parse_date(row_data[col_map["date"]]) if "date" in col_map and col_map["date"] < len(row_data) else datetime.now().isoformat(),
                "narration": row_data[col_map["narration"]] if "narration" in col_map and col_map["narration"] < len(row_data) else "",
                "debit": _parse_amount(row_data[col_map["debit"]]) if "debit" in col_map and col_map["debit"] < len(row_data) else 0.0,
                "credit": _parse_amount(row_data[col_map["credit"]]) if "credit" in col_map and col_map["credit"] < len(row_data) else 0.0,
                "balance": _parse_amount(row_data[col_map["balance"]]) if "balance" in col_map and col_map["balance"] < len(row_data) else 0.0,
                "cheque_no": row_data[col_map["cheque"]] if "cheque" in col_map and col_map["cheque"] < len(row_data) else "",
                "reference": "",
                "raw_data": {"sheet": sheet_name, "row": row_data},
            }
            transactions.append(tx)

    return transactions


def _extract_from_pdf(file_path: str, ollama_client=None) -> list[dict]:
    """Extract transactions from PDF bank statement using AI."""
    text = extract_text_from_pdf(file_path)

    if ollama_client and text:
        return _ai_extract_transactions(ollama_client, text)

    # Fallback: basic pattern matching
    return _basic_transaction_extraction(text)


def _extract_from_txt(file_path: str, ollama_client=None) -> list[dict]:
    """Extract transactions from text bank statement."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    if ollama_client:
        return _ai_extract_transactions(ollama_client, text)
    return _basic_transaction_extraction(text)


def _basic_transaction_extraction(text: str) -> list[dict]:
    """Basic regex-based transaction extraction."""
    transactions = []
    # Try to find lines with date patterns followed by amounts
    lines = text.split("\n")
    for line in lines:
        # Look for date pattern
        date_match = re.search(r"(\d{2}[-/]\d{2}[-/]\d{2,4})", line)
        if date_match:
            amounts = re.findall(r"([\d,]+\.\d{2})", line)
            if amounts:
                tx = {
                    "transaction_date": _parse_date(date_match.group(1)),
                    "narration": line.strip(),
                    "debit": _parse_amount(amounts[0]) if len(amounts) > 0 else 0.0,
                    "credit": _parse_amount(amounts[1]) if len(amounts) > 1 else 0.0,
                    "balance": _parse_amount(amounts[-1]) if len(amounts) > 0 else 0.0,
                    "cheque_no": "",
                    "reference": "",
                    "raw_data": {"line": line.strip()},
                }
                transactions.append(tx)
    return transactions


def _ai_extract_transactions(ollama_client, text: str) -> list[dict]:
    """Use AI to extract structured transactions from bank statement text."""
    from app.prompts import get_prompt

    system_prompt = get_prompt("bank_statement")

    user_prompt = f"""Extract all bank transactions from the following bank statement text.
Return a JSON array of transactions. Each transaction should have: transaction_date (ISO format), narration, debit, credit, balance, cheque_no (if present), reference.

Bank Statement Text:
{text[:10000]}

Return ONLY a valid JSON array."""

    response = ollama_client.invoke(
        system=system_prompt,
        prompt=user_prompt,
        temperature=0.05,
    )

    try:
        json_match = re.search(r"\[.*\]", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, Exception):
        pass

    return []
