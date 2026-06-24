"""Tally and QuickBooks compatible export module.

Generates CSV and XML files in formats that can be directly
imported into Tally Prime, QuickBooks, and Zoho Books.
"""

import csv
import io
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom
from typing import Any, Optional

from app.database import get_invoices, get_bank_transactions


# ================================================================
# TALLY EXPORT
# ================================================================

def generate_tally_xml(project_id: str, output_path: Optional[str] = None) -> str:
    """Generate Tally Prime compatible XML voucher data.

    Creates XML in Tally's native format for importing:
    - Sales invoices
    - Payment receipts
    - Journal entries (GST adjustments)
    """
    invoices = get_invoices(project_id)
    transactions = get_bank_transactions(project_id)

    # Create the root envelope
    envelope = ET.Element("ENVELOPE")
    header = ET.SubElement(envelope, "HEADER")
    header_text = ET.SubElement(header, "TALLYREQUEST")
    header_text.text = "Import Data"
    body = ET.SubElement(envelope, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")
    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    report_name = ET.SubElement(request_desc, "REPORTNAME")
    report_name.text = "All Masters"
    request_data = ET.SubElement(import_data, "REQUESTDATA")

    # Tally Company Info
    tally_msg = ET.SubElement(request_data, "TALLYMESSAGE")
    company = ET.SubElement(tally_msg, "COMPANY")
    name_el = ET.SubElement(company, "NAME")
    name_el.text = "TaxFlow AI Client"
    mailing_name = ET.SubElement(company, "MAILINGNAME")
    mailing_name.text = "TaxFlow AI"

    # Sales Vouchers
    for inv in invoices:
        tally_msg = ET.SubElement(request_data, "TALLYMESSAGE")

        voucher = ET.SubElement(tally_msg, "VOUCHER")
        voucher.set("VCHTYPE", "Sales")
        voucher.set("ACTION", "Create")

        date_el = ET.SubElement(voucher, "DATE")
        inv_date = (inv.get("invoice_date", "") or "")[:10]
        date_el.text = inv_date if inv_date else datetime.now().strftime("%Y%m%d")

        ref_el = ET.SubElement(voucher, "REFERENCE")
        ref_el.text = inv.get("invoice_number", "")

        voucher_type = ET.SubElement(voucher, "VOUCHERTYPENAME")
        voucher_type.text = "Sales"

        party_name = ET.SubElement(voucher, "PARTYNAME")
        party_name.text = inv.get("buyer_name", inv.get("seller_name", "Customer"))

        # Ledger entries
        sale_amount = inv.get("taxable_amount", 0)
        cgst = inv.get("cgst_amount", 0)
        sgst = inv.get("sgst_amount", 0)
        igst = inv.get("igst_amount", 0)
        total = inv.get("total_amount", 0)

        # Sales ledger (Dr)
        all_ledgers = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")

        # Debit: Customer (total)
        ledger_dr = ET.SubElement(all_ledgers, "LEDGERENTRY")
        dr_name = ET.SubElement(ledger_dr, "LEDGERNAME")
        dr_name.text = inv.get("buyer_name", "Sundry Debtors")
        dr_amount = ET.SubElement(ledger_dr, "AMOUNT")
        dr_amount.text = f"-{total:.2f}"  # Negative = Debit in Tally

        # Credit: Sales
        ledger_cr1 = ET.SubElement(all_ledgers, "LEDGERENTRY")
        cr1_name = ET.SubElement(ledger_cr1, "LEDGERNAME")
        cr1_name.text = "Sales Account"
        cr1_amount = ET.SubElement(ledger_cr1, "AMOUNT")
        cr1_amount.text = f"{sale_amount:.2f}"

        # Credit: CGST
        if cgst > 0:
            ledger_cr2 = ET.SubElement(all_ledgers, "LEDGERENTRY")
            cr2_name = ET.SubElement(ledger_cr2, "LEDGERNAME")
            cr2_name.text = "CGST Output"
            cr2_amount = ET.SubElement(ledger_cr2, "AMOUNT")
            cr2_amount.text = f"{cgst:.2f}"

        # Credit: SGST
        if sgst > 0:
            ledger_cr3 = ET.SubElement(all_ledgers, "LEDGERENTRY")
            cr3_name = ET.SubElement(ledger_cr3, "LEDGERNAME")
            cr3_name.text = "SGST Output"
            cr3_amount = ET.SubElement(ledger_cr3, "AMOUNT")
            cr3_amount.text = f"{sgst:.2f}"

        # Credit: IGST
        if igst > 0:
            ledger_cr4 = ET.SubElement(all_ledgers, "LEDGERENTRY")
            cr4_name = ET.SubElement(ledger_cr4, "LEDGERNAME")
            cr4_name.text = "IGST Output"
            cr4_amount = ET.SubElement(ledger_cr4, "AMOUNT")
            cr4_amount.text = f"{igst:.2f}"

    # Payment entries from bank transactions
    for tx in transactions[:20]:  # Limit to 20 transactions
        tally_msg = ET.SubElement(request_data, "TALLYMESSAGE")

        voucher = ET.SubElement(tally_msg, "VOUCHER")
        voucher.set("VCHTYPE", "Payment")
        voucher.set("ACTION", "Create")

        date_el = ET.SubElement(voucher, "DATE")
        tx_date = (tx.get("transaction_date", "") or "")[:10]
        date_el.text = tx_date if tx_date else datetime.now().strftime("%Y%m%d")

        voucher_type = ET.SubElement(voucher, "VOUCHERTYPENAME")
        voucher_type.text = "Payment"

        all_ledgers = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")

        if tx.get("debit", 0) > 0:
            # Debit entry
            ledger_dr = ET.SubElement(all_ledgers, "LEDGERENTRY")
            dr_name = ET.SubElement(ledger_dr, "LEDGERNAME")
            dr_name.text = "Expenses"  # Simplified
            dr_amount = ET.SubElement(ledger_dr, "AMOUNT")
            dr_amount.text = f"-{tx['debit']:.2f}"

            # Credit to Bank
            ledger_cr = ET.SubElement(all_ledgers, "LEDGERENTRY")
            cr_name = ET.SubElement(ledger_cr, "LEDGERNAME")
            cr_name.text = "Bank Account"
            cr_amount = ET.SubElement(ledger_cr, "AMOUNT")
            cr_amount.text = f"{tx['debit']:.2f}"
        elif tx.get("credit", 0) > 0:
            # Receipt entry
            ledger_dr = ET.SubElement(all_ledgers, "LEDGERENTRY")
            dr_name = ET.SubElement(ledger_dr, "LEDGERNAME")
            dr_name.text = "Bank Account"
            dr_amount = ET.SubElement(ledger_dr, "AMOUNT")
            dr_amount.text = f"-{tx['credit']:.2f}"

            ledger_cr = ET.SubElement(all_ledgers, "LEDGERENTRY")
            cr_name = ET.SubElement(ledger_cr, "LEDGERNAME")
            cr_name.text = "Sales Account"
            cr_amount = ET.SubElement(ledger_cr, "AMOUNT")
            cr_amount.text = f"{tx['credit']:.2f}"

    # Format XML with proper indentation
    rough_string = ET.tostring(envelope, encoding="unicode")
    try:
        dom = minidom.parseString(rough_string.encode())
        xml_str = dom.toprettyxml(indent="  ")
    except Exception:
        xml_str = rough_string

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

    return xml_str


# ================================================================
# CSV EXPORTS (QuickBooks, Zoho Books compatible)
# ================================================================

def generate_qb_csv(project_id: str) -> str:
    """Generate QuickBooks compatible CSV for invoice import.

    Format matches QuickBooks Desktop IIF and QBO import.
    """
    invoices = get_invoices(project_id)
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["!TRNS", "TRNSID", "TRNSTYPE", "DATE", "ACCNT", "NAME",
                     "CLASS", "AMOUNT", "DOCNUM", "MEMO", "CLEAR"])
    writer.writerow(["!SPL", "SPLID", "TRNSTYPE", "DATE", "ACCNT", "NAME",
                     "CLASS", "AMOUNT", "DOCNUM", "MEMO", "CLEAR", "QNTY",
                     "PRICE", "INVITEM", "TAXABLE"])

    for i, inv in enumerate(invoices):
        total = inv.get("total_amount", 0)
        taxable = inv.get("taxable_amount", 0)
        inv_num = inv.get("invoice_number", f"INV-{i+1}")
        inv_date = (inv.get("invoice_date", "") or "")[:10]
        customer = inv.get("buyer_name", inv.get("seller_name", "Customer"))
        cgst = inv.get("cgst_amount", 0)
        sgst = inv.get("sgst_amount", 0)
        igst = inv.get("igst_amount", 0)
        total_tax = cgst + sgst + igst

        # TRNS line
        writer.writerow([
            "TRNS", "", "INVOICE", inv_date, "Accounts Receivable",
            customer, "", total, inv_num, "Imported from TaxFlow AI", "N"
        ])

        # SPL lines
        writer.writerow([
            "SPL", "", "INVOICE", inv_date, "Sales Account",
            customer, "", taxable, inv_num, "Taxable amount", "N",
            "", "", "", "N"
        ])
        writer.writerow([
            "SPL", "", "INVOICE", inv_date, "GST Payable",
            customer, "", total_tax, inv_num, f"GST @ {total_tax/max(taxable,1)*100:.1f}%", "N",
            "", "", "", "N"
        ])

        # End marker
        writer.writerow(["ENDTRNS", "", "", "", "", "", "", "", "", "", ""])

    return output.getvalue()


def generate_zoho_csv(project_id: str) -> str:
    """Generate Zoho Books compatible CSV for invoice import."""
    invoices = get_invoices(project_id)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Invoice Number", "Invoice Date", "Customer Name", "Customer GSTIN",
        "Item Name", "Item Description", "Quantity", "Rate", "HSN/SAC",
        "Taxable Amount", "CGST %", "CGST Amount", "SGST %", "SGST Amount",
        "IGST %", "IGST Amount", "Total Amount",
    ])

    for i, inv in enumerate(invoices):
        hsn_codes = inv.get("hsn_codes", [])
        if hsn_codes:
            for hsn in hsn_codes:
                writer.writerow([
                    inv.get("invoice_number", f"INV-{i+1}"),
                    (inv.get("invoice_date", "") or "")[:10],
                    inv.get("buyer_name", ""),
                    inv.get("buyer_gstin", ""),
                    hsn.get("description", "Item"),
                    hsn.get("description", ""),
                    hsn.get("quantity", 1),
                    hsn.get("rate", 0),
                    hsn.get("code", ""),
                    hsn.get("amount", 0),
                    inv.get("cgst_rate", 0),
                    inv.get("cgst_amount", 0),
                    inv.get("sgst_rate", 0),
                    inv.get("sgst_amount", 0),
                    inv.get("igst_rate", 0),
                    inv.get("igst_amount", 0),
                    inv.get("total_amount", 0),
                ])
        else:
            writer.writerow([
                inv.get("invoice_number", f"INV-{i+1}"),
                (inv.get("invoice_date", "") or "")[:10],
                inv.get("buyer_name", ""),
                inv.get("buyer_gstin", ""),
                "Services",
                inv.get("seller_name", ""),
                1,
                inv.get("taxable_amount", 0),
                "",
                inv.get("taxable_amount", 0),
                inv.get("cgst_rate", 0),
                inv.get("cgst_amount", 0),
                inv.get("sgst_rate", 0),
                inv.get("sgst_amount", 0),
                inv.get("igst_rate", 0),
                inv.get("igst_amount", 0),
                inv.get("total_amount", 0),
            ])

    return output.getvalue()


def generate_tally_csv(project_id: str) -> str:
    """Generate Tally compatible CSV for master data import."""
    invoices = get_invoices(project_id)
    output = io.StringIO()
    writer = csv.writer(output)

    # Ledger master
    writer.writerow(["$LEDGER"])
    writer.writerow(["NAME", "PARENT", "GSTIN", "ADDRESS", "STATE", "PINCODE"])

    seen_parties = set()
    for inv in invoices:
        buyer = inv.get("buyer_name", "")
        seller = inv.get("seller_name", "")
        buyer_gstin = inv.get("buyer_gstin", "")
        seller_gstin = inv.get("seller_gstin", "")

        if buyer and buyer not in seen_parties:
            writer.writerow([buyer, "Sundry Debtors", buyer_gstin, "", "", ""])
            seen_parties.add(buyer)
        if seller and seller not in seen_parties:
            writer.writerow([seller, "Sundry Creditors", seller_gstin, "", "", ""])
            seen_parties.add(seller)

    # Stock items
    writer.writerow([])
    writer.writerow(["$STOCKITEM"])
    writer.writerow(["NAME", "PARENT", "HSN", "GST RATE", "UNITS"])
    seen_hsn = set()

    for inv in invoices:
        for hsn in inv.get("hsn_codes", []):
            code = str(hsn.get("code", ""))
            desc = hsn.get("description", f"Item {code}")
            if code not in seen_hsn:
                writer.writerow([desc[:50], "Primary", code, "", "Nos"])
                seen_hsn.add(code)

    return output.getvalue()


def generate_unified_accounting_export(project_id: str, output_dir: str) -> dict:
    """Generate all accounting format exports at once."""
    import os
    from datetime import datetime
    from pathlib import Path

    out = Path(output_dir)
    os.makedirs(str(out), exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    results = {}

    # Tally XML
    xml_path = str(out / f"tally_export_{ts}.xml")
    generate_tally_xml(project_id, xml_path)
    results["tally_xml"] = xml_path

    # QuickBooks CSV
    qb_csv = generate_qb_csv(project_id)
    qb_path = str(out / f"quickbooks_export_{ts}.csv")
    with open(qb_path, "w", encoding="utf-8") as f:
        f.write(qb_csv)
    results["quickbooks_csv"] = qb_path

    # Zoho CSV
    zoho_csv = generate_zoho_csv(project_id)
    zoho_path = str(out / f"zoho_export_{ts}.csv")
    with open(zoho_path, "w", encoding="utf-8") as f:
        f.write(zoho_csv)
    results["zoho_csv"] = zoho_path

    # Tally CSV
    tally_csv = generate_tally_csv(project_id)
    tally_path = str(out / f"tally_masters_{ts}.csv")
    with open(tally_path, "w", encoding="utf-8") as f:
        f.write(tally_csv)
    results["tally_csv"] = tally_path

    return results
