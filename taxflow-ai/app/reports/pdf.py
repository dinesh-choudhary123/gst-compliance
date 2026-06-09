"""PDF report generation using ReportLab."""

from datetime import datetime
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_report(title: str, content_sections: list[dict], output_path: str) -> str:
    """Generate a PDF report with sections of tables and paragraphs.

    content_sections: list of {"type": "paragraph"/"table"/"heading", "data": ..., "headers": [...]}
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#2E75B6"),
        spaceBefore=15,
        spaceAfter=10,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )

    elements = []

    # Title
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}", body_style))
    elements.append(Spacer(1, 0.2 * inch))

    for section in content_sections:
        stype = section.get("type", "paragraph")

        if stype == "heading":
            elements.append(Paragraph(section["data"], heading_style))

        elif stype == "paragraph":
            elements.append(Paragraph(str(section["data"]), body_style))
            elements.append(Spacer(1, 0.1 * inch))

        elif stype == "table":
            headers = section.get("headers", [])
            data = section.get("data", [])
            if headers and data:
                table_data = [headers]
                for row in data:
                    table_data.append([str(val) for val in row])

                col_widths = [doc.width / len(headers)] * len(headers)
                table = Table(table_data, colWidths=col_widths, repeatRows=1)
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.15 * inch))

    doc.build(elements)
    return output_path


def generate_invoice_pdf(invoices: list[dict], output_path: str) -> str:
    """Generate invoice report as PDF."""
    sections = []

    # Summary
    total_amount = sum(i.get("total_amount", 0) for i in invoices)
    total_tax = sum(i.get("cgst_amount", 0) + i.get("sgst_amount", 0) + i.get("igst_amount", 0) for i in invoices)

    sections.append({
        "type": "paragraph",
        "data": f"Total Invoices: {len(invoices)} | Total Value: ₹{total_amount:,.2f} | Total Tax: ₹{total_tax:,.2f}",
    })

    sections.append({
        "type": "heading",
        "data": "Invoice Details",
    })

    headers = ["Invoice #", "Date", "Seller", "Taxable", "CGST", "SGST", "IGST", "Total"]
    data_rows = []
    for inv in invoices:
        data_rows.append([
            inv.get("invoice_number", ""),
            (inv.get("invoice_date", "") or "")[:10],
            (inv.get("seller_name", "") or "")[:20],
            f"₹{inv.get('taxable_amount', 0):,.2f}",
            f"₹{inv.get('cgst_amount', 0):,.2f}",
            f"₹{inv.get('sgst_amount', 0):,.2f}",
            f"₹{inv.get('igst_amount', 0):,.2f}",
            f"₹{inv.get('total_amount', 0):,.2f}",
        ])

    sections.append({
        "type": "table",
        "headers": headers,
        "data": data_rows,
    })

    return generate_pdf_report("Invoice Report - TaxFlow AI", sections, output_path)


def generate_gstr_pdf(gstr_data: dict, return_type: str, output_path: str) -> str:
    """Generate GSTR return as PDF."""
    sections = []

    summary = gstr_data.get("summary", gstr_data.get("table_3_turnover", {}))
    sections.append({
        "type": "paragraph",
        "data": f"Period: {gstr_data.get('period', 'N/A')} | GSTIN: {gstr_data.get('gstin', 'N/A')}",
    })

    if return_type == "gstr1":
        sections.append({"type": "heading", "data": "B2B Invoices"})
        b2b = gstr_data.get("b2b_invoices", [])
        if b2b:
            headers = ["Invoice", "Date", "Buyer GSTIN", "Taxable", "Tax", "Total"]
            data_rows = []
            for inv in b2b:
                data_rows.append([
                    inv.get("invoice_number", ""),
                    (inv.get("invoice_date", "") or "")[:10],
                    inv.get("buyer_gstin", ""),
                    f"₹{inv.get('taxable_amount', 0):,.2f}",
                    f"₹{inv.get('igst_amount', 0) + inv.get('cgst_amount', 0) + inv.get('sgst_amount', 0):,.2f}",
                    f"₹{inv.get('total_amount', 0):,.2f}",
                ])
            sections.append({"type": "table", "headers": headers, "data": data_rows})

        sections.append({"type": "heading", "data": "Rate-wise Summary"})
        rates = gstr_data.get("rate_wise_summary", {})
        if rates:
            headers = ["Rate", "Count", "Taxable Amount", "Tax"]
            data_rows = []
            for rate, details in rates.items():
                data_rows.append([
                    rate,
                    str(details.get("count", 0)),
                    f"₹{details.get('taxable_amount', 0):,.2f}",
                    f"₹{details.get('cgst', 0) + details.get('sgst', 0) + details.get('igst', 0):,.2f}",
                ])
            sections.append({"type": "table", "headers": headers, "data": data_rows})

    elif return_type == "gstr3b":
        sections.append({"type": "heading", "data": "Table 3 - Turnover"})
        turnover = gstr_data.get("table_3_turnover", {})
        if turnover:
            headers = ["Category", "Amount"]
            data_rows = [[k.replace("_", " ").title(), f"₹{v:,.2f}"] for k, v in turnover.items()]
            sections.append({"type": "table", "headers": headers, "data": data_rows})

        sections.append({"type": "heading", "data": "Table 4 - ITC"})
        itc = gstr_data.get("table_4_itc", {})
        if itc:
            headers = ["Category", "Amount"]
            data_rows = [[k.replace("_", " ").title(), f"₹{v:,.2f}"] for k, v in itc.items() if k != "itc_breakdown"]
            sections.append({"type": "table", "headers": headers, "data": data_rows})

        sections.append({"type": "heading", "data": "Table 5 - Tax Liability"})
        liability = gstr_data.get("table_5_tax_liability", {})
        if liability:
            headers = ["Category", "Amount"]
            data_rows = [[k.replace("_", " ").title(), f"₹{v:,.2f}"] for k, v in liability.items()]
            sections.append({"type": "table", "headers": headers, "data": data_rows})

    title = f"GSTR-{return_type[-1]} Return" if return_type in ("gstr1", "gstr3b") else "GSTR Return"
    return generate_pdf_report(f"{title} - TaxFlow AI", sections, output_path)
