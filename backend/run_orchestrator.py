#!/usr/bin/env python3
"""
Run the Agent Orchestrator server
OpenTelemetry instrumentation enabled
"""
import os
import uvicorn
from app.config import get_settings


def setup_opentelemetry():
    """
    OpenTelemetry 프로그래매틱 설정
    OTEL_ENABLED=true 환경변수로 활성화
    """
    otel_enabled = os.getenv("OTEL_ENABLED", "false").lower() == "true"
    
    if not otel_enabled:
        print("[OTEL] OpenTelemetry is disabled (set OTEL_ENABLED=true to enable)")
        return None
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        
        service_name = os.getenv("OTEL_SERVICE_NAME", "agent-orchestrator")
        otlp_endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", 
            "http://ap-collector.4.217.129.211.nip.io"
        )
        environment = os.getenv("OTEL_ENVIRONMENT", "development")
        
        # 리소스 설정
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": environment
        })
        
        # TracerProvider 설정
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        
        # OTLP Exporter 설정 (HTTP)
        exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
        
        # HTTPX 클라이언트 계측 (에이전트 호출 추적)
        HTTPXClientInstrumentor().instrument()
        
        print(f"[OTEL] OpenTelemetry enabled")
        print(f"[OTEL]   Service: {service_name}")
        print(f"[OTEL]   Endpoint: {otlp_endpoint}")
        print(f"[OTEL]   Environment: {environment}")
        
        return FastAPIInstrumentor()
        
    except ImportError as e:
        print(f"[OTEL] OpenTelemetry packages not installed: {e}")
        return None
    except Exception as e:
        print(f"[OTEL] Failed to setup OpenTelemetry: {e}")
        return None


def main():
    settings = get_settings()
    
    # OpenTelemetry 설정 (앱 import 전에 호출)
    fastapi_instrumentor = setup_opentelemetry()
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║           🤖 Agent Fabric - AI Agent Orchestrator             ║
    ║                                                                ║
    ║   Intelligent routing service for AI agents                   ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"📡 Starting server on http://{settings.host}:{settings.port}")
    print(f"📚 API Docs: http://localhost:{settings.port}/docs")
    print(f"📖 ReDoc: http://localhost:{settings.port}/redoc")
    print("")
    
    # FastAPI 앱에 계측 적용
    if fastapi_instrumentor:
        from app.main import app
        fastapi_instrumentor.instrument_app(app)
        print("[OTEL] FastAPI instrumentation applied")
        print("")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
