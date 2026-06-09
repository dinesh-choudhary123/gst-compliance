"""FastAPI application with mounted Gradio UI.

This is the main application module that combines FastAPI backend
with Gradio frontend served from the same process.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn
import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import init_auth_db
from app.config import settings
from app.ui.chat import build_app
from app.api import router as api_router

# Create FastAPI app
app = FastAPI(
    title="TaxFlow AI",
    description="Local AI Chatbot for GST Compliance & Tax Automation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the API router
app.include_router(api_router, prefix="/api")

# Initialize auth database on startup
@app.on_event("startup")
async def startup():
    init_auth_db()
    # Ensure directories exist
    os.makedirs(settings.CLIENT_DATA_DIR, exist_ok=True)
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    os.makedirs(settings.BASE_DIR / "exports", exist_ok=True)
    os.makedirs(settings.BASE_DIR / "uploads", exist_ok=True)


# Mount Gradio app at the root
print("🎨 Building Gradio UI...")
gradio_app = build_app()
app = gr.mount_gradio_app(app, gradio_app, path="/")


# ─── Direct Execution ────────────────────────────────────────────

if __name__ == "__main__":
    # Rebuild directly
    ui = build_app()

    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║                    TaxFlow AI                        ║
    ║         Local AI Chatbot for GST Compliance          ║
    ╚══════════════════════════════════════════════════════╝

    🌐 UI:     http://localhost:{settings.GRADIO_SERVER_PORT}
    📡 API:    http://localhost:8000/api

    🔒 All data stays local. Powered by Ollama.
    """)

    ui.launch(
        server_name="0.0.0.0",
        server_port=settings.GRADIO_SERVER_PORT,
        share=settings.GRADIO_SHARE,
        show_error=True,
    )
