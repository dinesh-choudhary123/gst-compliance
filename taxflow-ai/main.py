#!/usr/bin/env python3
"""TaxFlow AI - Local AI Chatbot for GST Compliance & Tax Automation.

Run this script to start both the FastAPI backend and the Gradio UI.
"""

import os
import sys
import webbrowser
from pathlib import Path

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.config import settings


def main():
    """Main entry point - start the application."""
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║                    TaxFlow AI                        ║
    ║         Local AI Chatbot for GST Compliance          ║
    ║                  & Tax Automation                    ║
    ╚══════════════════════════════════════════════════════╝

    🔒 All data processing is LOCAL and PRIVATE.
    🧾 Powered by Ollama for AI inference.
    """)

    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ is required")
        sys.exit(1)

    # Ensure directories exist
    Path(settings.CLIENT_DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.BASE_DIR / "exports").mkdir(parents=True, exist_ok=True)
    Path(settings.BASE_DIR / "uploads").mkdir(parents=True, exist_ok=True)

    # Print configuration
    print(f"📁 Data Directory: {settings.DATA_DIR}")
    print(f"🔐 Client Data: {settings.CLIENT_DATA_DIR}")
    print(f"🤖 Ollama Model: {settings.OLLAMA_MODEL}")
    print(f"🌡️  Temperature: {settings.OLLAMA_TEMPERATURE}")
    print()

    # Start the server
    print(f"🚀 Starting TaxFlow AI...")
    print(f"   🌐 Web UI:      http://localhost:{settings.GRADIO_SERVER_PORT}")
    print(f"   📡 API:         http://localhost:8000")
    print(f"   📋 API Docs:    http://localhost:8000/docs")
    print()

    # Open browser
    webbrowser.open(f"http://localhost:{settings.GRADIO_SERVER_PORT}")

    # Run both FastAPI and Gradio via uvicorn
    # The Gradio app is mounted within the FastAPI app
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )


if __name__ == "__main__":
    main()
