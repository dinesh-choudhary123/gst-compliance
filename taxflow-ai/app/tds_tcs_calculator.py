"""TDS/TCS Calculator and Form 26Q ready data generation.

Calculates TDS/TCS under GST and Income Tax provisions,
generates Form 26Q compatible data for quarterly filing.
"""

import csv
import io
import json
from collections import defaultdict
from datetime import datetime, date
from typing import Any, Optional

from app.database import get_invoices, get_bank_transactions


# ================================================================
# TDS RATES UNDER INCOME TAX ACT (FY 2025-26)
# ================================================================

TDS_RATES_IT = {
    "rent_plant_machinery": {"code": "194I", "rate": 2.0, "threshold": 240000, "description": "Rent - Plant & Machinery"},
    "rent_land_building": {"code": "194I", "rate": 10.0, "threshold": 240000, "description": "Rent - Land/Building/Furniture"},
    "contractor": {"code": "194C", "rate": 1.0, "threshold": 30000, "description": "Contractor - Individual/HUF (single contract)"},
    "contractor_company": {"code": "194C", "rate": 2.0, "threshold": 30000, "description": "Contractor - Others"},
    "professional_fees": {"code": "194J", "rate": 10.0, "threshold": 30000, "description": "Professional/Technical Fees"},
    "salary": {"code": "192", "rate": 0.0, "threshold": 250000, "description": "Salary (slab rate)"},
    "interest_others": {"code": "194A", "rate": 10.0, "threshold": 5000, "description": "Interest - Others"},
    "interest_senior": {"code": "194A", "rate": 10.0, "threshold": 50000, "description": "Interest - Senior Citizens"},
    "dividend": {"code": "194", "rate": 10.0, "threshold": 5000, "description": "Dividend"},
    "commission": {"code": "194H", "rate": 5.0, "threshold": 15000, "description": "Commission/Brokerage"},
    "rent_furniture": {"code": "194I", "rate": 10.0, "threshold": 240000, "description": "Rent - Furniture"},
}

# TDS RATES UNDER GST (Section 51)
TDS_RATES_GST = {
    "gst_tds": {"rate": 2.0, "cgst": 1.0, "sgst": 1.0, "igst": 2.0, "threshold": 250000,
                "description": "TDS under GST (Govt/PSU contracts)"},
}

# TCS RATES UNDER GST (Section 52)
TCS_RATES_GST = {
    "gst_tcs": {"rate": 1.0, "cgst": 0.5, "sgst": 0.5, "igst": 1.0,
                "description": "TCS under GST (E-commerce operators)"},
}


class TDSCalculator:
    """Calculate TDS under Income Tax and GST provisions."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.invoices = get_invoices(project_id)
        self.transactions = get_bank_transactions(project_id)

    def calculate_tds_it(self, assessment_year: Optional[str] = None) -> dict:
        """Calculate TDS under Income Tax Act from invoice data."""
        assessment_year = assessment_year or f"{date.today().year}-{date.today().year + 1}"

        tds_summary = defaultdict(lambda: {
            "code": "", "rate": 0.0, "threshold": 0,
            "total_amount": 0.0, "tds_amount": 0.0, "count": 0,
            "description": "", "transactions": [],
        })

        for inv in self.invoices:
            total_amount = inv.get("total_amount", 0)

            # Classify by seller/buyer name for TDS type
            seller_name = (inv.get("seller_name", "") or "").lower()
            narration = f"Payment to {seller_name}"

            # Check for professional fees (SAC 99)
            hsn_codes = inv.get("hsn_codes", [])
            is_service = any(
                str(h.get("code", "")).startswith("99") for h in hsn_codes
            )

            if is_service and total_amount >= 30000:
                key = "professional_fees"
                rate_info = TDS_RATES_IT[key]
                tds = round(total_amount * rate_info["rate"] / 100, 2)
                tds_summary[key]["code"] = rate_info["code"]
                tds_summary[key]["rate"] = rate_info["rate"]
                tds_summary[key]["threshold"] = rate_info["threshold"]
                tds_summary[key]["description"] = rate_info["description"]
                tds_summary[key]["total_amount"] += total_amount
                tds_summary[key]["tds_amount"] += tds
                tds_summary[key]["count"] += 1
                tds_summary[key]["transactions"].append({
                    "invoice": inv.get("invoice_number", ""),
                    "amount": total_amount,
                    "tds": tds,
                    "party": inv.get("buyer_name", inv.get("seller_name", "")),
                    "date": inv.get("invoice_date", ""),
                })

        # Convert to list
        results = []
        for key, data in tds_summary.items():
            if data["count"] > 0:
                results.append({"type": key, **data})

        total_tds = sum(r["tds_amount"] for r in results)

        return {
            "assessment_year": assessment_year,
            "generated_at": datetime.now().isoformat(),
            "total_tds_deducted": round(total_tds, 2),
            "total_transactions_reviewed": len(self.invoices),
            "sections": results,
        }

    def calculate_tds_gst(self) -> dict:
        """Calculate TDS under GST (applicable for Govt/PSU contracts)."""
        total_contract_value = sum(i.get("total_amount", 0) for i in self.invoices)
        
        if total_contract_value <= TDS_RATES_GST["gst_tds"]["threshold"]:
            return {
                "applicable": False,
                "message": "No TDS applicable (contract value below ₹2.5 lakhs threshold)",
                "total_amount": total_contract_value,
            }

        tds_rate = TDS_RATES_GST["gst_tds"]
        tds_total = round(total_contract_value * tds_rate["rate"] / 100, 2)

        return {
            "applicable": True,
            "rate": tds_rate["rate"],
            "total_amount": round(total_contract_value, 2),
            "total_tds": tds_total,
            "cgst_tds": round(total_contract_value * tds_rate["cgst"] / 100, 2),
            "sgst_tds": round(total_contract_value * tds_rate["sgst"] / 100, 2),
            "igst_tds": round(total_contract_value * tds_rate["igst"] / 100, 2),
            "description": tds_rate["description"],
            "threshold": tds_rate["threshold"],
        }

    def calculate_tcs_gst(self) -> dict:
        """Calculate TCS under GST (applicable for E-commerce operators)."""
        total_sales = sum(i.get("total_amount", 0) for i in self.invoices)

        if total_sales <= 0:
            return {"applicable": False, "message": "No taxable supplies found"}

        tcs_rate = TCS_RATES_GST["gst_tcs"]
        tcs_total = round(total_sales * tcs_rate["rate"] / 100, 2)

        return {
            "applicable": True,
            "rate": tcs_rate["rate"],
            "total_supplies": round(total_sales, 2),
            "total_tcs": tcs_total,
            "cgst_tcs": round(total_sales * tcs_rate["cgst"] / 100, 2),
            "sgst_tcs": round(total_sales * tcs_rate["sgst"] / 100, 2),
            "igst_tcs": round(total_sales * tcs_rate["igst"] / 100, 2),
            "description": tcs_rate["description"],
        }


# ================================================================
# FORM 26Q GENERATION
# ================================================================

def generate_form26q_csv(tds_data: dict) -> str:
    """Generate Form 26Q compatible CSV data for TDS on non-salary payments.

    Form 26Q is filed quarterly for TDS on payments other than salary.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Form 26Q - TDS on Non-Salary Payments",
        f"Generated: {datetime.now().strftime('%d-%m-%Y')}",
    ])
    writer.writerow([])

    writer.writerow([
        "Sr No", "Section Code", "TDS Rate (%)", "Deductor Name",
        "Deductee Name", "Deductee PAN", "Payment Date",
        "Amount Paid (₹)", "TDS Amount (₹)", "Surcharge", "Cess",
    ])

    sr_no = 1
    for section in tds_data.get("sections", []):
        for tx in section.get("transactions", []):
            tds_amt = tx.get("tds", 0)
            cess = round(tds_amt * 0.04, 2)  # 4% Health & Education Cess
            
            writer.writerow([
                sr_no,
                section.get("code", ""),
                section.get("rate", 0),
                "TaxFlow AI Client",
                tx.get("party", ""),
                "",  # PAN (user to fill)
                tx.get("date", "")[:10],
                tx.get("amount", 0),
                tds_amt,
                0,
                cess,
            ])
            sr_no += 1

    # Summary
    writer.writerow([])
    writer.writerow(["TOTAL", "", "", "", "", "", "",
                     tds_data.get("total_tds_deducted", 0)])

    return output.getvalue()


def format_tds_html(tds_data: dict) -> str:
    """Format TDS calculation results as styled HTML."""
    sections_html = ""

    for section in tds_data.get("sections", []):
        tx_rows = ""
        for tx in section.get("transactions", [])[:10]:
            tx_rows += f"""
            <tr>
                <td>{tx.get('invoice', '')}</td>
                <td>{tx.get('party', '')[:20]}</td>
                <td style="text-align:right;">₹{tx.get('amount', 0):,.2f}</td>
                <td style="text-align:right;">₹{tx.get('tds', 0):,.2f}</td>
            </tr>"""

        sections_html += f"""
        <div style="background:white;border:1px solid #E2E8F0;border-radius:8px;padding:12px;margin-bottom:8px;">
            <div style="font-weight:600;font-size:13px;margin-bottom:6px;">
                Section {section.get('code', '')} · {section.get('description', '')}
                <span style="float:right;">Rate: {section.get('rate', 0)}%</span>
            </div>
            <table style="width:100%;border-collapse:collapse;font-size:11px;">
                <thead><tr style="background:#1F4E79;color:white;">
                    <th style="padding:4px 8px;">Invoice</th>
                    <th style="padding:4px 8px;">Party</th>
                    <th style="padding:4px 8px;text-align:right;">Amount</th>
                    <th style="padding:4px 8px;text-align:right;">TDS</th>
                </tr></thead>
                <tbody>{tx_rows}</tbody>
            </table>
            <div style="font-size:12px;font-weight:600;padding:4px 8px 0;text-align:right;border-top:1px solid #E2E8F0;margin-top:4px;">
                Total TDS: <span style="color:#DC2626;">₹{section.get('tds_amount', 0):,.2f}</span>
            </div>
        </div>"""

    if not sections_html:
        sections_html = """
        <div style="text-align:center;padding:32px;color:#6B7280;">
            <div style="font-size:32px;margin-bottom:8px;">💰</div>
            <p>No TDS applicable for current data.<br>Thresholds not met or no professional/service invoices.</p>
        </div>"""

    return f"""
    <div style="background:white;border-radius:12px;border:1px solid #E2E8F0;padding:16px;">
        <h3 style="margin:0 0 4px 0;color:#1F4E79;">💰 TDS Calculation</h3>
        <p style="font-size:12px;color:#6B7280;margin:0 0 12px 0;">
            AY: {tds_data.get('assessment_year', '')} · 
            Reviewed: {tds_data.get('total_transactions_reviewed', 0)} invoices ·
            <strong>Total TDS: ₹{tds_data.get('total_tds_deducted', 0):,.2f}</strong>
        </p>
        {sections_html}
    </div>"""


def format_tcs_html(tcs_data: dict) -> str:
    """Format TCS calculation results as HTML."""
    if not tcs_data.get("applicable"):
        return f"<p style='color:#6B7280;'>{tcs_data.get('message', 'No TCS applicable')}</p>"

    return f"""
    <div style="background:white;border:1px solid #E2E8F0;border-radius:8px;padding:16px;">
        <h4 style="margin:0 0 8px;color:#1F4E79;">🛒 TCS under GST (Section 52)</h4>
        <table style="width:100%;font-size:13px;">
            <tr><td style="padding:4px 8px;">Total Supplies</td><td style="text-align:right;">₹{tcs_data['total_supplies']:,.2f}</td></tr>
            <tr><td style="padding:4px 8px;">TCS Rate</td><td style="text-align:right;">{tcs_data['rate']}%</td></tr>
            <tr><td style="padding:4px 8px;font-weight:600;">Total TCS</td><td style="text-align:right;color:#DC2626;font-weight:700;">₹{tcs_data['total_tcs']:,.2f}</td></tr>
            <tr><td style="padding:4px 8px;">CGST Component</td><td style="text-align:right;">₹{tcs_data['cgst_tcs']:,.2f}</td></tr>
            <tr><td style="padding:4px 8px;">SGST Component</td><td style="text-align:right;">₹{tcs_data['sgst_tcs']:,.2f}</td></tr>
            <tr><td style="padding:4px 8px;">IGST Component</td><td style="text-align:right;">₹{tcs_data['igst_tcs']:,.2f}</td></tr>
        </table>
    </div>"""
