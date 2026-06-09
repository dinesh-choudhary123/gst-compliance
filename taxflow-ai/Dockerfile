# TaxFlow AI - Dockerfile
# Multi-stage build for a lean production image

# ─── Builder Stage ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ─── Runtime Stage ───────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data client_data exports uploads prompts

# Expose ports
EXPOSE 7860  # Gradio UI
EXPOSE 8000   # FastAPI

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: Run Gradio UI
CMD ["python", "app.py"]

# ─── Alternative Commands ────────────────────────────────────────
# To run with FastAPI + Gradio together:
#   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
#
# To build:
#   docker build -t taxflow-ai .
#
# To run with Ollama (requires host network for local Ollama):
#   docker run --network=host -v $(pwd)/client_data:/app/client_data taxflow-ai
#
# To run with remote Ollama:
#   docker run -e OLLAMA_BASE_URL=http://host.docker.internal:11434 -p 7860:7860 taxflow-ai
