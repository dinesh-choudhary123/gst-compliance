"""Bank reconciliation agent - matches bank transactions to invoices."""

import json
from datetime import datetime, timedelta
from typing import Any, Optional

from app.database import (
    get_invoices,
    get_bank_transactions,
    save_anomaly,
)
from app.ollama_client import TaxFlowOllama
from app.prompts import get_prompt


class ReconcilerAgent:
    """Agent that reconciles bank transactions with invoices."""

    def __init__(self, ollama_client: TaxFlowOllama):
        self.llm = ollama_client

    def reconcile(self, project_id: str, message: str) -> dict[str, Any]:
        """Perform bank reconciliation."""
        invoices = get_invoices(project_id)
        transactions = get_bank_transactions(project_id)

        if not invoices or not transactions:
            missing = []
            if not invoices:
                missing.append("invoices")
            if not transactions:
                missing.append("bank transactions")
            return {
                "response": f"No {' or '.join(missing)} found. Please upload both invoices and bank statements to perform reconciliation.",
                "actions": [],
            }

        # Perform automated matching
        matches = self._auto_match(invoices, transactions)
        unmatched_invoices = [i for i in invoices if not any(m["invoice_id"] == i["id"] for m in matches if m["confidence"] > 0.5)]
        unmatched_transactions = [t for t in transactions if not any(m["transaction_id"] == t["id"] for m in matches if m["confidence"] > 0.5)]

        # Save anomalies for mismatches
        for match in matches:
            if match["confidence"] < 0.8:
                save_anomaly(project_id, {
                    "severity": "medium" if match["confidence"] < 0.5 else "low",
                    "category": "reconciliation_mismatch",
                    "title": f"Low confidence match: {match.get('invoice_number', 'Unknown')}",
                    "description": match.get("notes", "Partial match found"),
                    "suggestion": "Verify manually and adjust",
                })

        # Generate AI summary
        summary_data = {
            "total_invoices": len(invoices),
            "total_transactions": len(transactions),
            "matched_count": len(matches),
            "high_confidence_matches": len([m for m in matches if m["confidence"] >= 0.8]),
            "unmatched_invoices": len(unmatched_invoices),
            "unmatched_transactions": len(unmatched_transactions),
            "total_invoice_amount": sum(i["total_amount"] for i in invoices),
            "total_credits": sum(t["credit"] for t in transactions),
            "total_debits": sum(t["debit"] for t in transactions),
            "matches": matches[:20],
        }

        response = self.llm.chat([
            {"role": "system", "content": get_prompt("reconciliation")},
            {"role": "user", "content": f"""Perform reconciliation analysis for this client data:
{json.dumps(summary_data, indent=2, default=str)}

Provide:
1. Summary of matching results
2. List of matched payments with confidence levels
3. Unmatched items that need attention
4. Outstanding amounts
5. Recommendations for resolving discrepancies"""}
        ])

        actions = [f"Reconciled {len(matches)} invoice-transaction pairs",
                   f"Found {len(unmatched_invoices)} unmatched invoices",
                   f"Found {len(unmatched_transactions)} unmatched transactions"]

        return {
            "response": response,
            "actions": actions,
            "data": summary_data,
        }

    def _auto_match(self, invoices: list[dict], transactions: list[dict]) -> list[dict]:
        """Automatically match invoices to bank transactions."""
        matches = []

        for invoice in invoices:
            inv_amount = invoice["total_amount"]
            best_match = None
            best_score = 0.0

            for tx in transactions:
                score = 0.0
                notes = []

                # Check amount match (allow small variance)
                tx_amount = tx.get("credit", 0) or tx.get("debit", 0)
                if abs(tx_amount - inv_amount) / max(inv_amount, 1) < 0.02:
                    score += 0.6
                    notes.append("Amount matches within 2% tolerance")
                elif abs(tx_amount - inv_amount) / max(inv_amount, 1) < 0.1:
                    score += 0.3
                    notes.append("Amount matches within 10% tolerance (partial payment?)")

                # Check date proximity
                inv_date = invoice.get("invoice_date", "")
                tx_date = tx.get("transaction_date", "")
                if inv_date and tx_date:
                    try:
                        inv_dt = datetime.fromisoformat(inv_date)
                        tx_dt = datetime.fromisoformat(tx_date)
                        days_diff = abs((inv_dt - tx_dt).days)
                        if days_diff <= 3:
                            score += 0.3
                            notes.append("Transaction within 3 days of invoice")
                        elif days_diff <= 7:
                            score += 0.2
                            notes.append("Transaction within 7 days of invoice")
                        elif days_diff <= 30:
                            score += 0.1
                    except (ValueError, TypeError):
                        pass

                # Check narration for invoice number or party name
                narration = tx.get("narration", "").lower()
                inv_number = invoice.get("invoice_number", "").lower()
                seller = invoice.get("seller_name", "").lower()
                buyer = invoice.get("buyer_name", "").lower()

                if inv_number and inv_number in narration:
                    score += 0.4
                    notes.append("Invoice number found in narration")

                if seller and seller.split()[0] in narration:
                    score += 0.2
                    notes.append("Seller name found in narration")
                if buyer and buyer.split()[0] in narration:
                    score += 0.2
                    notes.append("Buyer name found in narration")

                if score > best_score:
                    best_score = score
                    best_match = {
                        "invoice_id": invoice["id"],
                        "invoice_number": invoice["invoice_number"],
                        "invoice_amount": inv_amount,
                        "transaction_id": tx["id"],
                        "transaction_amount": tx_amount,
                        "transaction_date": tx["transaction_date"],
                        "narration": tx["narration"],
                        "confidence": round(score, 2),
                        "notes": "; ".join(notes) if notes else "Automated match",
                    }

            if best_match and best_score > 0.3:
                matches.append(best_match)

        return matches
