"""FastAPI API router for TaxFlow AI.

Provides REST API endpoints for external integrations.
The main UI is powered by Gradio, but this API can be used
for programmatic access or integration with other tools.
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.auth import authenticate_user, validate_session
from app.config import settings
from app.database import (
    get_projects,
    get_project,
    create_project,
    get_invoices,
    get_bank_transactions,
    get_anomalies,
    get_gstr_data,
)
from app.agents.orchestrator import AgentOrchestrator
from app.ollama_client import TaxFlowOllama

# ─── API Models ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    project_id: str

class ChatResponse(BaseModel):
    response: str
    actions_taken: list[str] = []

class ProjectCreate(BaseModel):
    name: str
    gstin: Optional[str] = ""
    pan: Optional[str] = ""
    notes: Optional[str] = ""

# ─── Router Setup ────────────────────────────────────────────────

router = APIRouter()

# Global instances (lazy initialized)
_ollama_client: Optional[TaxFlowOllama] = None
_orchestrator: Optional[AgentOrchestrator] = None


def _get_orchestrator() -> AgentOrchestrator:
    """Lazy-init and return the orchestrator."""
    global _ollama_client, _orchestrator
    if _orchestrator is None:
        try:
            _ollama_client = TaxFlowOllama()
            _orchestrator = AgentOrchestrator(_ollama_client)
        except Exception:
            raise HTTPException(status_code=503, detail="AI service not available. Check Ollama connection.")
    return _orchestrator


# ─── Auth Dependency ─────────────────────────────────────────────

async def get_current_user(authorization: str = ""):
    """Validate session token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    token = authorization.replace("Bearer ", "")
    user_id = validate_session(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user_id


# ─── Auth Endpoints ──────────────────────────────────────────────

@router.post("/auth/login")
async def login(username: str, password: str):
    """Login and get session token."""
    success, user_id, token = authenticate_user(username, password)
    if not success:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user_id": user_id, "token": token}


# ─── Project Endpoints ───────────────────────────────────────────

@router.get("/projects")
async def list_projects(user_id: str = Depends(get_current_user)):
    """List all projects for the authenticated user."""
    return get_projects(user_id)


@router.post("/projects")
async def new_project(project: ProjectCreate, user_id: str = Depends(get_current_user)):
    """Create a new project."""
    result = create_project(project.name, user_id, project.gstin, project.pan, "", project.notes)
    return result


@router.get("/projects/{project_id}")
async def get_project_details(project_id: str, user_id: str = Depends(get_current_user)):
    """Get project details with summary stats."""
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    invoices = get_invoices(project_id)
    transactions = get_bank_transactions(project_id)

    return {
        **project,
        "stats": {
            "invoices": len(invoices),
            "transactions": len(transactions),
            "total_taxable": sum(i.get("taxable_amount", 0) for i in invoices),
            "total_tax": sum(i.get("cgst_amount", 0) + i.get("sgst_amount", 0) + i.get("igst_amount", 0) for i in invoices),
        }
    }


# ─── Chat Endpoint ───────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return AI response."""
    orchestrator = _get_orchestrator()
    result = orchestrator.process_message(request.message, request.project_id)
    return ChatResponse(
        response=result.get("response", ""),
        actions_taken=result.get("actions_taken", []),
    )


# ─── Data Export Endpoints ───────────────────────────────────────

@router.get("/projects/{project_id}/invoices")
async def get_project_invoices(project_id: str):
    """Get all invoices for a project."""
    return get_invoices(project_id)


@router.get("/projects/{project_id}/transactions")
async def get_project_transactions(project_id: str):
    """Get all bank transactions for a project."""
    return get_bank_transactions(project_id)


@router.get("/projects/{project_id}/anomalies")
async def get_project_anomalies(project_id: str):
    """Get all anomalies for a project."""
    return get_anomalies(project_id)


@router.get("/projects/{project_id}/gstr1")
async def get_project_gstr1(project_id: str):
    """Get GSTR-1 data for a project."""
    return get_gstr_data(project_id, "gstr1")


@router.get("/projects/{project_id}/gstr3b")
async def get_project_gstr3b(project_id: str):
    """Get GSTR-3B data for a project."""
    return get_gstr_data(project_id, "gstr3b")


# ─── System Endpoints ────────────────────────────────────────────

@router.get("/system/status")
async def system_status():
    """Get system status including Ollama connection."""
    status = {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ollama_connected": False,
        "ollama_model": settings.OLLAMA_MODEL,
        "uptime": datetime.now().isoformat(),
    }

    if _ollama_client:
        status["ollama_connected"] = _ollama_client.is_available()
        status["available_models"] = _ollama_client.list_available_models()

    return status


@router.get("/system/models")
async def list_models():
    """List available Ollama models."""
    if not _ollama_client:
        return {"models": []}
    return {"models": _ollama_client.list_available_models()}


# ─── Health Check ────────────────────────────────────────────────

@router.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ollama": _ollama_client.is_available() if _ollama_client else False,
    }
