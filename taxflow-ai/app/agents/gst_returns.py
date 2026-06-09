"""GSTR Returns Agent - generates GSTR-1 and GSTR-3B data from invoices."""

import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Optional

from app.database import get_invoices, save_gstr1, save_gstr3b
from app.ollama_client import TaxFlowOllama
from app.prompts import get_prompt


class GSTRReturnsAgent:
    """Agent for generating GSTR-1 and GSTR-3B returns."""

    def __init__(self, ollama_client: TaxFlowOllama):
        self.llm = ollama_client

    def generate_gstr1(self, project_id: str, message: str) -> dict[str, Any]:
        """Generate GSTR-1 return data from invoices."""
        invoices = get_invoices(project_id)

        if not invoices:
            return {
                "response": "No invoices found. Please upload invoices first to generate GSTR-1 data.",
                "actions": [],
            }

        # Extract period from message or use current month
        period = self._extract_period(message)
        if not period:
            period = datetime.now().strftime("%m%Y")

        # Categorize invoices
        b2b = []
        b2c = []
        exports = []
        credit_notes = []
        debit_notes = []

        for inv in invoices:
            if inv.get("buyer_gstin") and len(inv.get("buyer_gstin", "")) == 15:
                b2b.append(inv)
            elif inv.get("buyer_name", "").upper() in ("SEZ", "EXPORT", ""):
                exports.append(inv)
            else:
                b2c.append(inv)

        # Calculate rate-wise summaries
        rate_wise = defaultdict(lambda: {
            "taxable_amount": 0.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "igst": 0.0,
            "cess": 0.0,
            "count": 0,
        })

        for inv in invoices:
            # Determine effective tax rate
            total_tax = inv.get("cgst_amount", 0) + inv.get("sgst_amount", 0) + inv.get("igst_amount", 0)
            taxable = inv.get("taxable_amount", 0)
            if taxable > 0:
                rate = round((total_tax / taxable) * 100, 1)
                rate_key = f"{rate:.1f}%"
                rate_wise[rate_key]["taxable_amount"] += taxable
                rate_wise[rate_key]["cgst"] += inv.get("cgst_amount", 0)
                rate_wise[rate_key]["sgst"] += inv.get("sgst_amount", 0)
                rate_wise[rate_key]["igst"] += inv.get("igst_amount", 0)
                rate_wise[rate_key]["cess"] += inv.get("cess_amount", 0)
                rate_wise[rate_key]["count"] += 1

        gstr1_data = {
            "period": period,
            "gstin": invoices[0].get("seller_gstin", ""),  # Use first invoice's seller as the filer
            "legal_name": invoices[0].get("seller_name", ""),
            "b2b_invoices": [
                {
                    "invoice_number": i["invoice_number"],
                    "invoice_date": i["invoice_date"],
                    "buyer_gstin": i["buyer_gstin"],
                    "buyer_name": i["buyer_name"],
                    "taxable_amount": i["taxable_amount"],
                    "cgst_amount": i["cgst_amount"],
                    "sgst_amount": i["sgst_amount"],
                    "igst_amount": i["igst_amount"],
                    "total_amount": i["total_amount"],
                }
                for i in b2b
            ],
            "b2c_invoices": [
                {
                    "invoice_number": i["invoice_number"],
                    "taxable_amount": i["taxable_amount"],
                    "total_amount": i["total_amount"],
                }
                for i in b2c
            ],
            "exports": [
                {
                    "invoice_number": i["invoice_number"],
                    "taxable_amount": i["taxable_amount"],
                    "total_amount": i["total_amount"],
                }
                for i in exports
            ],
            "rate_wise_summary": dict(rate_wise),
            "summary": {
                "total_b2b_invoices": len(b2b),
                "total_b2c_invoices": len(b2c),
                "total_exports": len(exports),
                "total_taxable_amount": sum(i["taxable_amount"] for i in invoices),
                "total_tax": sum(i["cgst_amount"] + i["sgst_amount"] + i["igst_amount"] + i["cess_amount"] for i in invoices),
                "total_invoice_value": sum(i["total_amount"] for i in invoices),
            },
        }

        # Save to database
        save_gstr1(project_id, period, gstr1_data)

        # Generate AI narrative
        response = self.llm.chat([
            {"role": "system", "content": get_prompt("gstr1_generation")},
            {"role": "user", "content": f"""GSTR-1 data generated for period {period[:2]}/{period[2:]}.

Summary:
{json.dumps(gstr1_data['summary'], indent=2)}

Rate-wise breakdown:
{json.dumps(rate_wise, indent=2)}

B2B invoices: {len(b2b)}
B2C invoices: {len(b2c)}

Provide:
1. GSTR-1 summary for filing
2. Key observations about the data
3. Any discrepancies that need attention before filing"""}
        ])

        actions = [
            f"Generated GSTR-1 data for period {period[:2]}/{period[2:]}",
            f"Categorized {len(invoices)} invoices into B2B ({len(b2b)}), B2C ({len(b2c)}), Exports ({len(exports)})",
            f"Total taxable value: ₹{gstr1_data['summary']['total_taxable_amount']:,.2f}",
        ]

        return {
            "response": response,
            "actions": actions,
            "data": gstr1_data,
        }

    def generate_gstr3b(self, project_id: str, message: str) -> dict[str, Any]:
        """Generate GSTR-3B summary return data."""
        invoices = get_invoices(project_id)

        if not invoices:
            return {
                "response": "No invoices found. Please upload invoices first to generate GSTR-3B data.",
                "actions": [],
            }

        period = self._extract_period(message)
        if not period:
            period = datetime.now().strftime("%m%Y")

        # Table 3: Turnover details
        rate_wise_turnover = defaultdict(float)
        for inv in invoices:
            rate_wise_turnover["taxable"] += inv.get("taxable_amount", 0)

        # Table 4: ITC details
        eligible_itc = sum(
            inv.get("cgst_amount", 0) + inv.get("sgst_amount", 0) + inv.get("igst_amount", 0)
            for inv in invoices
        )

        # Calculate by tax type
        total_cgst = sum(i.get("cgst_amount", 0) for i in invoices)
        total_sgst = sum(i.get("sgst_amount", 0) for i in invoices)
        total_igst = sum(i.get("igst_amount", 0) for i in invoices)
        total_cess = sum(i.get("cess_amount", 0) for i in invoices)

        gstr3b_data = {
            "period": period,
            "gstin": invoices[0].get("seller_gstin", ""),
            "legal_name": invoices[0].get("seller_name", ""),
            "table_3_turnover": {
                "3a_taxable_outward_supply": rate_wise_turnover["taxable"],
                "3b_nil_rated": 0.0,
                "3c_exempted": 0.0,
                "3d_nil_rated_taxable": 0.0,
                "3e_total_turnover": rate_wise_turnover["taxable"],
            },
            "table_4_itc": {
                "4a_itc_available": eligible_itc,
                "4b_itc_reversed": 0.0,
                "4c_net_itc": eligible_itc,
                "4d_ineligible_itc": 0.0,
                "itc_breakdown": {
                    "cgst": total_cgst,
                    "sgst": total_sgst,
                    "igst": total_igst,
                    "cess": total_cess,
                },
            },
            "table_5_tax_liability": {
                "cgst_payable": total_cgst,
                "sgst_payable": total_sgst,
                "igst_payable": total_igst,
                "cess_payable": total_cess,
                "total_tax_liability": total_cgst + total_sgst + total_igst + total_cess,
            },
            "summary": {
                "total_invoices": len(invoices),
                "total_taxable_amount": rate_wise_turnover["taxable"],
                "total_tax": eligible_itc,
                "total_invoice_value": sum(i["total_amount"] for i in invoices),
            },
        }

        save_gstr3b(project_id, period, gstr3b_data)

        response = self.llm.chat([
            {"role": "system", "content": get_prompt("gstr3b_generation")},
            {"role": "user", "content": f"""GSTR-3B data generated for period {period[:2]}/{period[2:]}.

Data:
{json.dumps(gstr3b_data, indent=2, default=str)}

Provide:
1. GSTR-3B filing summary
2. ITC position analysis
3. Tax payable summary
4. Key observations and recommendations before filing"""}
        ])

        actions = [
            f"Generated GSTR-3B data for period {period[:2]}/{period[2:]}",
            f"Net ITC available: ₹{eligible_itc:,.2f}",
            f"Total tax liability: ₹{gstr3b_data['table_5_tax_liability']['total_tax_liability']:,.2f}",
        ]

        return {
            "response": response,
            "actions": actions,
            "data": gstr3b_data,
        }

    def _extract_period(self, message: str) -> Optional[str]:
        """Extract period (MMYYYY) from a message."""
        import re

        # Try to find month and year patterns
        patterns = [
            r"(\d{2})[\/-]?(\d{4})",  # MMYYYY or MM/YYYY or MM-YYYY
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                month, year = match.groups()
                m = int(month)
                y = int(year)
                if 1 <= m <= 12 and 2000 <= y <= 2100:
                    return f"{m:02d}{y}"

        # Try month names
        month_names = {
            "january": "01", "february": "02", "march": "03", "april": "04",
            "may": "05", "june": "06", "july": "07", "august": "08",
            "september": "09", "october": "10", "november": "11", "december": "12",
        }
        for name, num in month_names.items():
            if name in message.lower():
                year_match = re.search(r"20\d{2}", message)
                if year_match:
                    return f"{num}{year_match.group()}"
                break

        return None
