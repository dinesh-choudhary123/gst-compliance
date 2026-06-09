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
        return "No project selected", "", ""

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

    return info, stats, gr.update(value=sidebar_items)


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

    for file_info in files:
        filename = file_info.name if hasattr(file_info, 'name') else os.path.basename(file_info)
        file_path = file_info if isinstance(file_info, str) else file_info.name

        # Copy to project uploads
        project_upload_dir = _UPLOAD_DIR / _CURRENT_PROJECT_ID
        os.makedirs(project_upload_dir, exist_ok=True)
        dest_path = project_upload_dir / filename

        try:
            shutil.copy2(file_path, dest_path)
        except Exception:
            # If file_info is already a path string, handle differently
            if os.path.isfile(file_path):
                shutil.copy2(file_path, dest_path)
            else:
                results.append(f"❌ Could not process: {filename}")
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
        file_size = os.path.getsize(dest_path)
        doc = add_document(
            _CURRENT_PROJECT_ID,
            filename,
            str(dest_path),
            doc_type=doc_type,
            file_size_bytes=file_size,
        )

        # Process with AI if available
        if _extractor and _orchestrator:
            try:
                result = _extractor.process_document(
                    _CURRENT_PROJECT_ID,
                    doc["id"],
                    str(dest_path),
                    filename,
                    doc_type,
                )
                if result.get("success"):
                    results.append(f"✅ {result.get('message', 'Processed')}")
                    all_messages.append(result.get("message", ""))
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

    return summary, gr.update(value=sidebar_items), f"📄 {len(files)} file(s) uploaded"


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
        return f"✅ JSON report generated", gr.update(visible=True)
    except Exception as e:
        return f"❌ JSON export error: {str(e)}", None


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

                        # ─── Settings Tab ─────────────────────────
                        with gr.TabItem("⚙️ Settings", id=3):
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
            outputs=[project_info, project_stats, sidebar_content],
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
