<div align="center">
  <h1>🧾 TaxFlow AI</h1>
  <p><strong>Local AI-Powered GST Compliance & Tax Automation Platform</strong></p>
  <p>
    <img src="https://img.shields.io/badge/version-1.0.0-blue?style=flat-square" alt="Version">
    <img src="https://img.shields.io/badge/python-3.10%2B-green?style=flat-square" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-orange?style=flat-square" alt="License">
    <img src="https://img.shields.io/badge/privacy-100%25_local-brightgreen?style=flat-square" alt="Privacy">
    <img src="https://img.shields.io/badge/framework-Gradio-8A2BE2?style=flat-square" alt="Gradio">
    <img src="https://img.shields.io/badge/ai-Ollama-FF6F00?style=flat-square" alt="Ollama">
    <img src="https://img.shields.io/badge/stack-FastAPI-009688?style=flat-square" alt="FastAPI">
  </p>
</div>

---

## 📋 Overview

TaxFlow AI is a **fully local, privacy-first** platform that leverages AI to automate GST compliance for Indian businesses. It processes invoices, reconciles bank statements, matches Input Tax Credit (ITC), generates GSTR returns, detects anomalies, and provides financial summaries — all **running 100% on your machine** with zero data leaving your computer.

**Perfect for:** Chartered Accountants, Tax Professionals, SMEs, and businesses managing GST compliance.

---

## ✨ Features

### 🔌 Core Capabilities

| Feature | Description |
|---------|-------------|
| **📄 Smart Document Processing** | Upload invoices (PDF/Excel/Images), bank statements (CSV/PDF/Excel), e-way bills — AI auto-extracts all GST data |
| **🤖 Multi-Agent AI System** | 6 specialized AI agents: Document Extractor, Reconciliation Agent, ITC Matcher, GSTR Returns Agent, Anomaly Detector, Financial Analyst |
| **🏦 Bank Reconciliation** | Automatically matches bank transactions to invoices with confidence scoring, flags partial payments and discrepancies |
| **✅ ITC Matching & Verification** | Checks Input Tax Credit eligibility under GST rules, identifies blocked credits, and provides recommendations |
| **📊 GSTR-1 & GSTR-3B Generation** | Auto-generates return-ready data from invoices with rate-wise summaries and tax breakdowns |
| **⚠️ Anomaly Detection** | Flags GSTIN mismatches, tax calculation errors, reconciliation gaps, missing data, and compliance issues |
| **📈 Export Reports** | Professional Excel reports, print-ready PDFs, and machine-readable JSON exports |
| **💬 Natural Language Chat** | Ask questions in plain English — *"Reconcile my bank statement"*, *"Check ITC for all invoices"*, *"Generate GSTR-1"* |

### 🎨 User Interface

- **Modern Gradio UI** with dark/light/system theme toggle (persisted via localStorage)
- **Responsive design** — works on desktop and tablet
- **Animated micro-interactions** — smooth transitions, hover effects, loading states
- **Real-time sidebar** — shows stats, recent documents, invoices, and anomalies
- **Multi-tab interface** — Chat, Upload, Reports, Settings

### 🛡️ Privacy & Security

- **100% Local** — All AI runs on your machine via [Ollama](https://ollama.com/)
- **Encrypted Storage** — Client data encrypted at rest using Fernet (AES-128)
- **No Telemetry** — Zero analytics, no data collection
- **No API Calls** — No data ever sent to external services
- **User Authentication** — Local SQLite-based auth with session management

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TaxFlow AI Platform                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐       ┌─────────────────────────┐  │
│  │    Gradio UI         │       │    FastAPI Backend      │  │
│  │  (app/ui/chat.py)    │       │    (app/api.py)         │  │
│  │                      │       │                         │  │
│  │  • Chat Interface    │       │  • REST Endpoints       │  │
│  │  • File Upload       │◄─────►│  • Auth API             │  │
│  │  • Reports Tab       │       │  • Data Export API      │  │
│  │  • Settings Panel    │       │  • Health Check         │  │
│  │  • Theme Toggle      │       │                         │  │
│  └──────────┬───────────┘       └─────────────────────────┘  │
│             │                                                │
│  ┌──────────▼───────────────────────────────────────────┐    │
│  │              Multi-Agent Orchestrator                │    │
│  │              (app/agents/orchestrator.py)            │    │
│  │                                                      │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │    │
│  │  │Document  │ │Reconciler│ │ITC       │ │GSTR    │  │    │
│  │  │Extractor │ │Agent     │ │Matcher   │ │Returns │  │    │
│  │  └─────┬────┘ └────┬─────┘ └────┬─────┘ └────┬───┘  │    │
│  │        └────────────┴────────────┴────────────┘      │    │
│  │                        │                             │    │
│  │              ┌─────────▼──────────┐                  │    │
│  │              │Anomaly Detector    │                  │    │
│  │              └───────────────────┘                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │              Ollama LLM Client                       │    │
│  │              (app/ollama_client.py)                  │    │
│  │              ┌──────────────────────┐                │    │
│  │              │  LangChain + Ollama  │                │    │
│  │              └──────────────────────┘                │    │
│  └─────────────────────────────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │              Local SQLite Database                   │    │
│  │              (app/database.py)                       │    │
│  │                                                      │    │
│  │  • Main DB (taxflow.db): users, sessions, projects   │    │
│  │  • Per-Project DBs (client_data/): invoices,         │    │
│  │    transactions, anomalies, chat history             │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Ollama** installed and running → [Download Ollama](https://ollama.com/download)
- **8GB+ RAM** (16GB recommended for larger models)

### Installation

```bash
# 1. Install Ollama and pull a model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b

# 2. Navigate to project
cd taxflow-ai

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure (optional)
cp .env.example .env

# 6. Run!
python app.py
```

Open **http://localhost:7860** in your browser.

---

## 🔐 Default Login

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Admin |

---

## 🎮 Usage Guide

### 1. Create a Project

Click **"➕ New"** in the sidebar → enter a Client Name (e.g. "Acme Corp") → click **"Create Project"**.

### 2. Upload Documents

Go to the **"📤 Upload"** tab → drag & drop invoices and bank statements → click **"Process Files"**. The AI will automatically extract all GST data.

### 3. Chat with AI

Ask questions naturally in the **"💬 Chat"** tab:

| Query | What happens |
|-------|-------------|
| *"Analyze my uploaded documents"* | AI extracts all data from unprocessed documents |
| *"Reconcile the bank statement with invoices"* | Matches payments to invoices with confidence scoring |
| *"Check ITC matching for all invoices"* | Verifies Input Tax Credit eligibility for each invoice |
| *"Generate GSTR-1 for this period"* | Creates GSTR-1 return data with rate-wise summaries |
| *"Generate GSTR-3B for last month"* | Creates GSTR-3B summary with ITC and tax liability |
| *"Detect any anomalies in the data"* | Scans for mismatches, errors, and compliance issues |
| *"Show me a financial summary"* | Produces P&L overview, tax summary, and recommendations |

### 4. Export Reports

Go to the **"📊 Reports"** tab → choose **Excel**, **PDF**, or **JSON** export.

### 5. Configure Settings

Go to the **"⚙️ Settings"** tab to:
- Change Ollama model (e.g. `qwen2.5:14b`, `mistral`, `phi3:14b`)
- Adjust temperature for precision vs creativity
- Pull new models directly from the UI

### 6. Theme Toggle

Click the theme button in the header to cycle through:
- **☀️ Light** — Clean, bright interface
- **🌙 Dark** — Easy on the eyes for extended use
- **💻 System** — Follows your OS preference

Your choice is saved automatically.

---

## 📁 Project Structure

```
taxflow-ai/
├── app.py                         # Gradio UI entry point
├── main.py                        # FastAPI + Gradio combined entry
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container build
├── .env.example                   # Environment template
├── README.md                      # This file
│
├── app/
│   ├── __init__.py
│   ├── config.py                  # Central configuration (pydantic-settings)
│   ├── auth.py                    # Local authentication (SQLite + PBKDF2)
│   ├── database.py                # SQLite database layer (encrypted)
│   ├── ollama_client.py           # Ollama LLM wrapper (LangChain)
│   ├── prompts.py                 # Centralized prompt management
│   ├── models.py                  # Pydantic data models
│   ├── api.py                     # FastAPI REST API router
│   ├── main.py                    # FastAPI application with mounted Gradio
│   │
│   ├── agents/
│   │   ├── orchestrator.py        # Main agent orchestrator (intent routing)
│   │   ├── extractor.py           # Document extraction agent
│   │   ├── reconciler.py          # Bank reconciliation agent
│   │   ├── itc_matcher.py         # ITC matching & verification
│   │   ├── gst_returns.py         # GSTR-1 & GSTR-3B generation
│   │   └── anomaly.py             # Anomaly detection agent
│   │
│   ├── document_processing/
│   │   ├── utils.py               # Shared utilities (PDF/Excel/CSV parsing)
│   │   ├── invoice.py             # Invoice extraction (regex + AI)
│   │   └── bank_stmt.py           # Bank statement processing
│   │
│   ├── reports/
│   │   ├── excel.py               # Excel report generation (openpyxl)
│   │   ├── pdf.py                 # PDF report generation (ReportLab)
│   │   └── json_report.py         # JSON data export
│   │
│   └── ui/
│       ├── chat.py                # Complete Gradio chat interface
│       └── styles.py              # Full CSS theme system (light/dark)
│
├── data/
│   └── sample/                    # Sample test data
│       ├── invoice_1.pdf
│       ├── invoice_2.pdf
│       ├── invoice_3.xlsx
│       └── bank_statement.csv
│
├── client_data/                   # Encrypted per-project databases (auto)
├── uploads/                       # Uploaded files (auto)
├── exports/                       # Generated reports (auto)
└── prompts/
    └── agent_prompts/             # Custom prompt overrides (optional)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | [Gradio](https://www.gradio.app/) 5.x (Python UI framework) |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) (REST API server) |
| **AI/LLM** | [Ollama](https://ollama.com/) + [LangChain](https://www.langchain.com/) (local LLM inference) |
| **Database** | SQLite 3 with WAL mode + Fernet encryption at rest |
| **PDF Processing** | pdfplumber + PyMuPDF |
| **Excel Processing** | openpyxl + pandas |
| **PDF Reports** | ReportLab |
| **Auth** | PBKDF2-SHA256 hashing + SQLite sessions |
| **Configuration** | pydantic-settings (`.env` support) |
| **Containerization** | Docker (multi-stage build) |

---

## 🔧 Configuration

All settings in `app/config.py` can be overridden via `.env` file:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TEMPERATURE=0.1
OLLAMA_TOP_P=0.9
OLLAMA_MAX_TOKENS=4096

# Web UI
GRADIO_SERVER_PORT=7860
GRADIO_SHARE=false

# App Settings
DEBUG=true
APP_NAME=TaxFlow AI
```

### Complete Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama2:latest` | Default LLM model (change to `llama3.1:8b` for better accuracy) |
| `OLLAMA_TEMPERATURE` | `0.1` | LLM temperature (lower = more precise, higher = more creative) |
| `OLLAMA_TOP_P` | `0.9` | Nucleus sampling parameter |
| `OLLAMA_MAX_TOKENS` | `4096` | Max tokens per response |
| `GRADIO_SERVER_PORT` | `7860` | Web UI port |
| `GRADIO_SHARE` | `false` | Create public Gradio share link |
| `DEBUG` | `true` | Debug mode (verbose logging) |
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum file upload size |
| `SESSION_EXPIRE_HOURS` | `24` | Session duration |

---

## 🐳 Docker Deployment

```bash
# Build the image
docker build -t taxflow-ai .

# Run with host network (recommended - access local Ollama)
docker run --network=host -v $(pwd)/client_data:/app/client_data taxflow-ai

# Run with remote Ollama
docker run -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
           -p 7860:7860 \
           -v $(pwd)/client_data:/app/client_data \
           taxflow-ai
```

---

## 📡 REST API

The FastAPI backend provides a REST API at `http://localhost:8000/api` (when running via `python main.py`).

### Authentication

```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login?username=admin&password=admin123"

# Response: {"user_id": "...", "token": "..."}
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login and get session token |
| `GET` | `/api/projects` | List all projects (auth required) |
| `POST` | `/api/projects` | Create a new project (auth required) |
| `GET` | `/api/projects/{id}` | Get project details with stats (auth required) |
| `POST` | `/api/chat` | Send chat message to AI agent |
| `GET` | `/api/projects/{id}/invoices` | Get all invoices for a project |
| `GET` | `/api/projects/{id}/transactions` | Get all bank transactions |
| `GET` | `/api/projects/{id}/anomalies` | Get all detected anomalies |
| `GET` | `/api/projects/{id}/gstr1` | Get GSTR-1 return data |
| `GET` | `/api/projects/{id}/gstr3b` | Get GSTR-3B return data |
| `GET` | `/api/system/status` | System health and Ollama status |
| `GET` | `/api/system/models` | List available Ollama models |
| `GET` | `/api/health` | Health check |

### Example: Chat API

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What invoices do I have?",
    "project_id": "<project-uuid>"
  }'

# Response:
# {
#   "response": "You have 3 invoices totaling ₹1,23,456...",
#   "actions_taken": ["Analyzed 3 existing invoices"]
# }
```

API docs are also available at **http://localhost:8000/docs** (Swagger UI).

---

## ⚙️ Recommended Ollama Models

| Model | Size | Quality | Speed | RAM | Recommendation |
|-------|------|---------|-------|-----|---------------|
| `llama3.1:8b` | 4.9GB | ★★★★☆ | ★★★★☆ | 8GB+ | ✅ **Best overall** |
| `qwen2.5:14b` | 8.5GB | ★★★★★ | ★★★☆☆ | 16GB+ | Best for complex analysis |
| `mistral` | 4.1GB | ★★★★☆ | ★★★★★ | 8GB+ | Fastest option |
| `phi3:14b` | 8.2GB | ★★★★★ | ★★★☆☆ | 16GB+ | Strong for Indian context |
| `llama3.2:3b` | 2.0GB | ★★★☆☆ | ★★★★★ | 4GB+ | Lightweight option |

---

## 🧪 Sample Test Data

Sample invoices and bank statements are in `data/sample/`:

### Invoice 1 (PDF) — Sales Invoice
- **Invoice #**: INV-2024-001, **Date**: 15-01-2024
- **Seller**: TechMart Solutions (GSTIN: 27AABCT1234F1Z5)
- **Buyer**: Global Trade Co (GSTIN: 29AAAFG5678H1Z6)
- **Items**: Laptops (HSN 847130), Printers (HSN 844332)
- **Tax**: 9% CGST + 9% SGST (Intra-state: Maharashtra)
- **Total**: ₹1,18,000

### Invoice 2 (PDF) — Services Invoice
- **Invoice #**: INV-2024-002, **Date**: 20-01-2024
- **Seller**: CloudSaaS Ltd (GSTIN: 06AABCS9012J1Z7)
- **Buyer**: RetailMart India (GSTIN: 07AAARM3456K1Z8)
- **Items**: Software Services (SAC 998311)
- **Tax**: 18% IGST (Inter-state: Gujarat → Delhi)
- **Total**: ₹5,90,000

### Invoice 3 (Excel) — Export Invoice
- **Invoice #**: EXP-2024-001, **Date**: 25-01-2024
- **Seller**: ExportHouse Inc (GSTIN: 33AAAE7890L1Z9)
- **Buyer**: International Buyer LLC
- **Tax**: 0% (Export with LUT)
- **Total**: $25,000 USD

### Bank Statement (CSV)
- **Period**: January 2024
- **Transactions**: 20+ entries (payments, receipts, expenses)
- **Balance**: Opening ₹5,00,000 → Closing ₹6,25,000

---

## 🤖 How the AI Works

```
User Message
     │
     ▼
┌─────────────┐     ┌──────────────────┐
│ Intent      │────►│ Agent            │
│ Detection   │     │ Orchestrator     │
│ (keywords)  │     │                  │
└─────────────┘     │ Routes to the    │
                    │ right specialist │
                    │ agent            │
                    └───────┬──────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                  ▼
   ┌──────────┐    ┌──────────────┐   ┌────────────┐
   │Document  │    │ Reconciliation│   │  GSTR      │
   │Extractor │    │ Agent         │   │  Returns   │
   │          │    │               │   │  Agent      │
   │Extracts  │    │Matches       │   │            │
   │data from │    │bank txns to  │   │Generates   │
   │invoices  │    │invoices      │   │return data │
   └────┬─────┘    └──────┬───────┘   └─────┬──────┘
        │                 │                  │
        └─────────────────┼──────────────────┘
                          ▼
                    ┌───────────┐
                    │ Anomaly   │
                    │ Detector  │
                    │           │
                    │Flags any │
                    │issues    │
                    └─────┬────┘
                          │
                          ▼
                    ┌───────────┐
                    │  Response │
                    │  (Markdown│
                    │  + data)  │
                    └───────────┘
```

**Key design principles:**
1. **Intent Detection** — The orchestrator analyzes user messages to determine the task (document analysis, reconciliation, GSTR, etc.)
2. **Specialized Agents** — Each agent has deep knowledge of its domain (GST law, banking, returns)
3. **Data Extraction** — Files are parsed using multiple strategies (regex, PDF parsers, AI-assisted)
4. **AI Enhancement** — Ollama provides natural language understanding and generation for complex fields
5. **Local Storage** — All data is stored in encrypted SQLite databases with per-project isolation

---

## 🔒 Privacy Guarantee

> ✅ **No internet required** — Everything runs on your machine
> ✅ **No data collection** — Zero telemetry, analytics, or tracking
> ✅ **No API calls** — All AI uses local Ollama inference
> ✅ **Encrypted storage** — Client data encrypted at rest with AES-128 (Fernet)
> ✅ **Open source** — Inspect every line of code

---

## 🛠️ Troubleshooting

### "Ollama is not running"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama (if not running):
# macOS: Open the Ollama app
# Linux: systemctl start ollama
# Or run: ollama serve
```

### "Model not found"
```bash
# Pull the recommended model
ollama pull llama3.1:8b

# List available models
ollama list
```

### Slow responses or high RAM usage
- Use a smaller model: `phi3:mini` (3.8B) or `llama3.2:3b`
- Reduce `OLLAMA_MAX_TOKENS` to 2048
- Close other applications
- Reduce `num_ctx` in Ollama config

### File upload fails
- Supported formats: PDF, CSV, XLSX, XLS, JSON, XML, TXT, JPG, PNG
- Max file size: 50MB (configurable in `.env`)
- For scanned PDFs: apply OCR before uploading

### Database errors
```bash
# Reset databases (will delete all data)
rm -rf client_data/ taxflow.db .encryption_key
```

---

## 🧪 Development

### Running Tests
```bash
# Activate environment
source venv/bin/activate

# Run with debug logging
python app.py
```

### Adding a New Agent
1. Create the agent class in `app/agents/`
2. Register it in `app/agents/orchestrator.py`
3. Add intent detection keywords in `_detect_intent()`
4. Add handler method in the orchestrator

### Custom Prompts
Create `.txt` files in `prompts/agent_prompts/` to override any built-in prompt:
- `system.txt` — System prompt
- `invoice_extraction.txt` — Invoice extraction prompt
- `reconciliation.txt` — Bank reconciliation prompt
- `gstr1_generation.txt` — GSTR-1 prompt
- `gstr3b_generation.txt` — GSTR-3B prompt
- `anomaly_detection.txt` — Anomaly detection prompt

---

## 📝 Roadmap

- [ ] GSTR-2A/2B auto-download and matching against uploaded invoices
- [ ] E-way bill generation and tracking
- [ ] Multi-user support with role-based access (Admin, User, Viewer)
- [ ] OCR integration for scanned/physical documents
- [ ] Dashboard with interactive charts and graphs
- [ ] Batch processing for multiple clients simultaneously
- [ ] Email integration for automated invoice collection
- [ ] Custom report builder with drag-and-drop fields
- [ ] HSN/SAC code lookup database with rate finder
- [ ] Export to popular accounting formats (ClearTally, Zoho Books, TallyPrime)
- [ ] Integration with GST portal for auto-filing
- [ ] Mobile-responsive PWA support

---

## 📄 License

**MIT License** — Free for personal and commercial use. See `LICENSE` for details.

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.com/) — Making local LLMs accessible to everyone
- [LangChain](https://www.langchain.com/) — Agent framework and LLM integration
- [Gradio](https://www.gradio.app/) — Beautiful Python web UI framework
- [FastAPI](https://fastapi.tiangolo.com/) — High-performance API backend
- [pdfplumber](https://github.com/jsvine/pdfplumber) — PDF table extraction
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF text extraction
- [ReportLab](https://www.reportlab.com/) — PDF report generation
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel file processing

---

<div align="center">
  <p><strong>Made with ❤️ for Indian Tax Professionals, CA Firms, and Businesses</strong></p>
  <p>🔒 <em>Your data stays yours. Always.</em></p>
</div>
