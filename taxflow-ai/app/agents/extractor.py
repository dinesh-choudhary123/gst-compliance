"""Document extraction agent - processes uploaded files and extracts structured data."""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from app.database import (
    save_invoice,
    save_bank_transaction,
    add_document,
    update_project,
)
from app.document_processing.invoice import extract_invoice_data
from app.document_processing.bank_stmt import extract_bank_transactions
from app.ollama_client import TaxFlowOllama


class DocumentExtractor:
    """Agent that processes uploaded documents and extracts structured data."""

    def __init__(self, ollama_client: TaxFlowOllama):
        self.llm = ollama_client

    def process_document(
        self,
        project_id: str,
        document_id: str,
        file_path: str,
        filename: str,
        doc_type: str = "other",
    ) -> dict[str, Any]:
        """Process a single document and extract data."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        result = {
            "type": "unknown",
            "filename": filename,
            "success": False,
            "total_amount": 0,
            "items_count": 0,
            "message": "",
        }

        # Determine document type from content if not specified
        if doc_type == "other" or doc_type == "auto":
            doc_type = self._classify_document(file_path, filename)

        if doc_type in ("invoice", "tax_invoice", "bill"):
            result = self._process_invoice(project_id, document_id, file_path, filename)
        elif doc_type in ("bank_statement", "bank_stmt", "bank"):
            result = self._process_bank_statement(project_id, document_id, file_path, filename)
        elif doc_type in ("eway_bill", "e_way_bill"):
            result = self._process_eway_bill(project_id, document_id, file_path, filename)
        else:
            # Try to detect type from content
            result = self._process_unknown(project_id, document_id, file_path, filename, ext)

        return result

    def _classify_document(self, file_path: str, filename: str) -> str:
        """Classify a document type from its content."""
        name_lower = filename.lower()
        if any(k in name_lower for k in ("invoice", "inv", "tax", "bill", "gst")):
            return "invoice"
        if any(k in name_lower for k in ("bank", "statement", "transaction")):
            return "bank_statement"
        if "eway" in name_lower or "e-way" in name_lower:
            return "eway_bill"
        return "other"

    def _process_invoice(self, project_id: str, document_id: str, file_path: str, filename: str) -> dict:
        """Extract and save invoice data."""
        try:
            data = extract_invoice_data(file_path, filename, document_id, self.llm)
            invoice_id = save_invoice(project_id, data)
            return {
                "type": "invoice",
                "filename": filename,
                "success": True,
                "total_amount": data.get("total_amount", 0),
                "items_count": len(data.get("hsn_codes", [])),
                "invoice_number": data.get("invoice_number", ""),
                "seller_gstin": data.get("seller_gstin", ""),
                "invoice_id": invoice_id,
                "message": f"✅ Invoice {data.get('invoice_number', 'N/A')} extracted successfully. Total: ₹{data.get('total_amount', 0):,.2f}",
            }
        except Exception as e:
            return {
                "type": "invoice",
                "filename": filename,
                "success": False,
                "message": f"❌ Failed to extract invoice: {str(e)}",
            }

    def _process_bank_statement(self, project_id: str, document_id: str, file_path: str, filename: str) -> dict:
        """Extract and save bank transactions."""
        try:
            transactions = extract_bank_transactions(file_path, filename, document_id, self.llm)
            saved_count = 0
            total_credit = 0.0
            total_debit = 0.0

            for tx in transactions:
                save_bank_transaction(project_id, tx)
                saved_count += 1
                total_credit += tx.get("credit", 0)
                total_debit += tx.get("debit", 0)

            return {
                "type": "bank_transaction",
                "filename": filename,
                "success": True,
                "items_count": saved_count,
                "total_credit": total_credit,
                "total_debit": total_debit,
                "message": f"✅ Bank statement processed: {saved_count} transactions extracted. Credits: ₹{total_credit:,.2f}, Debits: ₹{total_debit:,.2f}",
            }
        except Exception as e:
            return {
                "type": "bank_transaction",
                "filename": filename,
                "success": False,
                "message": f"❌ Failed to process bank statement: {str(e)}",
            }

    def _process_eway_bill(self, project_id: str, document_id: str, file_path: str, filename: str) -> dict:
        """Process an e-way bill document."""
        try:
            from app.document_processing.utils import extract_text_from_pdf
            text = extract_text_from_pdf(file_path)

            response = self.llm.invoke(
                system="Extract e-way bill details. Return JSON with: ewb_no, generated_date, valid_upto, from_gstin, to_gstin, invoice_no, invoice_value, transporter_doc, vehicle_no.",
                prompt=f"Extract e-way bill data from this text:\n{text[:4000]}",
                temperature=0.05,
            )

            return {
                "type": "eway_bill",
                "filename": filename,
                "success": True,
                "items_count": 1,
                "message": f"✅ E-way bill processed: {filename}",
                "raw_response": response,
            }
        except Exception as e:
            return {
                "type": "eway_bill",
                "filename": filename,
                "success": False,
                "message": f"❌ Failed to process e-way bill: {str(e)}",
            }

    def _process_unknown(self, project_id: str, document_id: str, file_path: str, filename: str, ext: str) -> dict:
        """Process an unknown document type."""
        try:
            # Try to read and classify
            if ext == "pdf":
                from app.document_processing.utils import extract_text_from_pdf
                text = extract_text_from_pdf(file_path)[:2000]
            elif ext in ("xlsx", "xls"):
                from app.document_processing.utils import extract_text_from_xlsx
                data = extract_text_from_xlsx(file_path)
                text = json.dumps(data, indent=2)[:2000]
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()[:2000]

            response = self.llm.invoke(
                system="You are a document classifier for Indian business documents. Identify the document type and key data.",
                prompt=f"Classify this document and extract key data:\n\nFilename: {filename}\n\nContent:\n{text}",
                temperature=0.1,
            )

            return {
                "type": "unknown",
                "filename": filename,
                "success": True,
                "items_count": 1,
                "message": f"📄 Document analyzed: {filename}\n{response[:500]}",
                "analysis": response,
            }
        except Exception as e:
            return {
                "type": "unknown",
                "filename": filename,
                "success": True,
                "items_count": 1,
                "message": f"📄 Document uploaded: {filename}",
            }
