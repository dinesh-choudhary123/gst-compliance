"""Excel report generation for invoices, reconciliations, and GSTR data."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def _style_header(ws, row: int, cols: int, title: str = ""):
    """Style a header row with colors and borders."""
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for col in range(1, cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = thin_border

    if title:
        ws.cell(row=row, column=1).value = title
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=cols)


def _style_data_cell(cell, is_amount: bool = False):
    """Style a data cell."""
    cell.font = Font(name="Calibri", size=10)
    cell.alignment = Alignment(horizontal="right" if is_amount else "left", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    cell.border = thin_border
    if is_amount:
        cell.number_format = '₹ #,##0.00'


def generate_invoice_report(invoices: list[dict], output_path: str) -> str:
    """Generate an Excel report of all invoices."""
    wb = openpyxl.Workbook()

    # Summary sheet
    ws_summary = wb.active
    ws_summary.title = "Summary"
    ws_summary.cell(row=1, column=1, value="INVOICE SUMMARY REPORT")
    ws_summary.cell(row=1, column=1).font = Font(name="Calibri", bold=True, size=16, color="1F4E79")
    ws_summary.merge_cells("A1:G1")

    ws_summary.cell(row=3, column=1, value=f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
    ws_summary.cell(row=4, column=1, value=f"Total Invoices: {len(invoices)}")
    ws_summary.cell(row=5, column=1, value=f"Total Taxable Amount: ₹{sum(i.get('taxable_amount', 0) for i in invoices):,.2f}")
    ws_summary.cell(row=6, column=1, value=f"Total Tax: ₹{sum(i.get('cgst_amount', 0) + i.get('sgst_amount', 0) + i.get('igst_amount', 0) for i in invoices):,.2f}")
    ws_summary.cell(row=7, column=1, value=f"Total Invoice Value: ₹{sum(i.get('total_amount', 0) for i in invoices):,.2f}")

    for row in range(3, 8):
        ws_summary.cell(row=row, column=1).font = Font(name="Calibri", size=11)

    # Invoice details sheet
    ws_invoices = wb.create_sheet("Invoices")
    headers = [
        "Invoice #", "Date", "Seller", "Seller GSTIN", "Buyer", "Buyer GSTIN",
        "Taxable Amount", "CGST", "SGST", "IGST", "Cess", "Total",
        "HSN Codes", "Place of Supply",
    ]

    for col, header in enumerate(headers, 1):
        ws_invoices.cell(row=1, column=col, value=header)
    _style_header(ws_invoices, 1, len(headers))

    for row_idx, inv in enumerate(invoices, 2):
        ws_invoices.cell(row=row_idx, column=1, value=inv.get("invoice_number", ""))
        ws_invoices.cell(row=row_idx, column=2, value=inv.get("invoice_date", "")[:10] if inv.get("invoice_date") else "")
        ws_invoices.cell(row=row_idx, column=3, value=inv.get("seller_name", ""))
        ws_invoices.cell(row=row_idx, column=4, value=inv.get("seller_gstin", ""))
        ws_invoices.cell(row=row_idx, column=5, value=inv.get("buyer_name", ""))
        ws_invoices.cell(row=row_idx, column=6, value=inv.get("buyer_gstin", ""))
        _style_data_cell(ws_invoices.cell(row=row_idx, column=7, value=inv.get("taxable_amount", 0)), True)
        _style_data_cell(ws_invoices.cell(row=row_idx, column=8, value=inv.get("cgst_amount", 0)), True)
        _style_data_cell(ws_invoices.cell(row=row_idx, column=9, value=inv.get("sgst_amount", 0)), True)
        _style_data_cell(ws_invoices.cell(row=row_idx, column=10, value=inv.get("igst_amount", 0)), True)
        _style_data_cell(ws_invoices.cell(row=row_idx, column=11, value=inv.get("cess_amount", 0)), True)
        _style_data_cell(ws_invoices.cell(row=row_idx, column=12, value=inv.get("total_amount", 0)), True)
        hsn_codes = inv.get("hsn_codes", [])
        hsn_str = ", ".join(f"{h.get('code', '')}" for h in hsn_codes) if isinstance(hsn_codes, list) else str(hsn_codes)
        ws_invoices.cell(row=row_idx, column=13, value=hsn_str)
        ws_invoices.cell(row=row_idx, column=14, value=inv.get("place_of_supply", ""))

        for col in range(1, len(headers) + 1):
            cell = ws_invoices.cell(row=row_idx, column=col)
            cell.font = Font(name="Calibri", size=10)
            cell.alignment = Alignment(vertical="center")
            thin_border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin"),
            )
            cell.border = thin_border

    # Auto-width columns
    for col in range(1, len(headers) + 1):
        ws_invoices.column_dimensions[get_column_letter(col)].width = 18

    wb.save(output_path)
    return output_path


def generate_gstr_report(gstr1_data: Optional[dict] = None, gstr3b_data: Optional[dict] = None, output_path: str = "") -> str:
    """Generate GSTR report in Excel format."""
    if not output_path:
        output_path = f"/tmp/gstr_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    wb = openpyxl.Workbook()

    if gstr1_data:
        ws = wb.active
        ws.title = "GSTR-1"
        _write_gstr1_sheet(ws, gstr1_data)

    if gstr3b_data:
        ws_gstr3b = wb.create_sheet("GSTR-3B")
        _write_gstr3b_sheet(ws_gstr3b, gstr3b_data)

    wb.save(output_path)
    return output_path


def _write_gstr1_sheet(ws, data: dict):
    """Write GSTR-1 data to a worksheet."""
    ws.cell(row=1, column=1, value="GSTR-1 RETURN DATA")
    ws.cell(row=1, column=1).font = Font(name="Calibri", bold=True, size=14, color="1F4E79")
    ws.merge_cells("A1:E1")

    ws.cell(row=3, column=1, value="Period")
    ws.cell(row=3, column=2, value=data.get("period", ""))
    ws.cell(row=4, column=1, value="GSTIN")
    ws.cell(row=4, column=2, value=data.get("gstin", ""))
    ws.cell(row=5, column=1, value="Legal Name")
    ws.cell(row=5, column=2, value=data.get("legal_name", ""))

    row = 7
    # B2B Invoices
    b2b = data.get("b2b_invoices", [])
    if b2b:
        ws.cell(row=row, column=1, value="B2B INVOICES").font = Font(bold=True, size=12)
        row += 1
        headers = ["Invoice #", "Date", "Buyer GSTIN", "Buyer Name", "Taxable", "CGST", "SGST", "IGST", "Total"]
        for col, h in enumerate(headers, 1):
            ws.cell(row=row, column=col, value=h)
        _style_header(ws, row, len(headers))
        row += 1
        for inv in b2b:
            ws.cell(row=row, column=1, value=inv.get("invoice_number", ""))
            ws.cell(row=row, column=2, value=inv.get("invoice_date", "")[:10])
            ws.cell(row=row, column=3, value=inv.get("buyer_gstin", ""))
            ws.cell(row=row, column=4, value=inv.get("buyer_name", ""))
            _style_data_cell(ws.cell(row=row, column=5, value=inv.get("taxable_amount", 0)), True)
            _style_data_cell(ws.cell(row=row, column=6, value=inv.get("cgst_amount", 0)), True)
            _style_data_cell(ws.cell(row=row, column=7, value=inv.get("sgst_amount", 0)), True)
            _style_data_cell(ws.cell(row=row, column=8, value=inv.get("igst_amount", 0)), True)
            _style_data_cell(ws.cell(row=row, column=9, value=inv.get("total_amount", 0)), True)
            row += 1

    # Summary
    summary = data.get("summary", {})
    if summary:
        row += 1
        ws.cell(row=row, column=1, value="SUMMARY").font = Font(bold=True, size=12)
        row += 1
        for key, val in summary.items():
            ws.cell(row=row, column=1, value=key.replace("_", " ").title())
            _style_data_cell(ws.cell(row=row, column=2, value=val), isinstance(val, (int, float)))
            row += 1


def _write_gstr3b_sheet(ws, data: dict):
    """Write GSTR-3B data to a worksheet."""
    ws.cell(row=1, column=1, value="GSTR-3B SUMMARY RETURN")
    ws.cell(row=1, column=1).font = Font(name="Calibri", bold=True, size=14, color="1F4E79")
    ws.merge_cells("A1:E1")

    ws.cell(row=3, column=1, value="Period")
    ws.cell(row=3, column=2, value=data.get("period", ""))
    ws.cell(row=4, column=1, value="GSTIN")
    ws.cell(row=4, column=2, value=data.get("gstin", ""))
    ws.cell(row=5, column=1, value="Legal Name")
    ws.cell(row=5, column=2, value=data.get("legal_name", ""))

    # Table 3: Turnover
    row = 7
    ws.cell(row=row, column=1, value="TABLE 3 - TURNOVER DETAILS").font = Font(bold=True, size=12)
    row += 1
    turnover = data.get("table_3_turnover", {})
    for key, val in turnover.items():
        ws.cell(row=row, column=1, value=key.replace("_", " ").title())
        _style_data_cell(ws.cell(row=row, column=2, value=val), True)
        row += 1

    # Table 4: ITC
    row += 1
    ws.cell(row=row, column=1, value="TABLE 4 - ITC DETAILS").font = Font(bold=True, size=12)
    row += 1
    itc = data.get("table_4_itc", {})
    for key, val in itc.items():
        if key != "itc_breakdown":
            ws.cell(row=row, column=1, value=key.replace("_", " ").title())
            _style_data_cell(ws.cell(row=row, column=2, value=val), isinstance(val, (int, float)))
            row += 1

    # ITC breakdown
    breakdown = itc.get("itc_breakdown", {})
    if breakdown:
        row += 1
        ws.cell(row=row, column=1, value="ITC Breakdown").font = Font(bold=True, size=10)
        row += 1
        for key, val in breakdown.items():
            ws.cell(row=row, column=1, value=key.upper())
            _style_data_cell(ws.cell(row=row, column=2, value=val), True)
            row += 1

    # Table 5: Tax Liability
    row += 1
    ws.cell(row=row, column=1, value="TABLE 5 - TAX LIABILITY").font = Font(bold=True, size=12)
    row += 1
    liability = data.get("table_5_tax_liability", {})
    for key, val in liability.items():
        ws.cell(row=row, column=1, value=key.replace("_", " ").title())
        _style_data_cell(ws.cell(row=row, column=2, value=val), isinstance(val, (int, float)))
        row += 1

    for col in range(1, 4):
        ws.column_dimensions[get_column_letter(col)].width = 25


def generate_reconciliation_report(matches: list[dict], unmatched_invoices: list[dict],
                                    unmatched_transactions: list[dict], output_path: str) -> str:
    """Generate reconciliation report."""
    wb = openpyxl.Workbook()

    # Matches sheet
    ws = wb.active
    ws.title = "Matched Items"
    headers = ["Invoice #", "Invoice Amount", "Transaction Date", "Transaction Amount",
               "Narration", "Confidence", "Notes"]
    for col, h in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=h)
    _style_header(ws, 1, len(headers))

    for row_idx, m in enumerate(matches, 2):
        ws.cell(row=row_idx, column=1, value=m.get("invoice_number", ""))
        _style_data_cell(ws.cell(row=row_idx, column=2, value=m.get("invoice_amount", 0)), True)
        ws.cell(row=row_idx, column=3, value=m.get("transaction_date", "")[:10])
        _style_data_cell(ws.cell(row=row_idx, column=4, value=m.get("transaction_amount", 0)), True)
        ws.cell(row=row_idx, column=5, value=m.get("narration", ""))
        ws.cell(row=row_idx, column=6, value=f"{m.get('confidence', 0) * 100:.0f}%")
        ws.cell(row=row_idx, column=7, value=m.get("notes", ""))

        for col in range(1, len(headers) + 1):
            ws.cell(row=row_idx, column=col).font = Font(name="Calibri", size=10)
            ws.cell(row=row_idx, column=col).border = Border(
                left=Side(style="thin"), right=Side(style="thin"),
                top=Side(style="thin"), bottom=Side(style="thin"),
            )

    # Unmatched sheet
    if unmatched_invoices:
        ws2 = wb.create_sheet("Unmatched Invoices")
        headers2 = ["Invoice #", "Date", "Amount", "Seller"]
        for col, h in enumerate(headers2, 1):
            ws2.cell(row=1, column=col, value=h)
        _style_header(ws2, 1, len(headers2))
        for row_idx, inv in enumerate(unmatched_invoices, 2):
            ws2.cell(row=row_idx, column=1, value=inv.get("invoice_number", ""))
            ws2.cell(row=row_idx, column=2, value=inv.get("invoice_date", "")[:10])
            _style_data_cell(ws2.cell(row=row_idx, column=3, value=inv.get("total_amount", 0)), True)
            ws2.cell(row=row_idx, column=4, value=inv.get("seller_name", ""))

    for col in range(1, 8):
        ws.column_dimensions[get_column_letter(col)].width = 20

    wb.save(output_path)
    return output_path
