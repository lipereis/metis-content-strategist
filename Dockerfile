# Dockerfile — Content Strategist Agent
# Build: docker build -t content-strategist .
# Run: docker run -v $(pwd)/data:/app/data content-strategist

FROM python:3.11-slim

# Metadata
LABEL maintainer="Content Strategist Team"
LABEL description="Content Strategist & Viral Scriptwriter Agent"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/ ./scripts/
COPY templates/ ./templates/
COPY references/ ./references/
COPY QUICKSTART.md .

# Create directories
RUN mkdir -p /app/config /app/state /app/output /app/transcripts /app/data

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Default command shows help
CMD ["python", "scripts/review_local.py", "--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/scripts'); from utils.formatting import FORMATTERS; print('OK')" || exit 1