# =====================================================
# K-Jarvis - Backend Dockerfile
# KT AI 에이전트 플랫폼
# Platform: linux/amd64 (for Azure deployment)
# OpenTelemetry: Programmatic instrumentation
# =====================================================
FROM --platform=linux/amd64 python:3.11-slim

# Set working directory
WORKDIR /app

# =============================================================================
# OpenTelemetry Configuration (Programmatic)
# Set OTEL_ENABLED=true to enable tracing
# =============================================================================
ENV OTEL_ENABLED="true" \
    OTEL_SERVICE_NAME="k-jarvis" \
    OTEL_EXPORTER_OTLP_ENDPOINT="http://ap-collector.4.217.129.211.nip.io" \
    OTEL_ENVIRONMENT="production"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (with trusted hosts for corporate network)
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 4001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:4001/health || exit 1

# Run the application (OpenTelemetry is configured programmatically)
CMD ["python", "run_orchestrator.py"]
