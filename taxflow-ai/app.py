#!/usr/bin/env python3
"""TaxFlow AI - Convenience entry point for Gradio UI.

Usage:
    python app.py          # Start the web UI
    python main.py         # Start both API and UI (alternative)
"""

import os
import sys
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.ui.chat import build_app


def main():
    """Start the Gradio UI directly."""
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║                    TaxFlow AI                        ║
    ║         Local AI Chatbot for GST Compliance          ║
    ╚══════════════════════════════════════════════════════╝

    🔒 All data is processed locally. No data leaves your machine.
    🤖 Powered by Ollama for private AI inference.

    📋 Default login: admin / admin123
    """)

    # Open browser
    webbrowser.open(f"http://localhost:{settings.GRADIO_SERVER_PORT}")

    # Build and launch the Gradio app
    app = build_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=settings.GRADIO_SERVER_PORT,
        share=settings.GRADIO_SHARE,
        show_error=True,
    )


if __name__ == "__main__":
    main()
