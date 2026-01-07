"""
Agent Catalog Service
Standalone microservice for Agent Card management
For MCPHub (K-ARC) integration
PostgreSQL persistence + Redis Cache
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from typing import List, Optional
from loguru import logger
import sys

from .models import AgentInfo, AgentRegistration, AgentURLRegistration
from .registry import registry

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await registry.start()
    logger.info("Agent Catalog Service started (PostgreSQL + Redis Cache)")
    
    yield
    
    # Shutdown
    await registry.stop()
    logger.info("Agent Catalog Service stopped")


# API Tags metadata
tags_metadata = [
    {
        "name": "Health",
        "description": "서비스 헬스체크 엔드포인트",
    },
    {
        "name": "Agents",
        "description": "Agent 등록, 조회, 검색, 삭제 관리",
    },
    {
        "name": "Health Monitoring",
        "description": "Agent 헬스 모니터링 - 대시보드, 이력 조회, 헬스체크 실행",
    },
    {
        "name": "Statistics",
        "description": "카탈로그 통계 조회",
    },
]

app = FastAPI(
    title="Agent Catalog Service",
    description="""
## K-Jarvis Agent Catalog Service

A2A Protocol 기반 AI Agent 카탈로그 관리 서비스입니다.

### 주요 기능

- 🤖 **Agent 관리**: 등록, 조회, 검색, 삭제
- 🔍 **A2A Discovery**: URL로 Agent Card 자동 fetch
- 🏥 **헬스 모니터링**: 60초 간격 자동 헬스체크
- 📊 **대시보드**: Uptime, 응답시간, 장애 횟수

### 데이터 저장

- **PostgreSQL**: Agent 정보 영속화
- **Redis**: 캐시 레이어 (Cache-Aside Pattern)

### 관련 서비스

- K-Jarvis Orchestrator: http://localhost:4001
- MCPHub (K-ARC): http://localhost:3000
""",
    version="1.3.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "K-Jarvis Team",
        "url": "https://github.com/OG056501-Opensource-Poc/agent-card",
    },
    license_info={
        "name": "Internal Use Only",
        "identifier": "KT-Internal",
    },
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:4000",
        "http://localhost:5173",
        "http://mcphub-frontend:5173",
        "http://mcphub-frontend-local:5173",
        "*"  # Development - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health Check
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    서비스 헬스체크
    
    서비스 상태와 연결된 Agent 수를 반환합니다.
    """
    try:
        stats = await registry.get_stats()
        return {
            "status": "healthy",
            "service": "agent-catalog-service",
            "version": "1.1.0",
            "persistence": "postgresql",
            "agents_online": stats.get('online_agents', 0),
            "agents_total": stats.get('total_agents', 0)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "agent-catalog-service",
            "version": "1.1.0",
            "error": str(e)
        }


# =============================================================================
# Agent Catalog API
# =============================================================================

@app.get("/api/agents", response_model=List[AgentInfo], tags=["Agents"])
async def list_agents(
    include_offline: bool = Query(False, description="오프라인 Agent 포함 여부")
):
    """
    Agent 목록 조회
    
    등록된 모든 Agent의 목록을 반환합니다.
    
    - **include_offline**: True면 오프라인 Agent도 포함
    
    **캐시**: 1분 TTL (Redis)
    """
    return await registry.list_agents(include_offline=include_offline)


@app.get("/api/agents/search", tags=["Agents"])
async def search_agents(
    q: Optional[str] = Query(None, description="검색어 (이름, 설명)"),
    tags: Optional[str] = Query(None, description="태그 (쉼표 구분)"),
    skill: Optional[str] = Query(None, description="스킬 이름"),
    domain: Optional[str] = Query(None, description="도메인 (development, project_management 등)")
):
    """
    Agent 검색
    
    다양한 조건으로 Agent를 검색합니다.
    
    - **q**: 이름 또는 설명에서 검색
    - **tags**: 스킬 태그로 필터링 (예: "github,pr")
    - **skill**: 스킬 이름으로 필터링
    - **domain**: 라우팅 도메인으로 필터링
    
    **예시**: `/api/agents/search?q=github&domain=development`
    """
    tag_list = tags.split(",") if tags else None
    return await registry.search_agents(query=q, tags=tag_list, skill=skill, domain=domain)


@app.get("/api/agents/{agent_id}", response_model=AgentInfo, tags=["Agents"])
async def get_agent(agent_id: str):
    """
    Agent 상세 조회
    
    ID로 특정 Agent의 상세 정보를 조회합니다.
    
    **캐시**: 5분 TTL (Redis)
    """
    agent = await registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.post("/api/agents/register", response_model=AgentInfo, tags=["Agents"])
async def register_agent(registration: AgentRegistration):
    """
    Agent 등록 (직접 입력)
    
    Agent 정보를 직접 입력하여 등록합니다.
    
    **참고**: URL 기반 등록(A2A Discovery)을 권장합니다.
    """
    try:
        agent = await registry.register_agent(registration)
        return agent
    except Exception as e:
        logger.error(f"Agent registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/agents/register/url", response_model=AgentInfo, tags=["Agents"])
async def register_agent_by_url(registration: AgentURLRegistration):
    """
    Agent 등록 (URL - A2A Discovery) ⭐ 권장
    
    Agent URL을 입력하면 `/.well-known/agent.json`에서 
    Agent Card를 자동으로 가져와 등록합니다.
    
    **A2A Protocol 표준 방식입니다.**
    
    **예시 요청**:
    ```json
    {"url": "http://kjarvis-github-agent:5012"}
    ```
    """
    try:
        agent = await registry.register_agent_by_url(registration.url)
        return agent
    except Exception as e:
        logger.error(f"Agent URL registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/agents/{agent_id}", tags=["Agents"])
async def unregister_agent(agent_id: str):
    """
    Agent 삭제
    
    등록된 Agent를 카탈로그에서 제거합니다.
    """
    if await registry.unregister_agent(agent_id):
        return {"status": "unregistered", "agent_id": agent_id}
    raise HTTPException(status_code=404, detail="Agent not found")


@app.post("/api/agents/{agent_id}/refresh", response_model=AgentInfo, tags=["Agents"])
async def refresh_agent(agent_id: str):
    """
    Agent 정보 갱신
    
    Agent Card를 다시 fetch하여 최신 정보로 업데이트합니다.
    """
    agent = await registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        refreshed = await registry.register_agent_by_url(agent.url)
        return refreshed
    except Exception as e:
        logger.error(f"Agent refresh failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/agents/{agent_id}/health-check", tags=["Health Monitoring"])
async def trigger_health_check(agent_id: str):
    """
    개별 Agent 헬스체크
    
    특정 Agent의 헬스체크를 수동으로 실행합니다.
    
    **반환값**:
    - `healthy`: 헬스체크 성공 여부
    - `status`: online/offline
    - `last_seen`: 마지막 응답 시간
    """
    agent = await registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    is_healthy = await registry.check_agent_health(agent)
    
    # Get updated agent info
    updated_agent = await registry.get_agent(agent_id)
    
    return {
        "agent_id": agent_id,
        "name": updated_agent.name if updated_agent else agent.name,
        "status": updated_agent.status if updated_agent else agent.status,
        "healthy": is_healthy,
        "last_seen": updated_agent.last_seen.isoformat() if updated_agent and updated_agent.last_seen else None
    }


# =============================================================================
# Statistics
# =============================================================================

@app.get("/api/stats", tags=["Statistics"])
async def get_stats():
    """
    카탈로그 통계 조회
    
    Agent 카탈로그의 전체 통계를 반환합니다.
    
    **반환값**:
    - `total_agents`: 전체 Agent 수
    - `online_agents`: 온라인 Agent 수
    - `offline_agents`: 오프라인 Agent 수
    - `total_skills`: 전체 스킬 수
    - `agents_by_domain`: 도메인별 Agent 수
    
    **캐시**: 1분 TTL (Redis)
    """
    return await registry.get_stats()


# =============================================================================
# Health Monitoring API
# =============================================================================

@app.get("/api/health/dashboard", tags=["Health Monitoring"])
async def get_health_dashboard():
    """
    헬스 대시보드 조회
    
    모든 Agent의 헬스 상태를 대시보드 형태로 반환합니다.
    
    **반환값** (각 Agent별):
    - `status`: online/offline
    - `last_seen`: 마지막 응답 시간
    - `last_health_check`: 마지막 헬스체크 시간
    - `health_check_failures`: 연속 실패 횟수
    - `avg_response_time_1h`: 최근 1시간 평균 응답시간 (ms)
    - `uptime_24h`: 최근 24시간 가동률 (%)
    
    **캐시**: 30초 TTL (Redis)
    """
    return await registry.get_dashboard()


@app.get("/api/health/history", tags=["Health Monitoring"])
async def get_health_history(
    agent_id: Optional[str] = Query(None, description="Agent ID로 필터링"),
    limit: int = Query(100, description="최대 레코드 수", ge=1, le=1000)
):
    """
    헬스체크 이력 조회
    
    헬스체크 결과 이력을 조회합니다.
    
    - **agent_id**: 특정 Agent로 필터링 (선택)
    - **limit**: 최대 레코드 수 (기본: 100)
    
    **반환값** (각 레코드별):
    - `agent_name`, `agent_url`: Agent 정보
    - `status`: online/offline
    - `response_time_ms`: 응답시간 (밀리초)
    - `error_message`: 에러 메시지 (있는 경우)
    - `checked_at`: 체크 시간
    
    **캐시**: 2분 TTL, 최근 100개 (Redis)
    """
    return await registry.get_health_history(agent_id=agent_id, limit=limit)


@app.get("/api/health/history/{agent_id}", tags=["Health Monitoring"])
async def get_agent_health_history(
    agent_id: str,
    limit: int = Query(50, description="최대 레코드 수", ge=1, le=500)
):
    """
    특정 Agent 헬스체크 이력 조회
    
    특정 Agent의 헬스체크 이력만 조회합니다.
    
    - **agent_id**: Agent ID (필수)
    - **limit**: 최대 레코드 수 (기본: 50)
    
    **캐시**: 2분 TTL, 최근 100개 (Redis)
    """
    # Verify agent exists
    agent = await registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return await registry.get_health_history(agent_id=agent_id, limit=limit)


@app.post("/api/health/check-all", tags=["Health Monitoring"])
async def trigger_all_health_checks():
    """
    전체 Agent 헬스체크 실행
    
    등록된 모든 Agent에 대해 헬스체크를 실행합니다.
    
    **반환값**:
    - `total`: 전체 Agent 수
    - `online`: 온라인 Agent 수
    - `offline`: 오프라인 Agent 수
    - `results`: 각 Agent별 결과 목록
    
    **주의**: 모든 Agent에 요청을 보내므로 시간이 소요될 수 있습니다.
    """
    agents = await registry.list_agents(include_offline=True)
    results = []
    
    for agent in agents:
        is_healthy = await registry.check_agent_health(agent)
        results.append({
            "agent_id": agent.id,
            "name": agent.name,
            "healthy": is_healthy,
            "status": "online" if is_healthy else "offline"
        })
    
    online_count = sum(1 for r in results if r['healthy'])
    
    return {
        "total": len(results),
        "online": online_count,
        "offline": len(results) - online_count,
        "results": results
    }


@app.delete("/api/health/history/cleanup", tags=["Health Monitoring"])
async def cleanup_health_history(
    days: int = Query(7, description="삭제할 이력의 기준 일수", ge=1, le=365)
):
    """
    헬스체크 이력 정리
    
    지정된 일수보다 오래된 헬스체크 이력을 삭제합니다.
    
    - **days**: 이 일수보다 오래된 이력 삭제 (기본: 7일)
    
    **반환값**:
    - `deleted_records`: 삭제된 레코드 수
    - `older_than_days`: 기준 일수
    """
    from .database import db
    deleted = await db.cleanup_old_health_history(days=days)
    return {
        "deleted_records": deleted,
        "older_than_days": days
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
