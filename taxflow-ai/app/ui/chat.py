"""Gradio-based chat interface for TaxFlow AI.

This is the main user interface with:
- Modern chat interface with message history
- File upload area for documents
- Sidebar with client projects and stats
- Settings panel for model configuration
- Export buttons for reports
"""

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import gradio as gr

from app.auth import authenticate_user, register_user, logout_user, init_auth_db, validate_session
from app.config import settings
from app.database import (
    create_project,
    get_projects,
    get_project,
    delete_project,
    get_documents,
    get_invoices,
    get_bank_transactions,
    get_anomalies,
    get_gstr_data,
    clear_chat_history,
    add_document,
    init_main_db,
)
from app.agents.orchestrator import AgentOrchestrator
from app.agents.extractor import DocumentExtractor
from app.ollama_client import TaxFlowOllama
from app.reports.excel import generate_invoice_report, generate_gstr_report
from app.reports.pdf import generate_invoice_pdf, generate_gstr_pdf
from app.reports.json_report import export_comprehensive_json
from app.ui.styles import CUSTOM_CSS, THEME_TOGGLE_JS
from app.ui.dashboard import build_dashboard_html
from app.ui.gst_calendar import build_calendar_html, get_next_deadline
from app.ui.gst_tools import build_tax_calculator_html, build_hsn_lookup_html
from app.ui.activity import build_activity_feed_html, build_quick_stats_html
from app.ui.onboarding import build_onboarding_html, get_onboarding_stats
from app.activity_db import (
    init_activity_db,
    add_activity,
    get_activities,
    get_recent_activities_summary,
)
from app.reports.accounting import (
    generate_balance_sheet, generate_cash_flow_statement,
    generate_trial_balance, generate_ledger_summary,
    format_balance_sheet_html, format_cash_flow_html,
    format_trial_balance_html, format_ledger_html,
)
from app.reports.tally_export import (
    generate_tally_xml, generate_qb_csv, generate_zoho_csv,
    generate_unified_accounting_export,
)
from app.tds_tcs_calculator import TDSCalculator, format_tds_html, format_tcs_html
from app.penalty_calculator import PenaltyCalculator, format_penalty_html
from app.cash_flow_forecaster import CashFlowForecaster, format_forecast_html
from app.rag_knowledge_base import get_knowledge_base, get_rag_context, search_gst_rules
from app.processing_logs import (
    init_processing_logs_db, add_processing_log, get_processing_logs,
    build_logs_viewer_html, get_logs_summary,
)
try:
    from app.ocr_module import check_tesseract_available, ocr_pdf, enhanced_extraction, install_tesseract_instructions
    HAS_OCR = check_tesseract_available()
except ImportError:
    HAS_OCR = False
    def check_tesseract_available(): return False
    def ocr_pdf(*args, **kwargs): return "[OCR not available]"
    def enhanced_extraction(*args, **kwargs): return {"text": "", "method": "text", "ocr_used": False}
    def install_tesseract_instructions(): return "Install: pip install pytesseract pillow"

# ─── Global State ────────────────────────────────────────────────

_ollama_client: Optional[TaxFlowOllama] = None
_orchestrator: Optional[AgentOrchestrator] = None
_extractor: Optional[DocumentExtractor] = None

_CURRENT_USER_ID: Optional[str] = None
_CURRENT_PROJECT_ID: Optional[str] = None
_CURRENT_TOKEN: Optional[str] = None

_UPLOAD_DIR = settings.BASE_DIR / "uploads"
os.makedirs(_UPLOAD_DIR, exist_ok=True)


def init_ollama():
    """Initialize the Ollama client and orchestrator."""
    global _ollama_client, _orchestrator, _extractor
    try:
        client = TaxFlowOllama()
        available = client.is_available()
        if not available:
            return False, "Ollama not running. Please start Ollama and pull a model."

        _ollama_client = client
        _orchestrator = AgentOrchestrator(client)
        _extractor = DocumentExtractor(client)
        return True, f"✅ Connected to Ollama ({client.model})"
    except Exception as e:
        return False, f"❌ Could not connect to Ollama: {str(e)}"


# ─── Auth Handlers ───────────────────────────────────────────────

def handle_login(username: str, password: str):
    """Handle user login."""
    global _CURRENT_USER_ID, _CURRENT_TOKEN

    success, user_id, token = authenticate_user(username, password)
    if success:
        _CURRENT_USER_ID = user_id
        _CURRENT_TOKEN = token
        # Load projects into dropdown
        projects = get_projects(user_id)
        choices = [(p["name"], p["id"]) for p in projects]
        return (
            gr.update(visible=False),  # login panel
            gr.update(visible=True),   # main app
            f"Welcome, {username}!",
            gr.update(value=""),
            gr.update(value=""),
            gr.update(choices=choices),
        )
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        "Invalid credentials",
        gr.update(value=""),
        gr.update(value=""),
        gr.update(),
    )


def handle_register(username: str, password: str):
    """Handle user registration."""
    if not username or not password:
        return "Username and password required"
    if len(password) < 4:
        return "Password must be at least 4 characters"
    success, message = register_user(username, password)
    return message


def handle_logout():
    """Handle user logout."""
    global _CURRENT_USER_ID, _CURRENT_TOKEN, _CURRENT_PROJECT_ID
    if _CURRENT_TOKEN:
        logout_user(_CURRENT_TOKEN)
    _CURRENT_USER_ID = None
    _CURRENT_TOKEN = None
    _CURRENT_PROJECT_ID = None
    return (
        gr.update(visible=True),   # login panel
        gr.update(visible=False),  # main app
    )


# ─── Project Handlers ────────────────────────────────────────────

def handle_create_project(name: str, gstin: str = "", pan: str = "", notes: str = ""):
    """Create a new client project."""
    if not _CURRENT_USER_ID:
        return "Please login first", gr.update(choices=[])
    if not name:
        return "Project name required", gr.update(choices=[])

    try:
        project = create_project(name, _CURRENT_USER_ID, gstin, pan, "", notes)
        projects = get_projects(_CURRENT_USER_ID)
        choices = [(p["name"], p["id"]) for p in projects]
        return f"✅ Project '{name}' created!", gr.update(choices=choices, value=project["id"])
    except Exception as e:
        return f"❌ Error: {str(e)}", gr.update()


def handle_select_project(project_id: str):
    """Select a project and update the UI."""
    global _CURRENT_PROJECT_ID

    if not project_id:
        _CURRENT_PROJECT_ID = None
        return "No project selected", "", "", ""

    _CURRENT_PROJECT_ID = project_id

    if _orchestrator:
        _orchestrator.set_project(project_id)

    project = get_project(project_id)
    docs = get_documents(project_id)
    invoices = get_invoices(project_id)
    transactions = get_bank_transactions(project_id)
    anomalies = get_anomalies(project_id, unresolved_only=True)

    info = f"📁 **{project.get('name', 'N/A')}**"
    if project.get("gstin"):
        info += f"\nGSTIN: `{project['gstin']}`"

    stats = f"""
    **📄 Documents:** {len(docs)}
    | **🧾 Invoices:** {len(invoices)}
    | **🏦 Transactions:** {len(transactions)}
    | **⚠️ Anomalies:** {len(anomalies)}
    """

    # Build sidebar HTML
    sidebar_items = _build_sidebar_html(project_id)

    # Build dashboard
    dashboard_html = build_dashboard_html(project, invoices, transactions, anomalies, docs)

    # Track activity
    add_activity(project_id, "project", f"Opened project: {project.get('name', '')}", f"{len(docs)} docs, {len(invoices)} invoices")

    return info, stats, gr.update(value=sidebar_items), gr.update(value=dashboard_html)


def handle_delete_project(project_id: str):
    """Delete a project."""
    if not project_id:
        return "No project selected", gr.update(choices=[])

    try:
        delete_project(project_id)
        projects = get_projects(_CURRENT_USER_ID) if _CURRENT_USER_ID else []
        choices = [(p["name"], p["id"]) for p in projects]
        return f"🗑️ Project deleted", gr.update(choices=choices, value=None)
    except Exception as e:
        return f"❌ Error: {str(e)}", gr.update()


# ─── File Upload ─────────────────────────────────────────────────

def handle_file_upload(files):
    """Handle file uploads for a project."""
    if not _CURRENT_PROJECT_ID:
        return "Please select a project first", "", ""

    if not files:
        return "No files selected", "", ""

    results = []
    all_messages = []
    success_count = 0

    for file_info in files:
        filename = file_info.name if hasattr(file_info, 'name') else os.path.basename(file_info)
        file_path = Path(file_info if isinstance(file_info, str) else file_info.name)

        # Copy to project uploads
        project_upload_dir = _UPLOAD_DIR / _CURRENT_PROJECT_ID
        os.makedirs(project_upload_dir, exist_ok=True)
        dest_path = project_upload_dir / filename

        # Skip copy if source and destination are the same file
        if file_path.resolve() == dest_path.resolve():
            final_path = str(file_path)
        else:
            try:
                shutil.copy2(str(file_path), str(dest_path))
                final_path = str(dest_path)
            except (shutil.SameFileError, OSError, IOError) as e:
                results.append(f"❌ Could not process {filename}: {e}")
                continue

        # Determine document type
        name_lower = filename.lower()
        if any(k in name_lower for k in ("invoice", "inv", "bill")):
            doc_type = "invoice"
        elif any(k in name_lower for k in ("bank", "statement")):
            doc_type = "bank_statement"
        else:
            doc_type = "other"

        # Record in database
        file_size = os.path.getsize(final_path)
        doc = add_document(
            _CURRENT_PROJECT_ID,
            filename,
            final_path,
            doc_type=doc_type,
            file_size_bytes=file_size,
        )

        # Track activity
        add_activity(
            _CURRENT_PROJECT_ID, "upload",
            f"Uploaded {filename}",
            f"Document type: {doc_type}, Size: {file_size:,} bytes",
            {"filename": filename, "doc_type": doc_type, "size": file_size},
        )

        # Process with AI if available
        if _extractor and _orchestrator:
            try:
                result = _extractor.process_document(
                    _CURRENT_PROJECT_ID,
                    doc["id"],
                    final_path,
                    filename,
                    doc_type,
                )
                if result.get("success"):
                    results.append(f"✅ {result.get('message', 'Processed')}")
                    all_messages.append(result.get("message", ""))
                    success_count += 1
                    add_activity(
                        _CURRENT_PROJECT_ID, "extract",
                        f"Extracted data from {filename}",
                        result.get("message", "")[:200],
                        result,
                    )
                else:
                    results.append(f"⚠️ {result.get('message', 'Uploaded but processing incomplete')}")
            except Exception as e:
                results.append(f"📄 Uploaded: {filename}")
        else:
            results.append(f"📄 Uploaded: {filename}")

    summary = "\n".join(results)

    # Update sidebar
    docs = get_documents(_CURRENT_PROJECT_ID)
    sidebar_items = _build_sidebar_html(_CURRENT_PROJECT_ID)

    return summary, gr.update(value=sidebar_items), f"📄 {success_count}/{len(files)} file(s) processed"


def _build_sidebar_html(project_id: str) -> str:
    """Build the sidebar HTML for a project."""
    docs = get_documents(project_id)
    invoices = get_invoices(project_id)
    anomalies = get_anomalies(project_id, unresolved_only=True)
    transactions = get_bank_transactions(project_id)

    items = ""

    # Stats
    items += f"""
    <div class="sidebar-section" style="display:flex; gap:8px;">
        <div class="sidebar-stat"><div class="stat-value">{len(docs)}</div><div class="stat-label">Docs</div></div>
        <div class="sidebar-stat"><div class="stat-value">{len(invoices)}</div><div class="stat-label">Invoices</div></div>
        <div class="sidebar-stat"><div class="stat-value">{len(transactions)}</div><div class="stat-label">Txns</div></div>
        <div class="sidebar-stat"><div class="stat-value">{len(anomalies)}</div><div class="stat-label">Issues</div></div>
    </div>"""

    if docs:
        items += '<div class="sidebar-section"><div class="sidebar-title">📄 Documents</div>'
        for d in docs[:8]:
            icon = {"invoice": "🧾", "bank_statement": "🏦", "other": "📄"}
            items += f"""
            <div class="sidebar-item">
                <div class="item-label">{icon.get(d['doc_type'], '📄')} {d['filename'][:25]}</div>
                <div class="item-desc">{d['doc_type'].replace('_', ' ').title()}</div>
            </div>"""
        items += "</div>"

    if invoices:
        items += '<div class="sidebar-section"><div class="sidebar-title">🧾 Recent Invoices</div>'
        for inv in invoices[:5]:
            items += f"""
            <div class="sidebar-item">
                <div class="item-label">{inv.get('invoice_number', 'N/A')}</div>
                <div class="item-desc">₹{inv.get('total_amount', 0):,.2f}</div>
            </div>"""
        items += "</div>"

    if anomalies:
        items += '<div class="sidebar-section"><div class="sidebar-title">⚠️ Unresolved Issues</div>'
        sev_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        for a in anomalies[:5]:
            items += f"""
            <div class="sidebar-item">
                <div class="item-label">{sev_icons.get(a.get('severity', 'low'), '⚪')} {a['title'][:30]}</div>
                <div class="item-desc">{a.get('description', '')[:50]}</div>
            </div>"""
        items += "</div>"

    return items or '<div class="sidebar-section" style="color:#9CA3AF;text-align:center;padding:40px;">No data yet.<br>Upload documents to get started.</div>'


# ─── Chat Handlers ───────────────────────────────────────────────

def handle_chat(message: str, history: list):
    """Handle a chat message and generate AI response."""
    if not _CURRENT_PROJECT_ID:
        return history + [(message, "Please select or create a project first.")]

    if not _orchestrator:
        return history + [(message, "AI not initialized. Check Ollama connection in Settings.")]

    if not message.strip():
        return history

    try:
        result = _orchestrator.process_message(message, _CURRENT_PROJECT_ID)
        response = result.get("response", "I processed your request. What would you like to do next?")

        # Add actions as system messages
        actions = result.get("actions_taken", [])
        if actions:
            action_text = "\n".join(f"✓ {a}" for a in actions)
            response = f"{response}\n\n---\n**Actions Taken:**\n{action_text}"

        return history + [(message, response)]
    except Exception as e:
        return history + [(message, f"❌ Error processing your request: {str(e)}")]





# ─── Settings Handlers ───────────────────────────────────────────

def handle_settings_refresh():
    """Refresh and get current Ollama status."""
    if not _ollama_client:
        return "❌ Ollama not initialized"

    available = _ollama_client.is_available()
    models = _ollama_client.list_available_models()
    model_info = _ollama_client.get_model_info()

    status = "🟢 Connected" if available else "🔴 Disconnected"
    info = f"""
    **Status:** {status}
    **Model:** {_ollama_client.model}
    **Temperature:** {_ollama_client.temperature}
    **Available Models:** {', '.join(models[:5]) or 'None'}
    """

    return info


def handle_update_settings(model: str, temperature: float):
    """Update Ollama settings."""
    if not _ollama_client:
        return "Ollama not initialized"

    try:
        _ollama_client.update_settings(model, temperature)

        # Update global settings
        settings.OLLAMA_MODEL = model
        settings.OLLAMA_TEMPERATURE = temperature

        return f"✅ Updated: Model={model}, Temperature={temperature}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def handle_pull_model(model_name: str):
    """Pull a new model in Ollama."""
    if not _ollama_client:
        return "Ollama not initialized"

    result = _ollama_client.pull_model(model_name)
    if result.get("success"):
        return f"✅ Model '{model_name}' pulled successfully!"
    return f"❌ Failed to pull model: {result.get('message', 'Unknown error')}"


# ─── Export Handlers ─────────────────────────────────────────────

def handle_export_excel():
    """Export data to Excel."""
    if not _CURRENT_PROJECT_ID:
        return "No project selected", None

    try:
        invoices = get_invoices(_CURRENT_PROJECT_ID)
        gstr1_data = get_gstr_data(_CURRENT_PROJECT_ID, "gstr1")

        output_dir = settings.BASE_DIR / "exports"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate invoice report
        if invoices:
            inv_path = str(output_dir / f"invoices_{ts}.xlsx")
            generate_invoice_report(invoices, inv_path)

        # Generate GSTR report
        gstr_path = None
        if gstr1_data:
            gstr_path = str(output_dir / f"gstr_report_{ts}.xlsx")
            generate_gstr_report(gstr1_data=gstr1_data[-1]["data"] if gstr1_data else None, output_path=gstr_path)

        msg = f"✅ Reports generated in exports/"
        return msg, gr.update(visible=True)
    except Exception as e:
        return f"❌ Export error: {str(e)}", None


def handle_export_pdf():
    """Export data to PDF."""
    if not _CURRENT_PROJECT_ID:
        return "No project selected", None

    try:
        invoices = get_invoices(_CURRENT_PROJECT_ID)

        output_dir = settings.BASE_DIR / "exports"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        if invoices:
            pdf_path = str(output_dir / f"invoice_report_{ts}.pdf")
            generate_invoice_pdf(invoices, pdf_path)
            return f"✅ PDF report generated", gr.update(visible=True)

        return "No data to export", None
    except Exception as e:
        return f"❌ PDF export error: {str(e)}", None


def handle_export_json():
    """Export data to JSON."""
    if not _CURRENT_PROJECT_ID:
        return "No project selected", None

    try:
        invoices = get_invoices(_CURRENT_PROJECT_ID)
        transactions = get_bank_transactions(_CURRENT_PROJECT_ID)
        anomalies_list = get_anomalies(_CURRENT_PROJECT_ID)
        gstr1_data = get_gstr_data(_CURRENT_PROJECT_ID, "gstr1")
        gstr3b_data = get_gstr_data(_CURRENT_PROJECT_ID, "gstr3b")

        output_dir = settings.BASE_DIR / "exports"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = str(output_dir / f"comprehensive_{ts}.json")

        export_comprehensive_json(
            invoices, transactions, anomalies_list,
            gstr1_data[-1]["data"] if gstr1_data else None,
            gstr3b_data[-1]["data"] if gstr3b_data else None,
            json_path,
        )
        add_activity(_CURRENT_PROJECT_ID, "export", "Exported JSON report", f"Comprehensive report saved to {json_path}")
        return f"✅ JSON report generated", gr.update(visible=True)
    except Exception as e:
        return f"❌ JSON export error: {str(e)}", None


# ─── Dashboard Handler ──────────────────────────────────────────

def handle_refresh_dashboard():
    """Refresh the dashboard with updated charts."""
    if not _CURRENT_PROJECT_ID:
        return build_dashboard_html({}, [], [], [], [])

    project = get_project(_CURRENT_PROJECT_ID) or {}
    invoices = get_invoices(_CURRENT_PROJECT_ID)
    transactions = get_bank_transactions(_CURRENT_PROJECT_ID)
    anomalies = get_anomalies(_CURRENT_PROJECT_ID)
    documents = get_documents(_CURRENT_PROJECT_ID)
    gstr1_data = get_gstr_data(_CURRENT_PROJECT_ID, "gstr1")
    gstr3b_data = get_gstr_data(_CURRENT_PROJECT_ID, "gstr3b")

    gstr1 = gstr1_data[-1]["data"] if gstr1_data else None
    gstr3b = gstr3b_data[-1]["data"] if gstr3b_data else None

    return build_dashboard_html(project, invoices, transactions, anomalies, documents, gstr1, gstr3b)


# ─── Calendar Handler ───────────────────────────────────────────

def handle_refresh_calendar():
    """Refresh the GST compliance calendar."""
    return build_calendar_html()


# ─── Activity Handler ───────────────────────────────────────────

def handle_refresh_activity():
    """Refresh the activity feed."""
    if not _CURRENT_PROJECT_ID:
        return build_activity_feed_html([])

    activities = get_activities(_CURRENT_PROJECT_ID, limit=50)
    return build_activity_feed_html(activities)


def handle_clear_activity():
    """Clear activity feed."""
    if _CURRENT_PROJECT_ID:
        from app.activity_db import clear_activities
        clear_activities(_CURRENT_PROJECT_ID)
    return build_activity_feed_html([])


# ─── CSV Export Handlers ────────────────────────────────────────

def _generate_gstr_csv(invoices: list[dict], form_type: str) -> str:
    """Generate a GST portal-ready CSV string."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    if form_type == "gstr1":
        # GSTR-1 CSV format
        writer.writerow([
            "GSTIN", "Invoice Number", "Invoice Date", "Invoice Value",
            "Place of Supply", "Rate", "Taxable Value",
            "IGST", "CGST", "SGST", "Cess",
            "Buyer GSTIN", "Buyer Name", "HSN Code",
        ])
        for inv in invoices:
            seller_gstin = inv.get("seller_gstin", "")
            hsn_codes = inv.get("hsn_codes", [])
            hsn = hsn_codes[0].get("code", "") if hsn_codes else ""
            total_tax = inv.get("cgst_amount", 0) + inv.get("sgst_amount", 0) + inv.get("igst_amount", 0)
            taxable = inv.get("taxable_amount", 0)
            rate = round((total_tax / taxable) * 100, 2) if taxable > 0 else 0

            writer.writerow([
                seller_gstin,
                inv.get("invoice_number", ""),
                (inv.get("invoice_date", "") or "")[:10],
                inv.get("total_amount", 0),
                inv.get("place_of_supply", ""),
                rate,
                taxable,
                inv.get("igst_amount", 0),
                inv.get("cgst_amount", 0),
                inv.get("sgst_amount", 0),
                inv.get("cess_amount", 0),
                inv.get("buyer_gstin", ""),
                inv.get("buyer_name", ""),
                hsn,
            ])

    elif form_type == "gstr3b":
        # GSTR-3B CSV format
        writer.writerow([
            "GSTIN", "Period", "Taxable Value (3a)",
            "CGST Payable", "SGST Payable", "IGST Payable", "Cess Payable",
            "Eligible ITC (CGST)", "Eligible ITC (SGST)", "Eligible ITC (IGST)",
            "Net Tax Payable",
        ])
        total_cgst = sum(i.get("cgst_amount", 0) for i in invoices)
        total_sgst = sum(i.get("sgst_amount", 0) for i in invoices)
        total_igst = sum(i.get("igst_amount", 0) for i in invoices)
        total_cess = sum(i.get("cess_amount", 0) for i in invoices)
        taxable_value = sum(i.get("taxable_amount", 0) for i in invoices)
        net_payable = total_cgst + total_sgst + total_igst + total_cess

        seller_gstin = invoices[0].get("seller_gstin", "") if invoices else ""
        period = datetime.now().strftime("%m%Y")

        writer.writerow([
            seller_gstin,
            period,
            taxable_value,
            total_cgst,
            total_sgst,
            total_igst,
            total_cess,
            total_cgst,  # Eligible ITC
            total_sgst,
            total_igst,
            net_payable,
        ])

    return output.getvalue()


# ─── New Feature Handler Functions ────────────────────────────────

def handle_accounting_report(report_type: str):
    """Generate accounting reports."""
    if not _CURRENT_PROJECT_ID:
        return "<p style='color:#DC2626;'>No project selected.</p>"

    try:
        if report_type == "balance_sheet":
            bs = generate_balance_sheet(_CURRENT_PROJECT_ID)
            return format_balance_sheet_html(bs)
        elif report_type == "cash_flow":
            cf = generate_cash_flow_statement(_CURRENT_PROJECT_ID)
            return format_cash_flow_html(cf)
        elif report_type == "trial_balance":
            tb = generate_trial_balance(_CURRENT_PROJECT_ID)
            return format_trial_balance_html(tb)
        elif report_type == "ledger":
            ls = generate_ledger_summary(_CURRENT_PROJECT_ID)
            return format_ledger_html(ls)
        return "<p>Select a report type</p>"
    except Exception as e:
        return f"<p style='color:#DC2626;font-size:13px;'>❌ Error: {str(e)}</p>"


def handle_tds_calculation():
    """Calculate TDS/TCS."""
    if not _CURRENT_PROJECT_ID:
        return "<p style='color:#DC2626;'>No project selected.</p>", "<p>N/A</p>"
    try:
        calc = TDSCalculator(_CURRENT_PROJECT_ID)
        tds_data = calc.calculate_tds_it()
        tcs_data = calc.calculate_tcs_gst()
        return format_tds_html(tds_data), format_tcs_html(tcs_data)
    except Exception as e:
        return f"<p style='color:#DC2626;'>❌ {str(e)}</p>", ""


def handle_penalty_calculation():
    """Calculate penalties."""
    if not _CURRENT_PROJECT_ID:
        return "<p style='color:#DC2626;'>No project selected.</p>"
    try:
        calc = PenaltyCalculator(_CURRENT_PROJECT_ID)
        data = calc.calculate_all()
        return format_penalty_html(data)
    except Exception as e:
        return f"<p style='color:#DC2626;'>❌ {str(e)}</p>"


def handle_cash_flow_forecast(months: int = 6):
    """Generate cash flow forecast."""
    if not _CURRENT_PROJECT_ID:
        return "<p style='color:#DC2626;'>No project selected.</p>"
    try:
        forecaster = CashFlowForecaster(_CURRENT_PROJECT_ID)
        data = forecaster.forecast(months)
        return format_forecast_html(data)
    except Exception as e:
        return f"<p style='color:#DC2626;'>❌ {str(e)}</p>"


def handle_knowledge_base_search(query: str):
    """Search GST knowledge base."""
    if not query:
        return "<p style='color:#6B7280;'>Enter a search query (e.g., 'ITC eligibility', 'GSTR-1 due date')</p>"
    try:
        kb = get_knowledge_base()
        results = kb.search(query, top_k=8)
        if not results:
            return "<p style='color:#6B7280;'>No results found for your query. Try different keywords.</p>"
        html = '<div style="background:white;border-radius:8px;padding:8px;">'
        for r in results:
            html += f'''
            <div class="kg-card" style="margin-bottom:6px;">
                <div class="kg-card-header">
                    <span class="kg-section-label">{r.get("section", "")}</span>
                    <span class="kg-subcategory">{r.get("category", "")} > {r.get("subcategory", "")}</span>
                    <span style="margin-left:auto;font-size:10px;color:#059669;font-weight:600;">{r.get("score", 0)*100:.0f}% match</span>
                </div>
                <div class="kg-card-title">{r.get("title", "")}</div>
                <div class="kg-card-content">{r.get("content", "")[:300]}</div>
            </div>'''
        html += '</div>'
        return html
    except Exception as e:
        return f"<p style='color:#DC2626;'>❌ {str(e)}</p>"


def handle_onboarding_checklist():
    """Build onboarding checklist."""
    if not _CURRENT_PROJECT_ID:
        return "<p style='color:#DC2626;'>No project selected.</p>"
    try:
        from app.database import get_project
        project = get_project(_CURRENT_PROJECT_ID)
        return build_onboarding_html(_CURRENT_PROJECT_ID, project)
    except Exception as e:
        return f"<p style='color:#DC2626;'>❌ {str(e)}</p>"


def handle_processing_logs():
    """Build processing logs viewer."""
    if not _CURRENT_PROJECT_ID:
        return "<p style='color:#DC2626;'>No project selected.</p>"
    try:
        return build_logs_viewer_html(_CURRENT_PROJECT_ID)
    except Exception as e:
        return f"<p style='color:#DC2626;'>❌ {str(e)}</p>"


def handle_tally_export():
    """Export to Tally/QuickBooks formats."""
    if not _CURRENT_PROJECT_ID:
        return "<p style='color:#DC2626;'>No project selected.</p>"
    try:
        from app.config import settings
        output_dir = settings.BASE_DIR / "exports"
        os.makedirs(str(output_dir), exist_ok=True)
        results = generate_unified_accounting_export(_CURRENT_PROJECT_ID, str(output_dir))
        msg = "✅ Tally/QuickBooks exports generated:<br>"
        for fmt, path in results.items():
            msg += f"• {fmt.replace('_', ' ').title()}: {path.rsplit('/', 1)[-1]}<br>"
        add_activity(_CURRENT_PROJECT_ID, "export", "Exported accounting data", f"Tally/QuickBooks exports generated")
        return msg
    except Exception as e:
        return f"<p style='color:#DC2626;'>❌ {str(e)}</p>"


def handle_ocr_status():
    """Check OCR availability and return info."""
    available = check_tesseract_available()
    if available:
        return "<p style='color:#059669;'>✅ Tesseract OCR is installed and available.</p>"
    instructions = install_tesseract_instructions()
    return f'<div style="background:#FEF3C7;border:1px solid #F59E0B;border-radius:8px;padding:12px;font-size:12px;"><strong>⚠️ Tesseract OCR not detected</strong><pre style="background:#1a2332;color:#E2E8F0;padding:12px;border-radius:6px;overflow-x:auto;font-size:11px;margin:8px 0;">{instructions[:200]}</pre></div>'


def handle_ocr_scan():
    """Placeholder for OCR scanning (would need file input)."""
    if not check_tesseract_available():
        return handle_ocr_status()
    return "<p style='color:#6B7280;'>Upload a scanned PDF or image in the Upload tab, then click Process. OCR will be automatically used for scanned documents.</p>"


def handle_export_gstr1_csv():
    """Export GSTR-1 CSV file for GST portal upload."""
    if not _CURRENT_PROJECT_ID:
        return "No project selected", None

    try:
        invoices = get_invoices(_CURRENT_PROJECT_ID)
        if not invoices:
            return "No invoices to export", None

        csv_content = _generate_gstr_csv(invoices, "gstr1")

        output_dir = settings.BASE_DIR / "exports"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = str(output_dir / f"gstr1_portal_{ts}.csv")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(csv_content)

        add_activity(_CURRENT_PROJECT_ID, "export", "Exported GSTR-1 CSV", f"GST portal CSV saved to exports/")
        return f"✅ GSTR-1 CSV saved to: {file_path}", gr.update(visible=True)
    except Exception as e:
        return f"❌ CSV export error: {str(e)}", None


def handle_export_gstr3b_csv():
    """Export GSTR-3B CSV file for GST portal upload."""
    if not _CURRENT_PROJECT_ID:
        return "No project selected", None

    try:
        invoices = get_invoices(_CURRENT_PROJECT_ID)
        if not invoices:
            return "No invoices to export", None

        csv_content = _generate_gstr_csv(invoices, "gstr3b")

        output_dir = settings.BASE_DIR / "exports"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = str(output_dir / f"gstr3b_portal_{ts}.csv")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(csv_content)

        add_activity(_CURRENT_PROJECT_ID, "export", "Exported GSTR-3B CSV", f"GST portal CSV saved to exports/")
        return f"✅ GSTR-3B CSV saved to: {file_path}", gr.update(visible=True)
    except Exception as e:
        return f"❌ CSV export error: {str(e)}", None


# ─── Utility Handlers ─────────────────────────────────────────────

def handle_clear_chat():
    """Clear chat history for current project and return empty list for chatbot."""
    if _CURRENT_PROJECT_ID:
        clear_chat_history(_CURRENT_PROJECT_ID)
    return []


def handle_refresh_sidebar():
    """Refresh the sidebar content."""
    if not _CURRENT_PROJECT_ID:
        return "", "", gr.update()
    project = get_project(_CURRENT_PROJECT_ID)

    info = f"📁 **{project.get('name', 'N/A')}**"
    if project.get("gstin"):
        info += f"\nGSTIN: `{project['gstin']}`"

    docs = get_documents(_CURRENT_PROJECT_ID)
    invoices = get_invoices(_CURRENT_PROJECT_ID)
    transactions = get_bank_transactions(_CURRENT_PROJECT_ID)
    anomalies = get_anomalies(_CURRENT_PROJECT_ID, unresolved_only=True)

    stats = f"**📄 {len(docs)}** | **🧾 {len(invoices)}** | **🏦 {len(transactions)}** | **⚠️ {len(anomalies)}**"

    sidebar_html = _build_sidebar_html(_CURRENT_PROJECT_ID)
    return info, stats, gr.update(value=sidebar_html)


# ─── Build Gradio UI ─────────────────────────────────────────────

def build_app():
    """Build and return the Gradio application."""
    init_auth_db()
    init_main_db()
    init_activity_db()
    init_processing_logs_db()
    ollama_status, ollama_msg = init_ollama()

    # Inject theme toggle JS directly into page head (avoids Gradio sanitization)
    theme_script = f"<script>{THEME_TOGGLE_JS}</script>"

    with gr.Blocks(
        title="TaxFlow AI",
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(
            primary_hue="blue",
            neutral_hue="slate",
            font="Inter",
        ),
        head=theme_script,
    ) as app:

        # ─── Login Panel ────────────────────────────────────────
        with gr.Column(visible=True, elem_classes="login-container") as login_panel:
            with gr.Column(elem_classes="login-card-wrapper"):
                gr.HTML("""
                    <div style="text-align:center;margin-bottom:24px;">
                        <div class="login-icon">🧾</div>
                        <h1 class="login-title">TaxFlow AI</h1>
                        <p class="login-subtitle">GST Compliance & Tax Automation</p>
                    </div>
                """)

                with gr.Tab("Log In"):
                    login_username = gr.Textbox(label="Username", placeholder="Enter your username")
                    login_password = gr.Textbox(label="Password", placeholder="Enter your password", type="password")
                    login_btn = gr.Button("Sign In", variant="primary", size="lg")
                    login_msg = gr.Markdown("")

                with gr.Tab("Register"):
                    reg_username = gr.Textbox(label="Username", placeholder="Choose a username")
                    reg_password = gr.Textbox(label="Password", placeholder="Choose a password (min 4 chars)", type="password")
                    reg_btn = gr.Button("Create Account", variant="secondary")
                    reg_msg = gr.Markdown("")

                gr.HTML("""
                    <div class="login-security-badge">
                        🔒 Everything runs locally. Your data never leaves your machine.
                    </div>
                """)

        # ─── Main Application ───────────────────────────────────
        with gr.Column(visible=False) as main_app:
            # Header
            gr.HTML(f"""
            <div class="header-container">
                <div style="display:flex; align-items:center; gap:12px;">
                    <span class="header-title-icon">🧾</span>
                    <div>
                        <div class="header-title">TaxFlow AI</div>
                        <div class="header-subtitle">Local AI for GST Compliance & Tax Automation</div>
                    </div>
                </div>
                <div class="header-status">
                    <span class="status-dot {'online' if ollama_status else 'offline'}"></span>
                    <span class="status-text">{'AI Ready' if ollama_status else 'Ollama Offline'}</span>
                    <button onclick="toggleTheme()" class="theme-toggle-btn" id="theme-toggle-btn">☀️ Light ▼</button>
                </div>
            </div>
            """)

            with gr.Row(equal_height=False):
                # ─── Sidebar ────────────────────────────────────
                with gr.Column(scale=1, min_width=280, elem_classes="sidebar-container"):
                    gr.HTML("""
                    <div class="sidebar-header-bg">
                        <div style="color:white;font-weight:700;font-size:16px;position:relative;z-index:1;">📁 Projects</div>
                    </div>
                    """)

                    project_dropdown = gr.Dropdown(
                        label="Select Project",
                        choices=[],
                        interactive=True,
                        scale=1,
                    )

                    with gr.Row():
                        create_project_btn = gr.Button("➕ New", size="sm", elem_id="btn-new-project")
                        delete_project_btn = gr.Button("🗑️", size="sm", elem_id="btn-delete-project")

                    with gr.Accordion("Create Project", open=False) as new_project_accordion:
                        new_project_name = gr.Textbox(label="Project Name", placeholder="Client name")
                        new_project_gstin = gr.Textbox(label="GSTIN (optional)", placeholder="15-digit GSTIN")
                        new_project_notes = gr.Textbox(label="Notes", placeholder="Any notes...", lines=2)
                        create_confirm_btn = gr.Button("Create Project", variant="primary", size="sm")

                    project_info = gr.Markdown("Select a project to begin")
                    project_stats = gr.Markdown("")

                    gr.HTML("""
                    <div class="sidebar-section-title">Project Data</div>
                    """)

                    sidebar_content = gr.HTML(
                        value='<div class="sidebar-section" style="color:#9CA3AF;text-align:center;padding:40px;">Select a project to view data</div>',
                    )

                    with gr.Row(elem_classes="action-btn-group"):
                        refresh_btn = gr.Button("🔄 Refresh", size="sm", elem_id="btn-refresh")
                        logout_btn = gr.Button("🚪 Logout", size="sm", elem_id="btn-logout")

                # ─── Main Content ────────────────────────────────
                with gr.Column(scale=3):
                    with gr.Tabs(elem_classes="tabs") as tabs:
                        # ─── Chat Tab ────────────────────────────
                        with gr.TabItem("💬 Chat", id=0):
                            with gr.Column(elem_classes="chat-container"):
                                chatbot = gr.Chatbot(
                                    label="TaxFlow AI Assistant",
                                    height=500,
                                    bubble_full_width=False,
                                    avatar_images=(None, "🧾"),
                                    show_copy_button=True,
                                )

                                with gr.Row():
                                    msg_input = gr.Textbox(
                                        label="",
                                        placeholder="Ask about invoices, request reconciliation, check ITC...",
                                        scale=10,
                                        container=False,
                                        elem_classes="chat-input",
                                    )
                                    send_btn = gr.Button("➤", variant="primary", scale=1, elem_classes="send-btn")

                                with gr.Row():
                                    clear_chat_btn = gr.Button("🗑️ Clear Chat", size="sm", elem_classes="gr-button-secondary")
                                    gr.Markdown(
                                        "💡 *Try: 'Analyze my documents', 'Reconcile bank statement', 'Check ITC matching', 'Generate GSTR-1'*",
                                    )

                        # ─── Upload Tab ──────────────────────────
                        with gr.TabItem("📤 Upload", id=1):
                            with gr.Column():
                                gr.Markdown("### Upload Documents")
                                gr.Markdown("Upload invoices (PDF/Excel), bank statements (CSV/PDF), or any GST documents.")
                                file_input = gr.File(
                                    label="Drag & Drop Files Here",
                                    file_count="multiple",
                                    file_types=[".pdf", ".csv", ".xlsx", ".xls", ".json", ".xml", ".txt", ".jpg", ".png"],
                                    elem_classes="file-upload",
                                )
                                upload_msg = gr.Markdown("")
                                with gr.Row():
                                    upload_btn = gr.Button("📤 Process Files", variant="primary", size="lg")
                                    upload_status = gr.Markdown("")

                        # ─── Reports Tab ──────────────────────────
                        with gr.TabItem("📊 Reports", id=2):
                            with gr.Column():
                                gr.Markdown("### Generate Reports")
                                gr.Markdown("Export processed data in Excel, PDF, or JSON format.")

                                with gr.Row():
                                    export_excel_btn = gr.Button("📊 Export Excel", variant="primary", size="lg")
                                    export_pdf_btn = gr.Button("📄 Export PDF", variant="primary", size="lg")
                                    export_json_btn = gr.Button("📋 Export JSON", variant="primary", size="lg")

                                export_msg = gr.Markdown("")
                                export_status = gr.HTML(visible=False)

                                gr.Markdown("---")
                                gr.Markdown("### Quick Actions")

                                with gr.Row():
                                    clear_chat_btn2 = gr.Button("🗑️ Clear Chat History", size="sm", elem_classes="gr-button-secondary")
                                    refresh_data_btn = gr.Button("🔄 Refresh Data", size="sm", elem_classes="gr-button-secondary")

                                # ─── Dashboard Tab ──────────────────────────
                        with gr.TabItem("📊 Dashboard", id=3):
                            dashboard_content = gr.HTML(
                                value='<div class="loading-dots"><div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div></div>',
                                elem_classes="dashboard-container",
                            )
                            with gr.Row():
                                refresh_dashboard_btn = gr.Button("🔄 Refresh Dashboard", variant="primary", elem_classes="gr-button-secondary")

                        # ─── Calendar Tab ───────────────────────────
                        with gr.TabItem("📅 Calendar", id=4):
                            calendar_content = gr.HTML(
                                value='<div class="loading-dots"><div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div></div>',
                            )

                        # ─── Tools Tab ─────────────────────────────
                        with gr.TabItem("🔧 Tools", id=5):
                            with gr.Tabs():
                                with gr.TabItem("🧮 Tax Calculator"):
                                    calculator_content = gr.HTML(build_tax_calculator_html())
                                with gr.TabItem("🔍 HSN/SAC Lookup"):
                                    hsn_content = gr.HTML(build_hsn_lookup_html())
                                with gr.TabItem("📊 GST Portal CSV"):
                                    gr.Markdown("### Export GST Portal-Ready CSV")
                                    gr.Markdown("Download CSV files formatted for direct upload to the GST portal.")
                                    with gr.Row():
                                        export_gstr1_csv_btn = gr.Button("📥 Download GSTR-1 CSV", variant="primary", size="lg")
                                        export_gstr3b_csv_btn = gr.Button("📥 Download GSTR-3B CSV", variant="primary", size="lg")
                                    export_csv_msg = gr.Markdown("")

                        # ─── Activity Tab ────────────────────────────
                        with gr.TabItem("📋 Activity", id=6):
                            activity_content = gr.HTML(
                                value='<div class="loading-dots"><div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div></div>',
                            )
                            with gr.Row():
                                refresh_activity_btn = gr.Button("🔄 Refresh Activity", size="sm", elem_classes="gr-button-secondary")
                                clear_activity_btn = gr.Button("🗑️ Clear", size="sm", elem_classes="gr-button-secondary")

                        # ─── Accounting Tab ─────────────────────────
                        with gr.TabItem("📈 Accounting", id=7):
                            with gr.Tabs():
                                with gr.TabItem("📊 Balance Sheet"):
                                    bs_content = gr.HTML('<p style="color:#6B7280;text-align:center;padding:40px;">Select a project and click Generate</p>')
                                    bs_btn = gr.Button("📊 Generate Balance Sheet", variant="primary", elem_classes="gr-button-secondary")
                                with gr.TabItem("💰 Cash Flow"):
                                    cf_content = gr.HTML('<p style="color:#6B7280;text-align:center;padding:40px;">Select a project and click Generate</p>')
                                    cf_btn = gr.Button("💰 Generate Cash Flow Statement", variant="primary", elem_classes="gr-button-secondary")
                                with gr.TabItem("⚖️ Trial Balance"):
                                    tb_content = gr.HTML('<p style="color:#6B7280;text-align:center;padding:40px;">Select a project and click Generate</p>')
                                    tb_btn = gr.Button("⚖️ Generate Trial Balance", variant="primary", elem_classes="gr-button-secondary")
                                with gr.TabItem("📓 Ledger Summary"):
                                    ls_content = gr.HTML('<p style="color:#6B7280;text-align:center;padding:40px;">Select a project and click Generate</p>')
                                    ls_btn = gr.Button("📓 Generate Ledger", variant="primary", elem_classes="gr-button-secondary")

                        # ─── TDS/TCS Tab ────────────────────────────
                        with gr.TabItem("💰 TDS/TCS", id=8):
                            tds_content = gr.HTML('<p style="color:#6B7280;text-align:center;padding:40px;">Select a project and click Calculate</p>')
                            with gr.Row():
                                tds_calc_btn = gr.Button("🧮 Calculate TDS/TCS", variant="primary")
                            tcs_content = gr.HTML('')

                        # ─── Penalty Calculator Tab ─────────────────
                        with gr.TabItem("⚠️ Penalty", id=9):
                            penalty_content = gr.HTML('<p style="color:#6B7280;text-align:center;padding:40px;">Select a project and click Assess</p>')
                            with gr.Row():
                                penalty_calc_btn = gr.Button("⚠️ Assess Penalty Risk", variant="primary")

                        # ─── Cash Flow Forecast Tab ─────────────────
                        with gr.TabItem("🔮 Forecast", id=10):
                            forecast_content = gr.HTML('<p style="color:#6B7280;text-align:center;padding:40px;">Select a project and click Forecast</p>')
                            with gr.Row():
                                forecast_3mo_btn = gr.Button("3 Month Forecast", variant="primary", elem_classes="gr-button-secondary")
                                forecast_6mo_btn = gr.Button("6 Month Forecast", variant="primary", elem_classes="gr-button-secondary")

                        # ─── Knowledge Base Tab ─────────────────────
                        with gr.TabItem("📚 Knowledge", id=11):
                            with gr.Column():
                                gr.Markdown("### GST Rule Knowledge Base")
                                gr.Markdown("Search 60+ GST rules, sections, and provisions")
                                kb_query = gr.Textbox(label="Search", placeholder="e.g., ITC eligibility, GSTR-1 due date, Section 16")
                                kb_btn = gr.Button("🔍 Search Knowledge Base", variant="primary")
                                kb_results = gr.HTML('<p style="color:#6B7280;text-align:center;padding:20px;">Enter a query above to search GST rules</p>')

                        # ─── Onboarding Tab ─────────────────────────
                        with gr.TabItem("📋 Onboarding", id=12):
                            onboarding_content = gr.HTML('<p style="color:#6B7280;text-align:center;padding:40px;">Select a project to view onboarding checklist</p>')
                            with gr.Row():
                                onboarding_btn = gr.Button("📋 Show Onboarding Checklist", variant="primary")

                        # ─── Processing Logs Tab ────────────────────
                        with gr.TabItem("📜 Logs", id=13):
                            logs_content = gr.HTML('<p style="color:#6B7280;text-align:center;padding:40px;">Select a project to view processing logs</p>')
                            with gr.Row():
                                logs_btn = gr.Button("📜 View Processing Logs", variant="primary")

                        # ─── Tally Export Tab ───────────────────────
                        with gr.TabItem("📦 Tally", id=14):
                            gr.Markdown("### Export to Accounting Software")
                            gr.Markdown("Generate Tally Prime, QuickBooks, and Zoho Books compatible exports")
                            tally_content = gr.HTML('<p style="color:#6B7280;text-align:center;padding:20px;">Select a project and export</p>')
                            with gr.Row():
                                tally_export_btn = gr.Button("📦 Generate All Formats", variant="primary")

                        # ─── Settings Tab ─────────────────────────
                        with gr.TabItem("⚙️ Settings", id=7):
                            with gr.Column():
                                gr.Markdown("### Ollama Settings")

                                settings_status = gr.Markdown(f"**Current Status:** {ollama_msg}")

                                with gr.Row():
                                    settings_model = gr.Textbox(
                                        label="Model Name",
                                        value=settings.OLLAMA_MODEL,
                                        placeholder="e.g., llama3.1:8b, qwen2.5:14b",
                                        scale=2,
                                    )
                                    settings_temp = gr.Slider(
                                        label="Temperature",
                                        minimum=0.0,
                                        maximum=1.0,
                                        value=settings.OLLAMA_TEMPERATURE,
                                        step=0.05,
                                        scale=1,
                                    )

                                with gr.Row():
                                    save_settings_btn = gr.Button("💾 Save Settings", variant="primary", size="lg")
                                    refresh_settings_btn = gr.Button("🔄 Refresh", size="lg", elem_classes="gr-button-secondary")

                                settings_msg = gr.Markdown("")

                                gr.Markdown("---")
                                gr.Markdown("### Model Management")
                                pull_model_name = gr.Textbox(
                                    label="Pull New Model",
                                    placeholder="e.g., llama3.1:8b, qwen2.5:14b, mistral",
                                )
                                pull_model_btn = gr.Button("📥 Pull Model", variant="primary")
                                pull_status = gr.Markdown("")

                    # ─── Footer ──────────────────────────────────
                    gr.HTML("""
                    <div class="footer-text">
                        🔒 <strong>TaxFlow AI</strong> v1.0.0 — All processing is local and private.
                        Made with ❤️ for Indian GST compliance.
                    </div>
                    """)

        # ─── Dashboard ────────────────────────────────────────
        refresh_dashboard_btn.click(
            handle_refresh_dashboard,
            outputs=[dashboard_content],
        )

        # ─── Calendar ──────────────────────────────────────────
        # Calendar is static (loaded on init), but refreshable
        app.load(
            lambda: build_calendar_html(),
            outputs=[calendar_content],
        )

        # ─── Activity ──────────────────────────────────────────
        refresh_activity_btn.click(
            handle_refresh_activity,
            outputs=[activity_content],
        )
        clear_activity_btn.click(
            handle_clear_activity,
            outputs=[activity_content],
        )

        # ─── CSV Export ────────────────────────────────────────
        export_gstr1_csv_btn.click(
            handle_export_gstr1_csv,
            outputs=[export_csv_msg, export_status],
        )
        export_gstr3b_csv_btn.click(
            handle_export_gstr3b_csv,
            outputs=[export_csv_msg, export_status],
        )

        # ─── Accounting Reports ────────────────────────────────
        bs_btn.click(lambda: handle_accounting_report("balance_sheet"), outputs=[bs_content])
        cf_btn.click(lambda: handle_accounting_report("cash_flow"), outputs=[cf_content])
        tb_btn.click(lambda: handle_accounting_report("trial_balance"), outputs=[tb_content])
        ls_btn.click(lambda: handle_accounting_report("ledger"), outputs=[ls_content])

        # ─── TDS/TCS ──────────────────────────────────────────
        tds_calc_btn.click(handle_tds_calculation, outputs=[tds_content, tcs_content])

        # ─── Penalty Calculator ───────────────────────────────
        penalty_calc_btn.click(handle_penalty_calculation, outputs=[penalty_content])

        # ─── Cash Flow Forecast ───────────────────────────────
        forecast_3mo_btn.click(lambda: handle_cash_flow_forecast(3), outputs=[forecast_content])
        forecast_6mo_btn.click(lambda: handle_cash_flow_forecast(6), outputs=[forecast_content])

        # ─── Knowledge Base ────────────────────────────────────
        kb_btn.click(handle_knowledge_base_search, inputs=[kb_query], outputs=[kb_results])

        # ─── Onboarding ────────────────────────────────────────
        onboarding_btn.click(handle_onboarding_checklist, outputs=[onboarding_content])

        # ─── Processing Logs ──────────────────────────────────
        logs_btn.click(handle_processing_logs, outputs=[logs_content])

        # ─── Tally Export ──────────────────────────────────────
        tally_export_btn.click(handle_tally_export, outputs=[tally_content])

        # ─── Event Handlers ──────────────────────────────────────

        # Chat
        def chat_wrapper(message, history):
            result = handle_chat(message, history)
            return result, ""

        send_btn.click(chat_wrapper, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input])
        msg_input.submit(chat_wrapper, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input])

        clear_chat_btn.click(handle_clear_chat, outputs=[chatbot])
        clear_chat_btn2.click(handle_clear_chat, outputs=[chatbot])

        # Projects
        project_dropdown.change(
            handle_select_project,
            inputs=[project_dropdown],
            outputs=[project_info, project_stats, sidebar_content, dashboard_content],
        )

        create_confirm_btn.click(
            handle_create_project,
            inputs=[new_project_name, new_project_gstin, new_project_notes],
            outputs=[project_info, project_dropdown],
        )

        delete_project_btn.click(
            handle_delete_project,
            inputs=[project_dropdown],
            outputs=[project_info, project_dropdown],
        )

        # Upload
        upload_btn.click(
            handle_file_upload,
            inputs=[file_input],
            outputs=[upload_msg, sidebar_content, upload_status],
        )

        # Reports
        export_excel_btn.click(
            handle_export_excel,
            outputs=[export_msg, export_status],
        )
        export_pdf_btn.click(
            handle_export_pdf,
            outputs=[export_msg, export_status],
        )
        export_json_btn.click(
            handle_export_json,
            outputs=[export_msg, export_status],
        )

        # Settings
        save_settings_btn.click(
            handle_update_settings,
            inputs=[settings_model, settings_temp],
            outputs=[settings_msg],
        )
        refresh_settings_btn.click(
            handle_settings_refresh,
            outputs=[settings_status],
        )
        pull_model_btn.click(
            handle_pull_model,
            inputs=[pull_model_name],
            outputs=[pull_status],
        )

        # Sidebar
        refresh_btn.click(
            handle_refresh_sidebar,
            outputs=[project_info, project_stats, sidebar_content],
        )
        refresh_data_btn.click(
            handle_refresh_sidebar,
            outputs=[project_info, project_stats, sidebar_content],
        )

        # Auth
        login_btn.click(
            handle_login,
            inputs=[login_username, login_password],
            outputs=[login_panel, main_app, login_msg, login_username, login_password, project_dropdown],
        )
        reg_btn.click(
            handle_register,
            inputs=[reg_username, reg_password],
            outputs=[reg_msg],
        )
        logout_btn.click(
            handle_logout,
            outputs=[login_panel, main_app],
        )

        # Create Project button opens the accordion
        create_project_btn.click(
            lambda: gr.update(open=True),
            outputs=[new_project_accordion],
        )

        # Initialize projects on load
        def load_projects():
            if _CURRENT_USER_ID:
                projects = get_projects(_CURRENT_USER_ID)
                return gr.update(choices=[(p["name"], p["id"]) for p in projects])
            return gr.update(choices=[])

        app.load(load_projects, outputs=[project_dropdown])

    return app
