"""ITC Matching Agent - verifies Input Tax Credit eligibility and matching."""

import json
from typing import Any

from app.database import get_invoices, save_anomaly, save_bank_transaction
from app.ollama_client import TaxFlowOllama
from app.prompts import get_prompt


class ITCMatcherAgent:
    """Agent for Input Tax Credit matching and verification."""

    def __init__(self, ollama_client: TaxFlowOllama):
        self.llm = ollama_client

    def match_itc(self, project_id: str, message: str) -> dict[str, Any]:
        """Perform ITC matching on invoices."""
        invoices = get_invoices(project_id)

        if not invoices:
            return {
                "response": "No invoices found. Please upload invoices first to perform ITC matching.",
                "actions": [],
            }

        # Analyze each invoice for ITC eligibility
        itc_results = []
        total_eligible_itc = 0.0
        total_ineligible_itc = 0.0

        for invoice in invoices:
            result = self._check_itc_eligibility(invoice)
            itc_results.append(result)
            if result["eligible"]:
                total_eligible_itc += result["eligible_amount"]
            else:
                total_ineligible_itc += result.get("total_tax", 0)

            # Save anomaly for ineligible ITC
            if not result["eligible"] and result.get("reasons"):
                save_anomaly(project_id, {
                    "severity": "high" if result.get("is_blocked") else "medium",
                    "category": "itc_issue",
                    "title": f"ITC issue: {invoice.get('invoice_number', 'Unknown')}",
                    "description": "; ".join(result["reasons"]),
                    "suggestion": result.get("suggestion", "Review ITC eligibility criteria"),
                    "source_document_id": invoice.get("document_id"),
                })

        summary = {
            "total_invoices_reviewed": len(invoices),
            "invoices_with_itc_issues": len([r for r in itc_results if not r["eligible"]]),
            "total_eligible_itc": total_eligible_itc,
            "total_ineligible_itc": total_ineligible_itc,
            "eligible_invoices": len([r for r in itc_results if r["eligible"]]),
        }

        response = self.llm.chat([
            {"role": "system", "content": get_prompt("anomaly_detection")},
            {"role": "user", "content": f"""ITC matching completed for {len(invoices)} invoices.

Summary:
- Total eligible ITC: ₹{total_eligible_itc:,.2f}
- Total ineligible ITC: ₹{total_ineligible_itc:,.2f}
- Invoices with issues: {summary['invoices_with_itc_issues']}

Detailed results:
{json.dumps(itc_results[:10], indent=2, default=str)}

Provide a detailed ITC analysis including:
1. Total eligible ITC amount with breakdown
2. Ineligible items and reasons
3. Recommendations for optimizing ITC claims
4. Documents needed for ITC compliance"""}
        ])

        actions = [
            f"Reviewed ITC eligibility for {len(invoices)} invoices",
            f"Found ₹{total_eligible_itc:,.2f} eligible ITC",
            f"Flagged {summary['invoices_with_itc_issues']} invoice(s) with ITC issues",
        ]

        return {
            "response": response,
            "actions": actions,
            "data": summary,
        }

    def _check_itc_eligibility(self, invoice: dict) -> dict:
        """Check ITC eligibility for a single invoice."""
        reasons = []
        eligible = True
        is_blocked = False

        total_tax = (invoice.get("cgst_amount", 0) +
                     invoice.get("sgst_amount", 0) +
                     invoice.get("igst_amount", 0) +
                     invoice.get("cess_amount", 0))

        # Check 1: Valid GSTIN of supplier
        seller_gstin = invoice.get("seller_gstin", "")
        if not seller_gstin or len(seller_gstin) != 15:
            reasons.append("Invalid or missing seller GSTIN")
            eligible = False

        # Check 2: Invoice from registered dealer
        if not seller_gstin.startswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
            reasons.append("Seller may be unregistered (no valid GSTIN)")
            eligible = False

        # Check 3: Goods received (for most cases)
        # Note: This requires a separate e-way bill or receipt note

        # Check 4: Tax invoice vs bill of supply
        # Composition dealers issue bill of supply - no ITC available

        # Check 5: Specific blocked credits under Section 17(5)
        # Examples: motor vehicles (except specified), food & beverages, etc.
        hsn_codes = invoice.get("hsn_codes", [])
        for hsn_item in hsn_codes:
            code = str(hsn_item.get("code", ""))
            if code.startswith(("87", "22")):  # Motor vehicles, beverages
                reasons.append(f"HSN {code}: May be blocked credit under Section 17(5)")
                is_blocked = True
                eligible = False

        # Check 6: Reverse charge applicability
        if invoice.get("reverse_charge"):
            reasons.append("Reverse charge transaction - verify ITC eligibility")
            # RCM transactions are eligible if paid

        # Calculate eligible amount
        eligible_amount = 0.0
        if eligible:
            eligible_amount = total_tax
        elif not is_blocked:
            # Partially eligible - some portion may be claimable
            eligible_amount = total_tax * 0.5 if total_tax > 0 else 0.0

        suggestion = ""
        if not eligible:
            if is_blocked:
                suggestion = "This ITC is blocked under Section 17(5) of CGST Act. Cannot be claimed."
            elif not seller_gstin:
                suggestion = "Obtain valid GST invoice from supplier to claim ITC."
            else:
                suggestion = "Review ITC conditions under Section 16 of CGST Act."

        return {
            "invoice_number": invoice.get("invoice_number", "N/A"),
            "seller_name": invoice.get("seller_name", ""),
            "seller_gstin": seller_gstin,
            "invoice_amount": invoice.get("total_amount", 0),
            "total_tax": total_tax,
            "eligible": eligible,
            "eligible_amount": eligible_amount if eligible else 0.0,
            "reasons": reasons,
            "is_blocked": is_blocked,
            "suggestion": suggestion,
        }
