# 🧾 TaxFlow AI

**Local AI Chatbot for GST Compliance & Tax Automation in India**

TaxFlow AI is a fully local, privacy-first application that uses AI to automate GST compliance tasks. It processes invoices, reconciles bank statements, matches Input Tax Credit (ITC), generates GSTR returns, detects anomalies, and provides financial summaries — all running 100% on your machine with no data leaving your computer.

![TaxFlow AI](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![Privacy](https://img.shields.io/badge/privacy-100%25_local-brightgreen)

---

## 🚀 Features

### 📄 Document Processing
- **Invoice Extraction**: Automatically extracts GST details, HSN codes, tax splits, and amounts from PDF, Excel, and image invoices
- **Bank Statement Processing**: Parses CSV, PDF, and Excel bank statements, extracting all transactions
- **Smart Classification**: Automatically identifies document types (invoice, bank statement, e-way bill, etc.)

### 🤖 AI-Powered Agents
- **Document Extractor**: Extracts structured data from uploaded documents using AI
- **Reconciliation Agent**: Matches bank transactions to invoices with confidence scoring
- **ITC Matcher**: Verifies Input Tax Credit eligibility under GST rules
- **GSTR Returns Agent**: Generates GSTR-1 and GSTR-3B return data
- **Anomaly Detector**: Identifies mismatches, tax errors, and compliance issues

### 📊 Reports & Export
- **Excel Reports**: Professional formatted reports with summaries
- **PDF Reports**: Print-ready PDF documents
- **JSON Export**: Machine-readable data export
- **Real-time Dashboards**: Sidebar shows documents, invoices, transactions, and anomalies

### 🛡️ Privacy & Security
- **100% Local**: All processing happens on your machine using Ollama
- **Encrypted Storage**: Client data encryption at rest
- **User Authentication**: Simple local auth with session management
- **No Data Leakage**: Zero data sent to external services

---

## 📋 Prerequisites

1. **Python 3.10+** installed
2. **Ollama** installed and running ([Download Ollama](https://ollama.com/download))
3. At least **8GB RAM** (16GB recommended for larger models)

---

## 🔧 Installation

### Step 1: Install Ollama and Pull a Model

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com/download

# Pull a model (recommended for GST work)
ollama pull llama3.1:8b

# Alternative good models:
# ollama pull qwen2.5:14b
# ollama pull mistral
# ollama pull phi3:14b
```

### Step 2: Clone and Setup TaxFlow AI

```bash
# Navigate to the project directory
cd taxflow-ai

# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment (Optional)

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed (defaults work for most setups)
# OLLAMA_MODEL=llama3.1:8b
# OLLAMA_TEMPERATURE=0.1
```

---

## 🎮 Running TaxFlow AI

### Quick Start (Gradio UI only)
```bash
python app.py
```
Opens the web UI at `http://localhost:7860`

### Full Stack (FastAPI + Gradio UI)
```bash
python main.py
```
Opens the web UI at `http://localhost:7860` and API at `http://localhost:8000`

### Docker
```bash
# Build the image
docker build -t taxflow-ai .

# Run with host network (for local Ollama)
docker run --network=host -v $(pwd)/client_data:/app/client_data taxflow-ai

# Run with remote Ollama
docker run -e OLLAMA_BASE_URL=http://host.docker.internal:11434 -p 7860:7860 taxflow-ai
```

---

## 🔐 First Time Login

| Username | Password | Role |
|----------|----------|------|
| `admin`  | `admin123` | Admin |

**Important:** Change the default password after first login!

---

## 🧪 Sample Test Data

Sample test data is located in `data/sample/`:

### Invoice 1 (PDF) - Sample Sales Invoice
- **Invoice #**: INV-2024-001
- **Seller**: TechMart Solutions, GSTIN: 27AABCT1234F1Z5
- **Buyer**: Global Trade Co, GSTIN: 29AAAFG5678H1Z6
- **Items**: Laptops (HSN 847130), Printers (HSN 844332)
- **Tax**: 9% CGST + 9% SGST (Intra-state: Maharashtra → Maharashtra)
- **Total**: ₹1,18,000

### Invoice 2 (PDF) - Services Invoice
- **Invoice #**: INV-2024-002
- **Seller**: CloudSaaS Ltd, GSTIN: 06AABCS9012J1Z7
- **Buyer**: RetailMart India, GSTIN: 07AAARM3456K1Z8
- **Items**: Software Services (SAC 998311)
- **Tax**: 18% IGST (Inter-state: Gujarat → Delhi)
- **Total**: ₹5,90,000

### Invoice 3 (Excel) - Export Invoice
- **Invoice #**: EXP-2024-001
- **Seller**: ExportHouse Inc, GSTIN: 33AAAE7890L1Z9
- **Buyer**: International Buyer LLC
- **Items**: Cotton Textiles (HSN 5208)
- **Tax**: 0% (Export with LUT)
- **Total**: $25,000 USD

### Bank Statement (CSV) - Monthly Statement
- Contains 20+ transactions including:
  - Multiple invoice payments
  - GST payments
  - Operating expenses
  - Salary payments
  - Opening/Closing balances

---

## 🗺️ How to Use

### 1. Create a Project
- Login with admin/admin123
- Click "New" to create a client project
- Enter client name and GSTIN (optional)

### 2. Upload Documents
- Go to the "Upload" tab
- Drag & drop invoices and bank statements
- Click "Process Files" — the AI automatically extracts data

### 3. Chat with AI
- Ask questions naturally:
  - *"Analyze my uploaded documents"*
  - *"Reconcile the bank statement with invoices"*
  - *"Check ITC matching for all invoices"*
  - *"Generate GSTR-1 for this period"*
  - *"Generate GSTR-3B for last month"*
  - *"Detect any anomalies in the data"*
  - *"Show me a financial summary"*
  - *"What are the outstanding payments?"*

### 4. Export Reports
- Go to "Reports" tab
- Choose Excel, PDF, or JSON export
- Reports include invoice details, GSTR data, reconciliation status

### 5. Configure Settings
- Change Ollama model (try different models for better results)
- Adjust temperature (lower = more precise, higher = more creative)
- Pull new models directly from the UI

---

## 📁 Project Structure

```
taxflow-ai/
├── app.py                    # Gradio UI entry point
├── main.py                   # FastAPI + Gradio entry point
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker build
├── README.md                 # This file
├── .env.example              # Environment config template
│
├── app/
│   ├── __init__.py
│   ├── config.py             # Application configuration
│   ├── auth.py               # Local authentication
│   ├── database.py           # SQLite database layer
│   ├── models.py             # Pydantic data models
│   ├── api.py                # FastAPI REST endpoints
│   ├── prompts.py            # LLM prompt management
│   ├── ollama_client.py      # Ollama LLM client wrapper
│   │
│   ├── agents/
│   │   ├── orchestrator.py   # Main agent orchestrator
│   │   ├── extractor.py      # Document extraction agent
│   │   ├── reconciler.py     # Bank reconciliation agent
│   │   ├── itc_matcher.py    # ITC matching agent
│   │   ├── gst_returns.py    # GSTR-1/3B generation
│   │   └── anomaly.py        # Anomaly detection
│   │
│   ├── document_processing/
│   │   ├── invoice.py        # Invoice extraction
│   │   ├── bank_stmt.py      # Bank statement processing
│   │   └── utils.py          # Shared utilities
│   │
│   ├── reports/
│   │   ├── excel.py          # Excel report generation
│   │   ├── pdf.py            # PDF report generation
│   │   └── json_report.py    # JSON export
│   │
│   └── ui/
│       ├── chat.py           # Gradio chat interface
│       └── styles.py         # CSS styles
│
├── data/
│   └── sample/               # Sample test data
│       ├── invoice_1.pdf
│       ├── invoice_2.pdf
│       ├── invoice_3.xlsx
│       └── bank_statement.csv
│
├── client_data/              # Encrypted client data (auto-created)
├── uploads/                  # Uploaded files (auto-created)
├── exports/                  # Generated reports (auto-created)
└── prompts/
    └── agent_prompts/        # Custom prompt files (optional)
```

---

## 🔧 Configuration

All configuration is in `app/config.py` and can be overridden via `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1:8b` | Default LLM model |
| `OLLAMA_TEMPERATURE` | `0.1` | LLM temperature (0.0-1.0) |
| `GRADIO_SERVER_PORT` | `7860` | Web UI port |
| `GRADIO_SHARE` | `false` | Create public link |
| `DEBUG` | `true` | Debug mode |

---

## ⚙️ Recommended Models

| Model | Size | Quality | Speed | RAM |
|-------|------|---------|-------|-----|
| `llama3.1:8b` | 4.7GB | ★★★★☆ | ★★★★☆ | 8GB+ |
| `qwen2.5:14b` | 8.5GB | ★★★★★ | ★★★☆☆ | 16GB+ |
| `mistral` | 4.1GB | ★★★★☆ | ★★★★★ | 8GB+ |
| `phi3:14b` | 8.2GB | ★★★★★ | ★★★☆☆ | 16GB+ |

**llama3.1:8b** is recommended for most users as it offers the best balance of quality and speed for GST work.

---

## 🧠 How the AI Works

1. **Document Upload**: Files are saved locally and metadata is recorded in SQLite
2. **AI Extraction**: Ollama processes documents to extract structured data with high precision prompts
3. **Multi-Agent Orchestration**: Specialized agents handle specific tasks (reconciliation, ITC, GSTR)
4. **LangChain Integration**: Structured prompt chains for multi-step reasoning
5. **Local Database**: All extracted data is stored in encrypted SQLite databases
6. **Report Generation**: Data can be exported as Excel, PDF, or JSON

---

## 🔒 Privacy Guarantee

- **No internet required**: Everything runs on your machine
- **No data collection**: Zero telemetry or analytics
- **No API calls**: All AI uses local Ollama inference
- **Encrypted storage**: Client data is encrypted at rest
- **Open source**: Inspect every line of code

---

## 🛠️ Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it:
# macOS: open the Ollama app
# Linux: systemctl start ollama
```

### Model Not Found
```bash
# Pull the recommended model
ollama pull llama3.1:8b

# Check available models
ollama list
```

### Performance Issues
- Close other applications to free RAM
- Try a smaller model (e.g., `phi3:mini` or `llama3.2:3b`)
- Reduce `num_ctx` in the Ollama configuration

### File Upload Issues
- Supported formats: PDF, CSV, XLSX, XLS, JSON, XML, TXT
- Max file size: 50MB (configurable)
- For scanned PDFs: Ensure OCR is applied first

---

## 📝 TODO / Future Enhancements

- [ ] GSTR-2A/2B auto-download and matching
- [ ] E-way bill generation and tracking
- [ ] Multi-user support with roles
- [ ] OCR for scanned documents
- [ ] Dashboard with charts and graphs
- [ ] Batch processing for multiple clients
- [ ] Email integration for invoice collection
- [ ] Custom report builder
- [ ] HSN/SAC code lookup database
- [ ] GST rate change updates
- [ ] Export to ClearTally/Zoho/QuickBooks formats

---

## 📄 License

MIT License - Free for personal and commercial use.

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.com/) for making local LLMs accessible
- [LangChain](https://www.langchain.com/) for the agent framework
- [Gradio](https://www.gradio.app/) for the web UI framework
- [FastAPI](https://fastapi.tiangolo.com/) for the API backend

---

*Made with ❤️ for Indian Tax Professionals and CA Firms*
