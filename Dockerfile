# ═══════════════════════════════════════════
# Corporate Toxic Comment Detector
# Multi-stage Docker Build
# Compatible with Hugging Face Spaces
# ═══════════════════════════════════════════

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend + Serve Frontend
FROM python:3.11-slim

WORKDIR /app

# Install system deps for Presidio + ML
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY models/ ./models/
COPY config.yaml .

# Create data directory (audit DB will be created at runtime)
RUN mkdir -p data

# Copy built frontend into /app/static
COPY --from=frontend-build /app/frontend/dist ./static

# Expose port (7860 for HF Spaces, 8000 for standalone)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/api/health')"

# Run FastAPI — HF Spaces requires port 7860
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
