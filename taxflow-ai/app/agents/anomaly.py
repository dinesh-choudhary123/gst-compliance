"""Anomaly Detection Agent - identifies issues and discrepancies in GST data."""

import json
from typing import Any

from app.database import get_invoices, get_bank_transactions, get_anomalies, save_anomaly
from app.ollama_client import TaxFlowOllama
from app.prompts import get_prompt


class AnomalyDetector:
    """Agent for detecting anomalies, mismatches, and issues in GST data."""

    def __init__(self, ollama_client: TaxFlowOllama):
        self.llm = ollama_client

    def detect(self, project_id: str, message: str) -> dict[str, Any]:
        """Run anomaly detection on all project data."""
        invoices = get_invoices(project_id)
        transactions = get_bank_transactions(project_id)
        existing_anomalies = get_anomalies(project_id, unresolved_only=True)

        all_anomalies = []

        # 1. Invoice-level checks
        for inv in invoices:
            inv_anomalies = self._check_invoice_anomalies(inv)
            for a in inv_anomalies:
                anomaly_id = save_anomaly(project_id, a)
                a["id"] = anomaly_id
                all_anomalies.append(a)

        # 2. Cross-document checks (if both invoices and transactions exist)
        if invoices and transactions:
            cross_anomalies = self._check_cross_anomalies(invoices, transactions)
            for a in cross_anomalies:
                anomaly_id = save_anomaly(project_id, a)
                a["id"] = anomaly_id
                all_anomalies.append(a)

        # 3. Tax calculation verification
        tax_anomalies = self._check_tax_calculations(invoices)
        for a in tax_anomalies:
            anomaly_id = save_anomaly(project_id, a)
            a["id"] = anomaly_id
            all_anomalies.append(a)

        # Generate AI analysis of all anomalies
        if all_anomalies or existing_anomalies:
            all_items = all_anomalies + [dict(a) for a in existing_anomalies]
            response = self.llm.chat([
                {"role": "system", "content": get_prompt("anomaly_detection")},
                {"role": "user", "content": f"""Analyze the following anomalies found for a client project:

{json.dumps(all_items[:30], indent=2, default=str)}

Provide:
1. Categorized summary of all anomalies (High/Medium/Low)
2. Most critical issues that need immediate attention
3. Recommended actions for each category
4. Overall compliance health assessment"""}
            ])

            severity_counts = {}
            for a in all_items:
                s = a.get("severity", "medium")
                severity_counts[s] = severity_counts.get(s, 0) + 1

            actions = [
                f"Found {len(all_items)} total anomalies",
                f"High: {severity_counts.get('high', 0)}, Medium: {severity_counts.get('medium', 0)}, Low: {severity_counts.get('low', 0)}",
            ]

            return {
                "response": response,
                "actions": actions,
                "data": {"anomalies": all_items, "counts": severity_counts},
            }
        else:
            return {
                "response": "✅ No anomalies detected! All data looks clean. Here's what was checked:\n- Invoice data validation\n- Tax calculation verification\n- Cross-document consistency\n\nYour data appears to be in good order.",
                "actions": ["Ran full anomaly detection - no issues found"],
                "data": {"anomalies": [], "counts": {}},
            }

    def _check_invoice_anomalies(self, invoice: dict) -> list[dict]:
        """Check a single invoice for anomalies."""
        anomalies = []

        # Check GSTIN format
        seller_gstin = invoice.get("seller_gstin", "")
        if seller_gstin and len(seller_gstin) != 15:
            anomalies.append({
                "severity": "high",
                "category": "gst_mismatch",
                "title": f"Invalid seller GSTIN: {seller_gstin}",
                "description": f"Invoice {invoice.get('invoice_number', 'N/A')}: Seller GSTIN has invalid length ({len(seller_gstin)} instead of 15)",
                "suggestion": "Verify the seller's GSTIN from GST portal",
                "source_document_id": invoice.get("document_id"),
            })

        # Check tax amounts
        total_tax = (invoice.get("cgst_amount", 0) +
                     invoice.get("sgst_amount", 0) +
                     invoice.get("igst_amount", 0) +
                     invoice.get("cess_amount", 0))

        # CGST and SGST should be equal for intra-state
        cgst = invoice.get("cgst_amount", 0)
        sgst = invoice.get("sgst_amount", 0)
        if cgst > 0 and sgst > 0 and abs(cgst - sgst) > 0.01:
            anomalies.append({
                "severity": "medium",
                "category": "gst_mismatch",
                "title": f"CGST/SGST mismatch: {invoice.get('invoice_number', 'N/A')}",
                "description": f"CGST ₹{cgst:,.2f} ≠ SGST ₹{sgst:,.2f}. These should be equal for intra-state transactions.",
                "suggestion": "Verify tax calculation - CGST and SGST rates should be equal",
                "source_document_id": invoice.get("document_id"),
            })

        # Check IGST with CGST+SGST (should not have both)
        igst = invoice.get("igst_amount", 0)
        if igst > 0 and (cgst > 0 or sgst > 0):
            anomalies.append({
                "severity": "high",
                "category": "tax_error",
                "title": f"Both IGST and CGST/SGST present: {invoice.get('invoice_number', 'N/A')}",
                "description": "Invoice has both IGST and CGST/SGST. For inter-state, only IGST applies. For intra-state, only CGST+SGST applies.",
                "suggestion": "Correct the tax type - use either IGST (inter-state) or CGST+SGST (intra-state)",
                "source_document_id": invoice.get("document_id"),
            })

        # Check total = taxable + tax
        expected_total = invoice.get("taxable_amount", 0) + total_tax
        actual_total = invoice.get("total_amount", 0)
        if actual_total > 0 and abs(expected_total - actual_total) > 1.0:
            anomalies.append({
                "severity": "medium",
                "category": "tax_error",
                "title": f"Total amount mismatch: {invoice.get('invoice_number', 'N/A')}",
                "description": f"Taxable (₹{invoice.get('taxable_amount', 0):,.2f}) + Tax (₹{total_tax:,.2f}) = ₹{expected_total:,.2f} ≠ Total ₹{actual_total:,.2f}",
                "suggestion": "Recalculate invoice totals",
                "source_document_id": invoice.get("document_id"),
            })

        # Check for missing invoice number
        if not invoice.get("invoice_number"):
            anomalies.append({
                "severity": "high",
                "category": "missing_data",
                "title": "Missing invoice number",
                "description": "Invoice has no invoice number",
                "suggestion": "Assign a valid sequential invoice number",
                "source_document_id": invoice.get("document_id"),
            })

        return anomalies

    def _check_cross_anomalies(self, invoices: list[dict], transactions: list[dict]) -> list[dict]:
        """Check for anomalies across invoices and bank transactions."""
        anomalies = []

        # Check for high-value invoices without corresponding bank entries
        for inv in invoices:
            if inv.get("total_amount", 0) > 100000:  # High-value > ₹1L
                # Check if any transaction matches
                matched = False
                for tx in transactions:
                    tx_amt = tx.get("credit", 0) or tx.get("debit", 0)
                    if abs(tx_amt - inv["total_amount"]) / inv["total_amount"] < 0.05:
                        matched = True
                        break
                if not matched:
                    anomalies.append({
                        "severity": "medium",
                        "category": "reconciliation_gap",
                        "title": f"No payment found for invoice: {inv.get('invoice_number', 'N/A')}",
                        "description": f"High-value invoice ₹{inv['total_amount']:,.2f} has no matching bank transaction",
                        "suggestion": "Verify payment status and reconcile",
                        "source_document_id": inv.get("document_id"),
                    })

        return anomalies

    def _check_tax_calculations(self, invoices: list[dict]) -> list[dict]:
        """Verify tax calculations on invoices."""
        anomalies = []

        for inv in invoices:
            taxable = inv.get("taxable_amount", 0)
            if taxable <= 0:
                continue

            # Verify CGST @ 9% (standard rate)
            cgst_amt = inv.get("cgst_amount", 0)
            cgst_rate = inv.get("cgst_rate", 0)
            if cgst_amt > 0 and cgst_rate > 0:
                expected_cgst = round(taxable * cgst_rate / 100, 2)
                if abs(expected_cgst - cgst_amt) > 0.5:
                    anomalies.append({
                        "severity": "low",
                        "category": "tax_error",
                        "title": f"CGST calculation error: {inv.get('invoice_number', 'N/A')}",
                        "description": f"Expected CGST = {cgst_rate}% of ₹{taxable:,.2f} = ₹{expected_cgst:,.2f}, Actual: ₹{cgst_amt:,.2f}",
                        "suggestion": "Recheck CGST calculation",
                        "source_document_id": inv.get("document_id"),
                    })

        return anomalies
