#!/bin/bash
# =============================================================================
# K-Jarvis - Run with OpenTelemetry (Programmatic)
# KT AI 에이전트 플랫폼
# 로컬 환경에서 OTEL을 활성화하여 실행
# =============================================================================

echo "=============================================="
echo "K-Jarvis with OpenTelemetry"
echo "=============================================="

# OpenTelemetry 환경변수 설정
export OTEL_ENABLED="true"
export OTEL_SERVICE_NAME="k-jarvis"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://ap-collector.4.217.129.211.nip.io"
export OTEL_ENVIRONMENT="development"

echo "[INFO] OTEL_ENABLED: $OTEL_ENABLED"
echo "[INFO] OTEL_SERVICE_NAME: $OTEL_SERVICE_NAME"
echo "[INFO] OTEL_EXPORTER_OTLP_ENDPOINT: $OTEL_EXPORTER_OTLP_ENDPOINT"
echo "[INFO] OTEL_ENVIRONMENT: $OTEL_ENVIRONMENT"
echo ""

# OpenTelemetry 패키지 확인
if ! python -c "from opentelemetry import trace" 2>/dev/null; then
    echo "[WARN] OpenTelemetry not installed. Installing..."
    pip install opentelemetry-api opentelemetry-sdk \
        opentelemetry-exporter-otlp \
        opentelemetry-instrumentation-fastapi \
        opentelemetry-instrumentation-httpx
fi

echo "[INFO] Starting orchestrator..."
echo "=============================================="

# 일반 Python 실행 (프로그래매틱 OTEL)
python run_orchestrator.py
