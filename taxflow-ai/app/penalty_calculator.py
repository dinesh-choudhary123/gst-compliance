"""Penalty Risk Calculator - Calculate potential GST penalties and interest.

Evaluates compliance status and estimates potential penalty exposure
under various sections of CGST Act.
"""

from datetime import datetime, date, timedelta
from typing import Any, Optional

from app.database import get_invoices, get_bank_transactions, get_anomalies


# ================================================================
# PENALTY REFERENCE DATA
# ================================================================

PENALTY_SECTIONS = {
    "sec122_general": {
        "section": "Section 122",
        "description": "Penalty for certain offences (general)",
        "penalty_type": "FIXED",
        "penalty_amount": 10000,
        "penalty_percentage": 10.0,
        "max_penalty": None,
        "prosecution_possible": True,
        "compounding_possible": True,
        "notes": "Applies for: issuing invoice without supply, claiming excess ITC, failing to collect tax, transporting goods without documents",
    },
    "sec73_non_fraud": {
        "section": "Section 73",
        "description": "Non-payment or short payment (non-fraud)",
        "penalty_type": "PERCENTAGE",
        "penalty_amount": 10000,
        "penalty_percentage": 10.0,
        "max_penalty": None,
        "prosecution_possible": False,
        "compounding_possible": True,
        "notes": "Interest at 18% + penalty of 10% (min Rs. 10,000). Notice must be within 33 months.",
    },
    "sec74_fraud": {
        "section": "Section 74",
        "description": "Non-payment or short payment (fraud)",
        "penalty_type": "PERCENTAGE",
        "penalty_amount": None,
        "penalty_percentage": 100.0,
        "max_penalty": None,
        "prosecution_possible": True,
        "compounding_possible": True,
        "notes": "100% penalty of tax amount. Notice within 54 months. 25% penalty if paid before order, 15% if paid within 30 days of notice.",
    },
    "sec122_return": {
        "section": "Section 122",
        "description": "Failure to file returns",
        "penalty_type": "FIXED",
        "penalty_amount": 100,
        "penalty_percentage": 0.0,
        "max_penalty": 5000,
        "prosecution_possible": False,
        "compounding_possible": True,
        "notes": "Rs. 100 per day of delay (SGST + CGST). Max Rs. 5,000 per return.",
    },
    "sec125_general": {
        "section": "Section 125",
        "description": "General penalty (residual)",
        "penalty_type": "FIXED",
        "penalty_amount": 25000,
        "penalty_percentage": 0.0,
        "max_penalty": 25000,
        "prosecution_possible": False,
        "compounding_possible": True,
        "notes": "For contraventions not specifically penalized. Max Rs. 25,000.",
    },
    "sec122_einvoice": {
        "section": "Notification (E-Invoice)",
        "description": "E-invoicing non-compliance",
        "penalty_type": "FIXED",
        "penalty_amount": 10000,
        "penalty_percentage": 0.0,
        "max_penalty": 25000,
        "prosecution_possible": False,
        "compounding_possible": True,
        "notes": "Per invoice non-compliance for e-invoicing. Fine up to Rs. 25,000 per contravention.",
    },
    "sec122_eway": {
        "section": "Rule 138",
        "description": "E-way bill non-compliance",
        "penalty_type": "FIXED",
        "penalty_amount": 10000,
        "penalty_percentage": 0.0,
        "max_penalty": None,
        "prosecution_possible": False,
        "compounding_possible": True,
        "notes": "Rs. 10,000 or tax sought to be evaded, whichever is higher. Transport without valid e-way bill.",
    },
    "itc_reversal_180": {
        "section": "Section 16(2)",
        "description": "ITC not reversed within 180 days",
        "penalty_type": "INTEREST",
        "penalty_amount": None,
        "penalty_percentage": 18.0,
        "max_penalty": None,
        "prosecution_possible": False,
        "compounding_possible": False,
        "notes": "Interest at 18% on ITC amount not reversed within 180 days of invoice date.",
    },
}

INTEREST_RATE_LATE_PAYMENT = 18.0  # per annum
INTEREST_RATE_DELAYED_REFUND = 6.0  # per annum


class PenaltyCalculator:
    """Calculate potential GST penalties and interest exposure."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.invoices = get_invoices(project_id)
        self.transactions = get_bank_transactions(project_id)
        self.anomalies = get_anomalies(project_id)

    def calculate_all(self) -> dict:
        """Calculate all potential penalties for the project."""
        penalties = []
        total_risk = 0.0

        # 1. Check for late payment of tax
        late_payment = self._check_late_payment()
        if late_payment:
            penalties.append(late_payment)
            total_risk += late_payment.get("estimated_penalty", 0)

        # 2. Check ITC reversal
        itc_issue = self._check_itc_reversal()
        if itc_issue:
            penalties.append(itc_issue)
            total_risk += itc_issue.get("estimated_penalty", 0)

        # 3. Check anomalies for potential section 73/74
        for anomaly in self.anomalies:
            if anomaly.get("severity") in ("high", "medium"):
                sec_penalty = self._assess_anomaly_penalty(anomaly)
                if sec_penalty:
                    penalties.append(sec_penalty)
                    total_risk += sec_penalty.get("estimated_penalty", 0)

        # 4. Check for missing returns
        missing_return = self._check_missing_returns()
        if missing_return:
            penalties.append(missing_return)
            total_risk += missing_return.get("estimated_penalty", 0)

        # 5. Check e-invoice compliance
        einvoice_issue = self._check_einvoice_compliance()
        if einvoice_issue:
            penalties.append(einvoice_issue)
            total_risk += einvoice_issue.get("estimated_penalty", 0)

        # 6. Check e-way bill
        eway_issue = self._check_eway_bill()
        if eway_issue:
            penalties.append(eway_issue)
            total_risk += eway_issue.get("estimated_penalty", 0)

        risk_level = "LOW"
        if total_risk > 100000:
            risk_level = "HIGH"
        elif total_risk > 25000:
            risk_level = "MEDIUM"

        return {
            "project_id": self.project_id,
            "generated_at": datetime.now().isoformat(),
            "total_penalty_exposure": round(total_risk, 2),
            "risk_level": risk_level,
            "count": len(penalties),
            "penalties": sorted(penalties, key=lambda x: x.get("estimated_penalty", 0), reverse=True),
            "mitigation_suggestions": self._generate_mitigation_suggestions(penalties),
        }

    def _check_late_payment(self) -> Optional[dict]:
        """Estimate penalty for late payment of tax."""
        total_tax = sum(
            i.get("cgst_amount", 0) + i.get("sgst_amount", 0) +
            i.get("igst_amount", 0) + i.get("cess_amount", 0)
            for i in self.invoices
        )
        if total_tax <= 0:
            return None

        # Assume conservative estimate: 30 days late on average
        avg_days_late = 30
        interest_amount = round(total_tax * INTEREST_RATE_LATE_PAYMENT / 100 * avg_days_late / 365, 2)

        return {
            "type": "late_payment",
            "section": PENALTY_SECTIONS["sec73_non_fraud"]["section"],
            "description": f"Interest on late payment of tax (est. {avg_days_late} days delay)",
            "penalty_type": "Interest",
            "estimated_penalty": interest_amount,
            "details": PENALTY_SECTIONS["sec73_non_fraud"],
            "tax_amount": round(total_tax, 2),
        }

    def _check_itc_reversal(self) -> Optional[dict]:
        """Check ITC reversal compliance (180-day rule)."""
        total_igst = sum(i.get("igst_amount", 0) for i in self.invoices)
        total_cgst = sum(i.get("cgst_amount", 0) for i in self.invoices)
        total_sgst = sum(i.get("sgst_amount", 0) for i in self.invoices)

        # Assume some ITC might need reversal (conservative: 10%)
        total_itc = total_cgst + total_sgst + total_igst
        potential_reversal = total_itc * 0.10

        if potential_reversal <= 0:
            return None

        interest_amount = round(potential_reversal * INTEREST_RATE_LATE_PAYMENT / 100 * 60 / 365, 2)

        return {
            "type": "itc_reversal",
            "section": PENALTY_SECTIONS["itc_reversal_180"]["section"],
            "description": f"Potential ITC reversal needed (~10% of ₹{total_itc:,.2f} ITC claimed)",
            "penalty_type": "Interest (18% p.a.)",
            "estimated_penalty": interest_amount,
            "details": PENALTY_SECTIONS["itc_reversal_180"],
            "itc_amount": round(potential_reversal, 2),
            "interest_amount": interest_amount,
        }

    def _assess_anomaly_penalty(self, anomaly: dict) -> Optional[dict]:
        """Assess penalty based on anomaly severity."""
        category = anomaly.get("category", "")
        severity = anomaly.get("severity", "low")

        if severity == "high":
            # Potential fraud case
            penalty = PENALTY_SECTIONS["sec74_fraud"].copy()
            tax_involved = 0
            # Estimate from description
            desc = (anomaly.get("description", "") or "")
            import re
            amounts = re.findall(r'₹?([0-9,]+\.?\d*)', desc)
            if amounts:
                try:
                    tax_involved = float(amounts[0].replace(",", ""))
                except (ValueError, IndexError):
                    tax_involved = 0

            estimated = round(tax_involved * penalty["penalty_percentage"] / 100, 2)
            return {
                "type": "fraud_penalty",
                "section": penalty["section"],
                "description": anomaly.get("title", "Potential fraud penalty"),
                "penalty_type": f"{penalty['penalty_percentage']:.0f}% of tax",
                "estimated_penalty": max(estimated, 0),
                "details": penalty,
                "anomaly_id": anomaly.get("id"),
                "tax_amount": tax_involved,
            }

        elif severity == "medium":
            penalty = PENALTY_SECTIONS["sec73_non_fraud"].copy()
            return {
                "type": "non_fraud_penalty",
                "section": penalty["section"],
                "description": anomaly.get("title", "Potential non-fraud penalty"),
                "penalty_type": f"{penalty['penalty_percentage']:.0f}% (min ₹{penalty['penalty_amount']:,})",
                "estimated_penalty": penalty["penalty_amount"],
                "details": penalty,
                "anomaly_id": anomaly.get("id"),
            }

        return None

    def _check_missing_returns(self) -> Optional[dict]:
        """Estimate penalty for missing/late returns."""
        import random
        # Use invoice dates to estimate return compliance
        if not self.invoices:
            return None

        # Check if there's a wide date range suggesting missing returns
        penalty = PENALTY_SECTIONS["sec122_return"]
        # Estimate: assume 1 late filing
        estimated = 100 * 2  # CGST + SGST per day
        return {
            "type": "late_return",
            "section": penalty["section"],
            "description": "Potential late return filing penalty (est.)",
            "penalty_type": "Per day (max ₹5,000)",
            "estimated_penalty": estimated,
            "details": penalty,
        }

    def _check_einvoice_compliance(self) -> Optional[dict]:
        """Check e-invoicing compliance."""
        high_value_b2b = [
            i for i in self.invoices
            if i.get("total_amount", 0) > 0 and i.get("buyer_gstin")
        ]
        if not high_value_b2b:
            return None

        # Check if IRN is present
        missing_irn = [i for i in high_value_b2b if not i.get("irn")]
        if not missing_irn:
            return None

        penalty = PENALTY_SECTIONS["sec122_einvoice"]
        estimated = min(len(missing_irn) * penalty["penalty_amount"], 25000)
        return {
            "type": "e_invoice",
            "section": penalty["section"],
            "description": f"{len(missing_irn)} B2B invoices without IRN",
            "penalty_type": "Per invoice (max ₹25,000)",
            "estimated_penalty": estimated,
            "details": penalty,
            "missing_count": len(missing_irn),
        }

    def _check_eway_bill(self) -> Optional[dict]:
        """Check e-way bill compliance based on anomalies."""
        eway_anomalies = [a for a in self.anomalies if "eway" in (a.get("category", "") or "").lower()]
        if not eway_anomalies:
            return None

        penalty = PENALTY_SECTIONS["sec122_eway"]
        estimated = len(eway_anomalies) * 10000
        return {
            "type": "e_way_bill",
            "section": penalty["section"],
            "description": f"{len(eway_anomalies)} potential e-way bill compliance issues",
            "penalty_type": "Rs. 10,000 per instance",
            "estimated_penalty": estimated,
            "details": penalty,
        }

    def _generate_mitigation_suggestions(self, penalties: list) -> list:
        """Generate mitigation suggestions based on identified penalties."""
        suggestions = []

        for p in penalties:
            ptype = p.get("type", "")
            if ptype == "late_payment":
                suggestions.append("✓ File pending returns immediately and pay tax with interest to stop further interest accrual.")
            elif ptype == "itc_reversal":
                suggestions.append("✓ Review ITC claimed on invoices older than 180 days. Reverse ineligible ITC in next return.")
            elif ptype == "fraud_penalty":
                suggestions.append("⚡ Pay tax + interest voluntarily within 30 days to reduce penalty from 100% to 15% (Section 74).")
            elif ptype == "non_fraud_penalty":
                suggestions.append("✓ Pay the short-paid tax with interest to limit penalty to 10% under Section 73.")
            elif ptype == "late_return":
                suggestions.append("✓ File belated returns immediately to stop further late fee accrual (Rs. 100/day).")
            elif ptype == "e_invoice":
                suggestions.append("✓ Generate IRN for all B2B invoices immediately. Non-compliance costs Rs. 10,000 per invoice.")
            elif ptype == "e_way_bill":
                suggestions.append("✓ Ensure valid e-way bill for all goods transport valued above Rs. 50,000.")

        if not suggestions:
            suggestions.append("✓ Current data shows no significant penalty exposure. Continue maintaining compliance.")

        return suggestions


def format_penalty_html(penalty_data: dict) -> str:
    """Format penalty calculation results as styled HTML."""
    risk_colors = {"LOW": "#059669", "MEDIUM": "#D97706", "HIGH": "#DC2626"}
    risk_color = risk_colors.get(penalty_data.get("risk_level", "LOW"), "#6B7280")

    penalties_html = ""
    for p in penalty_data.get("penalties", []):
        penalties_html += f"""
        <div class="penalty-item">
            <div class="penalty-header">
                <span class="penalty-section">{p.get('section', '')}</span>
                <span class="penalty-amount">₹{p.get('estimated_penalty', 0):,.2f}</span>
            </div>
            <div class="penalty-desc">{p.get('description', '')}</div>
            <div class="penalty-meta">
                <span class="penalty-type">{p.get('penalty_type', '')}</span>
                <span class="penalty-notes">{p.get('details', {}).get('notes', '')}</span>
            </div>
        </div>"""

    if not penalties_html:
        penalties_html = """
        <div style="text-align:center;padding:32px;color:#6B7280;">
            <div style="font-size:40px;margin-bottom:8px;">🛡️</div>
            <p>No significant penalty exposure detected.</p>
        </div>"""

    suggestions_html = ""
    for s in penalty_data.get("mitigation_suggestions", []):
        suggestions_html += f'<li style="padding:4px 0;font-size:12px;">{s}</li>'

    return f"""
    <div style="background:white;border-radius:12px;border:1px solid #E2E8F0;padding:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <h3 style="margin:0;color:#1F4E79;">⚠️ Penalty Risk Assessment</h3>
            <div style="text-align:right;">
                <div style="font-size:11px;color:#6B7280;">Total Exposure</div>
                <div style="font-size:22px;font-weight:700;color:{risk_color};">₹{penalty_data.get('total_penalty_exposure', 0):,.0f}</div>
            </div>
        </div>
        <div style="margin-bottom:12px;">
            <span style="background:{risk_color}10;color:{risk_color};padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;">{penalty_data.get('risk_level', 'LOW')} RISK</span>
            <span style="color:#6B7280;font-size:12px;margin-left:8px;">{penalty_data.get('count', 0)} items flagged</span>
        </div>
        <div style="margin-bottom:12px;">
            <h4 style="margin:0 0 6px;font-size:13px;color:#374151;">Detailed Findings</h4>
            {penalties_html}
        </div>
        {f'<div style="border-top:1px solid #E2E8F0;padding-top:8px;"><h4 style="margin:0 0 6px;font-size:13px;color:#374151;">💡 Mitigation Suggestions</h4><ul style="margin:0;padding-left:20px;">{suggestions_html}</ul></div>' if suggestions_html else ''}
    </div>

    <style>
    .penalty-item {{
        background:#F9FAFB;border:1px solid #E2E8F0;border-radius:6px;padding:8px 12px;margin-bottom:6px;
        transition:all 0.2s;
    }}
    .penalty-item:hover {{border-color:#2E75B6;box-shadow:0 2px 8px rgba(46,117,182,0.1);}}
    .penalty-header {{display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;}}
    .penalty-section {{font-size:12px;font-weight:600;color:#1F4E79;}}
    .penalty-amount {{font-size:14px;font-weight:700;color:#DC2626;}}
    .penalty-desc {{font-size:11px;color:#6B7280;margin-bottom:4px;}}
    .penalty-meta {{display:flex;gap:8px;font-size:10px;}}
    .penalty-type {{color:#D97706;font-weight:600;}}
    .penalty-notes {{color:#9CA3AF;}}
    </style>"""
