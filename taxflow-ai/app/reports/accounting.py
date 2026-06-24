"""Accounting Reports - Balance Sheet, Cash Flow Statement, Trial Balance, and Ledger.

Generates comprehensive accounting reports from invoice and transaction data.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

from app.database import get_invoices, get_bank_transactions


def generate_balance_sheet(project_id: str) -> dict:
    """Generate a Balance Sheet from invoice and transaction data.

    Returns a structured dict with assets and liabilities sections.
    """
    invoices = get_invoices(project_id)
    transactions = get_bank_transactions(project_id)

    total_receivables = sum(i.get("total_amount", 0) for i in invoices)
    total_payables = sum(i.get("total_amount", 0) for i in invoices if i.get("seller_gstin"))
    
    total_credits = sum(t.get("credit", 0) for t in transactions)
    total_debits = sum(t.get("debit", 0) for t in transactions)
    net_cash = total_credits - total_debits

    # Calculate tax assets/liabilities
    total_tax = sum(
        i.get("cgst_amount", 0) + i.get("sgst_amount", 0) + i.get("igst_amount", 0) + i.get("cess_amount", 0)
        for i in invoices
    )
    total_taxable = sum(i.get("taxable_amount", 0) for i in invoices)

    balance_sheet = {
        "generated_at": datetime.now().isoformat(),
        "period": datetime.now().strftime("%B %Y"),
        "assets": {
            "current_assets": {
                "cash_and_bank": round(net_cash, 2),
                "accounts_receivable": round(total_receivables, 2),
                "input_tax_credit": round(total_tax, 2),
                "total_current_assets": round(net_cash + total_receivables + total_tax, 2),
            },
            "fixed_assets": {
                "equipment": 0.0,
                "furniture": 0.0,
                "total_fixed_assets": 0.0,
            },
            "total_assets": round(net_cash + total_receivables + total_tax, 2),
        },
        "liabilities": {
            "current_liabilities": {
                "accounts_payable": round(total_payables, 2),
                "gst_payable": round(total_tax, 2),
                "tds_payable": round(total_tax * 0.02, 2),
                "total_current_liabilities": round(total_payables + total_tax + total_tax * 0.02, 2),
            },
            "equity": {
                "retained_earnings": round(total_receivables - total_payables, 2),
                "total_equity": round(total_receivables - total_payables, 2),
            },
            "total_liabilities_and_equity": round(
                total_payables + total_tax + total_tax * 0.02 + (total_receivables - total_payables),
                2
            ),
        },
        "key_ratios": {
            "current_ratio": round((net_cash + total_receivables) / max(total_payables, 1), 2),
            "debt_to_equity": round(total_payables / max(total_receivables - total_payables, 1), 2),
            "net_working_capital": round((net_cash + total_receivables) - total_payables, 2),
        },
    }

    return balance_sheet


def generate_cash_flow_statement(project_id: str, months: int = 12) -> dict:
    """Generate a Cash Flow Statement from transactions.

    Categorizes transactions into operating, investing, and financing activities.
    """
    transactions = get_bank_transactions(project_id)
    invoices = get_invoices(project_id)

    # Separate into monthly buckets
    monthly_data = defaultdict(lambda: {
        "operating_inflows": 0.0, "operating_outflows": 0.0,
        "investing_inflows": 0.0, "investing_outflows": 0.0,
        "financing_inflows": 0.0, "financing_outflows": 0.0,
        "net_change": 0.0,
    })

    for tx in transactions:
        tx_date_str = tx.get("transaction_date", "")
        try:
            tx_date = datetime.fromisoformat(tx_date_str) if isinstance(tx_date_str, str) else tx_date_str
            month_key = tx_date.strftime("%Y-%m")
        except (ValueError, AttributeError):
            month_key = datetime.now().strftime("%Y-%m")

        amount = tx.get("credit", 0) - tx.get("debit", 0)
        narration = (tx.get("narration", "") or "").lower()

        # Simple categorization based on narration
        if amount > 0:
            if any(k in narration for k in ("loan", "capital", "equity")):
                monthly_data[month_key]["financing_inflows"] += amount
            elif any(k in narration for k in ("sale", "sale investment", "asset")):
                monthly_data[month_key]["investing_inflows"] += amount
            else:
                monthly_data[month_key]["operating_inflows"] += amount
        else:
            if any(k in narration for k in ("loan repayment", "dividend", "buyback")):
                monthly_data[month_key]["financing_outflows"] += abs(amount)
            elif any(k in narration for k in ("purchase equipment", "investment", "fixed asset")):
                monthly_data[month_key]["investing_outflows"] += abs(amount)
            else:
                monthly_data[month_key]["operating_outflows"] += abs(amount)

    # Sort months
    sorted_months = sorted(monthly_data.keys())[-months:]

    # Calculate totals
    total_operating = sum(
        monthly_data[m]["operating_inflows"] - monthly_data[m]["operating_outflows"]
        for m in sorted_months
    )
    total_investing = sum(
        monthly_data[m]["investing_inflows"] - monthly_data[m]["investing_outflows"]
        for m in sorted_months
    )
    total_financing = sum(
        monthly_data[m]["financing_inflows"] - monthly_data[m]["financing_outflows"]
        for m in sorted_months
    )

    return {
        "generated_at": datetime.now().isoformat(),
        "period": f"Last {months} months",
        "operating_activities": {
            "total_inflows": round(sum(monthly_data[m]["operating_inflows"] for m in sorted_months), 2),
            "total_outflows": round(sum(monthly_data[m]["operating_outflows"] for m in sorted_months), 2),
            "net_cash_from_operations": round(total_operating, 2),
        },
        "investing_activities": {
            "total_inflows": round(sum(monthly_data[m]["investing_inflows"] for m in sorted_months), 2),
            "total_outflows": round(sum(monthly_data[m]["investing_outflows"] for m in sorted_months), 2),
            "net_cash_from_investing": round(total_investing, 2),
        },
        "financing_activities": {
            "total_inflows": round(sum(monthly_data[m]["financing_inflows"] for m in sorted_months), 2),
            "total_outflows": round(sum(monthly_data[m]["financing_outflows"] for m in sorted_months), 2),
            "net_cash_from_financing": round(total_financing, 2),
        },
        "net_change_in_cash": round(total_operating + total_investing + total_financing, 2),
        "monthly_breakdown": {
            m: monthly_data[m] for m in sorted_months[-6:]
        },
    }


def generate_trial_balance(project_id: str) -> dict:
    """Generate a Trial Balance from invoice and transaction data."""
    invoices = get_invoices(project_id)
    transactions = get_bank_transactions(project_id)

    total_sales = sum(i.get("taxable_amount", 0) for i in invoices)
    total_tax_collected = sum(
        i.get("cgst_amount", 0) + i.get("sgst_amount", 0) + i.get("igst_amount", 0) + i.get("cess_amount", 0)
        for i in invoices
    )
    total_credits = sum(t.get("credit", 0) for t in transactions)
    total_debits = sum(t.get("debit", 0) for t in transactions)

    accounts = [
        {"account": "Sales Revenue", "debit": 0.0, "credit": round(total_sales, 2)},
        {"account": "CGST Collected", "debit": 0.0, "credit": round(sum(i.get("cgst_amount", 0) for i in invoices), 2)},
        {"account": "SGST Collected", "debit": 0.0, "credit": round(sum(i.get("sgst_amount", 0) for i in invoices), 2)},
        {"account": "IGST Collected", "debit": 0.0, "credit": round(sum(i.get("igst_amount", 0) for i in invoices), 2)},
        {"account": "Bank Account", "debit": round(net_cash := total_credits - total_debits, 2) if net_cash > 0 else 0.0, "credit": abs(net_cash) if net_cash < 0 else 0.0},
        {"account": "Accounts Receivable", "debit": round(sum(i.get("total_amount", 0) for i in invoices), 2), "credit": 0.0},
        {"account": "Input GST (ITC)", "debit": round(total_tax_collected, 2), "credit": 0.0},
        {"account": "Accounts Payable", "debit": 0.0, "credit": round(sum(i.get("total_amount", 0) for i in invoices if i.get("seller_gstin")), 2)},
    ]

    total_debit = sum(a["debit"] for a in accounts)
    total_credit = sum(a["credit"] for a in accounts)

    return {
        "generated_at": datetime.now().isoformat(),
        "accounts": accounts,
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "is_balanced": abs(total_debit - total_credit) < 1.0,
    }


def generate_ledger_summary(project_id: str) -> dict:
    """Generate a ledger summary showing account-wise balances."""
    invoices = get_invoices(project_id)
    transactions = get_bank_transactions(project_id)

    # Group invoices by seller (customer ledger)
    customer_ledger = defaultdict(lambda: {"invoices": 0, "total": 0.0, "paid": 0.0, "balance": 0.0})
    for inv in invoices:
        customer = inv.get("buyer_name", inv.get("seller_name", "Unknown"))
        customer_ledger[customer]["invoices"] += 1
        customer_ledger[customer]["total"] += inv.get("total_amount", 0)

    # Group transactions by narration pattern
    payment_ledger = defaultdict(lambda: {"count": 0, "total": 0.0})
    for tx in transactions:
        category = "Other"
        narration = (tx.get("narration", "") or "").lower()
        if any(k in narration for k in ("gst", "tax")):
            category = "GST Payment"
        elif any(k in narration for k in ("salary", "wage")):
            category = "Salary"
        elif any(k in narration for k in ("rent", "lease")):
            category = "Rent"
        elif any(k in narration for k in ("purchase", "vendor", "supplier")):
            category = "Purchase"
        elif any(k in narration for k in ("sale", "invoice", "receipt")):
            category = "Sales Receipt"
        elif any(k in narration for k in ("interest", "bank charge", "commission")):
            category = "Bank Charges"

        payment_ledger[category]["count"] += 1
        amount = tx.get("credit", 0) or tx.get("debit", 0)
        payment_ledger[category]["total"] += amount

    return {
        "generated_at": datetime.now().isoformat(),
        "customer_ledger": dict(customer_ledger),
        "payment_ledger": dict(payment_ledger),
        "total_customers": len(customer_ledger),
        "total_categories": len(payment_ledger),
    }


def format_balance_sheet_html(bs: dict) -> str:
    """Format balance sheet as styled HTML."""
    assets = bs["assets"]
    liabilities = bs["liabilities"]

    def _section_html(items: dict, label: str) -> str:
        rows = ""
        for k, v in items.items():
            if k.startswith("total_"):
                rows += f"""
                <tr style="border-top:2px solid #E2E8F0;font-weight:700;">
                    <td>{' '.join(k.replace('total_', '').split('_')).title()}</td>
                    <td style="text-align:right;">₹{v:,.2f}</td>
                </tr>"""
            else:
                rows += f"""
                <tr>
                    <td>{' '.join(k.split('_')).title()}</td>
                    <td style="text-align:right;">₹{v:,.2f}</td>
                </tr>"""
        return f"""
        <div style="margin-bottom:16px;">
            <h4 style="color:#1F4E79;margin:0 0 8px 0;font-size:13px;">{label}</h4>
            <table style="width:100%;border-collapse:collapse;font-size:12px;">
                {rows}
            </table>
        </div>"""

    ratios_html = ""
    for k, v in bs.get("key_ratios", {}).items():
        ratios_html += f'<span style="background:#F0F4F8;padding:4px 10px;border-radius:6px;font-size:11px;font-weight:500;">{" ".join(k.split("_")).title()}: {v}</span> '

    return f"""
    <div style="background:white;border-radius:12px;border:1px solid #E2E8F0;padding:20px;">
        <h3 style="margin:0 0 4px 0;color:#1F4E79;">📊 Balance Sheet</h3>
        <p style="font-size:12px;color:#6B7280;margin:0 0 16px 0;">As of {bs['period']}</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
            {_section_html(assets["current_assets"], "Current Assets")}
            {_section_html(liabilities["current_liabilities"], "Current Liabilities")}
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:8px;">
            {_section_html({"total_assets": assets["total_assets"]}, "Total Assets")}
            {_section_html(liabilities["equity"], "Equity")}
        </div>
        <div style="margin-top:16px;padding-top:12px;border-top:2px solid #E2E8F0;">
            <strong style="font-size:13px;">Key Ratios:</strong>
            <div style="display:flex;gap:8px;margin-top:6px;flex-wrap:wrap;">{ratios_html}</div>
        </div>
    </div>"""


def format_cash_flow_html(cf: dict) -> str:
    """Format cash flow statement as styled HTML."""
    def _flow_section(items: dict, title: str) -> str:
        net_key = [k for k in items.keys() if k.startswith("net_")][0]
        rows = ""
        for k, v in items.items():
            if k == net_key:
                prefix = "✅" if v >= 0 else "❌"
                rows += f"""
                <tr style="border-top:2px solid #E2E8F0;font-weight:700;">
                    <td>{prefix} {' '.join(k.replace('net_', '').split('_')).title()}</td>
                    <td style="text-align:right;">₹{v:,.2f}</td>
                </tr>"""
            else:
                rows += f"""
                <tr>
                    <td style="padding-left:12px;">{' '.join(k.split('_')).title()}</td>
                    <td style="text-align:right;">₹{v:,.2f}</td>
                </tr>"""
        return f"""
        <div style="margin-bottom:12px;">
            <h4 style="color:#1F4E79;margin:0 0 6px 0;font-size:13px;">{title}</h4>
            <table style="width:100%;border-collapse:collapse;font-size:12px;">{rows}</table>
        </div>"""

    return f"""
    <div style="background:white;border-radius:12px;border:1px solid #E2E8F0;padding:20px;">
        <h3 style="margin:0 0 4px 0;color:#1F4E79;">💰 Cash Flow Statement</h3>
        <p style="font-size:12px;color:#6B7280;margin:0 0 16px 0;">{cf['period']}</p>
        {_flow_section(cf["operating_activities"], "Operating Activities")}
        {_flow_section(cf["investing_activities"], "Investing Activities")}
        {_flow_section(cf["financing_activities"], "Financing Activities")}
        <div style="border-top:2px solid #1F4E79;padding-top:8px;margin-top:8px;">
            <strong>Net Change in Cash: ₹{cf['net_change_in_cash']:,.2f}</strong>
        </div>
    </div>"""


def format_trial_balance_html(tb: dict) -> str:
    """Format trial balance as styled HTML."""
    rows = ""
    for a in tb["accounts"]:
        rows += f"""
        <tr>
            <td>{a['account']}</td>
            <td style="text-align:right;">{'₹{:,.2f}'.format(a['debit']) if a['debit'] > 0 else ''}</td>
            <td style="text-align:right;">{'₹{:,.2f}'.format(a['credit']) if a['credit'] > 0 else ''}</td>
        </tr>"""

    status = "✅ Balanced" if tb["is_balanced"] else "❌ Not Balanced"
    status_color = "#059669" if tb["is_balanced"] else "#DC2626"

    return f"""
    <div style="background:white;border-radius:12px;border:1px solid #E2E8F0;padding:20px;">
        <h3 style="margin:0 0 4px 0;color:#1F4E79;">⚖️ Trial Balance</h3>
        <div style="display:flex;gap:16px;margin:8px 0 16px;">
            <span style="font-size:12px;color:{status_color};font-weight:600;">{status}</span>
            <span style="font-size:12px;color:#6B7280;">Dr: ₹{tb['total_debit']:,.2f}</span>
            <span style="font-size:12px;color:#6B7280;">Cr: ₹{tb['total_credit']:,.2f}</span>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
            <thead><tr style="background:#1F4E79;color:white;">
                <th style="padding:8px 12px;text-align:left;">Account</th>
                <th style="padding:8px 12px;text-align:right;">Debit (₹)</th>
                <th style="padding:8px 12px;text-align:right;">Credit (₹)</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>"""


def format_ledger_html(ls: dict) -> str:
    """Format ledger summary as styled HTML."""
    customer_rows = ""
    for customer, data in ls["customer_ledger"].items():
        customer_rows += f"""
        <tr>
            <td>{customer[:25]}</td>
            <td style="text-align:right;">{data['invoices']}</td>
            <td style="text-align:right;">₹{data['total']:,.2f}</td>
            <td style="text-align:right;">₹{data['balance']:,.2f}</td>
        </tr>"""

    payment_rows = ""
    for category, data in ls["payment_ledger"].items():
        payment_rows += f"""
        <tr>
            <td>{category}</td>
            <td style="text-align:right;">{data['count']}</td>
            <td style="text-align:right;">₹{data['total']:,.2f}</td>
        </tr>"""

    return f"""
    <div style="background:white;border-radius:12px;border:1px solid #E2E8F0;padding:20px;">
        <h3 style="margin:0 0 4px 0;color:#1F4E79;">📓 Ledger Summary</h3>
        <p style="font-size:12px;color:#6B7280;margin:0 0 12px 0;">{ls['total_customers']} customers · {ls['total_categories']} categories</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div>
                <h4 style="font-size:13px;color:#1F4E79;margin:0 0 8px 0;">🧑‍💼 Customer Ledger</h4>
                <table style="width:100%;border-collapse:collapse;font-size:11px;">
                    <thead><tr style="background:#1F4E79;color:white;">
                        <th style="padding:6px 8px;text-align:left;">Customer</th>
                        <th style="padding:6px 8px;text-align:right;">Invoices</th>
                        <th style="padding:6px 8px;text-align:right;">Total</th>
                        <th style="padding:6px 8px;text-align:right;">Balance</th>
                    </tr></thead>
                    <tbody>{customer_rows}</tbody>
                </table>
            </div>
            <div>
                <h4 style="font-size:13px;color:#1F4E79;margin:0 0 8px 0;">💳 Payment Ledger</h4>
                <table style="width:100%;border-collapse:collapse;font-size:11px;">
                    <thead><tr style="background:#1F4E79;color:white;">
                        <th style="padding:6px 8px;text-align:left;">Category</th>
                        <th style="padding:6px 8px;text-align:right;">Count</th>
                        <th style="padding:6px 8px;text-align:right;">Total</th>
                    </tr></thead>
                    <tbody>{payment_rows}</tbody>
                </table>
            </div>
        </div>
    </div>"""
