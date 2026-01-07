# Agent Catalog Service

K-Jarvis 생태계의 **Agent Card 관리**를 위한 독립 마이크로서비스입니다.

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)]()
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)]()
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)]()

---

## 📋 목차

- [개요](#-개요)
- [아키텍처](#-아키텍처)
- [주요 기능](#-주요-기능)
- [API 문서 (Swagger)](#-api-문서-swagger)
- [캐시 전략](#-캐시-전략-cache-aside-pattern)
- [데이터 흐름](#-데이터-흐름)
- [API 엔드포인트](#-api-엔드포인트)
- [빠른 시작](#-빠른-시작)
- [환경 변수](#-환경-변수)
- [API 사용 예시](#-api-사용-예시)
- [MCPHub 연동](#-mcphub-frontend-연동)

---

## 📖 개요

이 서비스는 **A2A Protocol**을 준수하는 AI Agent들의 카탈로그를 관리합니다.

### 핵심 역할
- 🔍 Agent 등록, 조회, 검색, 삭제
- 🏥 Agent 헬스 모니터링 (60초 간격)
- 📊 실시간 대시보드 및 통계 제공
- 🔗 MCPHub(K-ARC) Frontend와 연동

---

## 🏗 아키텍처

### 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "Client Layer"
        MHF[MCPHub Frontend<br/>:5173]
        KJF[K-Jarvis Frontend<br/>:4000]
    end

    subgraph "Agent Catalog Service :8080"
        API[FastAPI Server]
        REG[Registry<br/>Agent 관리]
        CACHE[Cache Manager<br/>Redis 캐싱]
        DB_MGR[Database Manager<br/>PostgreSQL]
    end

    subgraph "Data Layer"
        REDIS[(Redis<br/>Cache DB 1)]
        PG[(PostgreSQL<br/>agent_catalog)]
    end

    subgraph "AI Agents (A2A Protocol)"
        GA[GitHub Agent<br/>:5012]
        JA[Jira Agent<br/>:5011]
        CA[Confluence Agent<br/>:5010]
        SA[Sample Agent<br/>:5020]
    end

    MHF --> API
    KJF --> API
    API --> REG
    REG --> CACHE
    REG --> DB_MGR
    CACHE --> REDIS
    DB_MGR --> PG
    REG --> GA
    REG --> JA
    REG --> CA
    REG --> SA
```

### 서비스 컴포넌트

```mermaid
graph LR
    subgraph "app/"
        MAIN[main.py<br/>FastAPI 앱]
        MODELS[models.py<br/>Pydantic 모델]
        REGISTRY[registry.py<br/>Agent 관리 로직]
        CACHE[cache.py<br/>Redis 캐시]
        DATABASE[database.py<br/>PostgreSQL 연결]
    end

    MAIN --> REGISTRY
    REGISTRY --> CACHE
    REGISTRY --> DATABASE
    REGISTRY --> MODELS
```

---

## ✨ 주요 기능

### Agent 관리
| 기능 | 설명 |
|------|------|
| ✅ Agent 목록 조회 | 온라인/전체 Agent 목록 |
| ✅ Agent 상세 조회 | ID로 개별 Agent 정보 |
| ✅ Agent 등록 (직접) | JSON으로 직접 등록 |
| ✅ Agent 등록 (URL) | A2A Discovery - URL로 Agent Card 자동 fetch |
| ✅ Agent 삭제 | Agent 등록 해제 |
| ✅ Agent 검색 | 이름, 태그, 스킬, 도메인으로 검색 |

### 헬스 모니터링
| 기능 | 설명 |
|------|------|
| ✅ 자동 헬스체크 | 60초 간격 백그라운드 실행 |
| ✅ 수동 헬스체크 | 개별/전체 Agent 헬스체크 트리거 |
| ✅ 헬스 대시보드 | 응답시간, Uptime, 장애 횟수 |
| ✅ 헬스 이력 조회 | Agent별/전체 헬스체크 이력 |

### 데이터 관리
| 기능 | 설명 |
|------|------|
| ✅ PostgreSQL 영속화 | 서버 재시작 후에도 데이터 유지 |
| ✅ Redis 캐싱 | 조회 성능 최적화 (Cache-Aside) |
| ✅ 배치 DB 쓰기 | 헬스체크 이력 10개 단위 저장 |

---

## 📚 API 문서 (Swagger)

서비스가 실행되면 아래 URL에서 인터랙티브 API 문서를 확인할 수 있습니다.

| 문서 | URL | 설명 |
|------|-----|------|
| **Swagger UI** | http://localhost:8080/docs | 인터랙티브 API 테스트 |
| **ReDoc** | http://localhost:8080/redoc | 읽기 편한 API 문서 |
| **OpenAPI JSON** | http://localhost:8080/openapi.json | OpenAPI 3.0 스펙 |

### Swagger UI 스크린샷

```
┌─────────────────────────────────────────────────────────────────┐
│  Agent Catalog Service                              v1.3.0      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ▼ Health                                                       │
│    GET  /health                서비스 헬스체크                    │
│                                                                 │
│  ▼ Agents                                                       │
│    GET  /api/agents            Agent 목록 조회                   │
│    GET  /api/agents/search     Agent 검색                        │
│    GET  /api/agents/{id}       Agent 상세 조회                   │
│    POST /api/agents/register   Agent 등록 (직접)                 │
│    POST /api/agents/register/url  Agent 등록 (URL) ⭐            │
│    DELETE /api/agents/{id}     Agent 삭제                        │
│    POST /api/agents/{id}/refresh  Agent 정보 갱신                │
│                                                                 │
│  ▼ Health Monitoring                                            │
│    GET  /api/health/dashboard  헬스 대시보드                      │
│    GET  /api/health/history    헬스체크 이력                      │
│    POST /api/health/check-all  전체 헬스체크                      │
│    DELETE /api/health/history/cleanup  이력 정리                 │
│                                                                 │
│  ▼ Statistics                                                   │
│    GET  /api/stats             카탈로그 통계                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### API 카테고리

| 카테고리 | 설명 |
|----------|------|
| **Health** | 서비스 헬스체크 |
| **Agents** | Agent 등록, 조회, 검색, 삭제 |
| **Health Monitoring** | 대시보드, 헬스체크 이력, 수동 헬스체크 |
| **Statistics** | 카탈로그 통계 |

---

## 🚀 캐시 전략 (Cache-Aside Pattern)

### 캐시 아키텍처

```mermaid
flowchart TB
    subgraph "READ 요청"
        R1[API 요청] --> R2{Redis 캐시<br/>확인}
        R2 -->|HIT| R3[캐시 데이터 반환]
        R2 -->|MISS| R4[PostgreSQL 조회]
        R4 --> R5[Redis에 저장]
        R5 --> R6[데이터 반환]
    end

    subgraph "WRITE 요청"
        W1[API 요청] --> W2[PostgreSQL 저장]
        W2 --> W3[Redis 캐시 무효화]
        W3 --> W4[응답 반환]
    end
```

### TTL (Time-To-Live) 설정

| 캐시 대상 | Redis 키 | TTL | 이유 |
|----------|----------|-----|------|
| Agent Card | `agent:{id}` | 5분 | 자주 변경되지 않음 |
| Agent 목록 | `agents:online`, `agents:all` | 1분 | 목록 변경 가능성 |
| **대시보드** | `dashboard` | **30초** | 실시간성 필요 |
| 헬스 이력 | `health:{agent_id}`, `health:all` | 2분 | 최근 100개만 |
| 통계 | `stats` | 1분 | 집계 데이터 |
| 실시간 상태 | `agent:{id}:status` | 2분 | 빠른 상태 확인 |

### 캐시 키 구조

```
agent:{uuid}              # Agent Card 전체 데이터
agent:{uuid}:status       # 실시간 상태 (status, last_seen)
agents:online             # 온라인 Agent 목록
agents:all                # 전체 Agent 목록
health:{uuid}             # Agent별 헬스체크 이력 (최근 100개)
health:all                # 전체 헬스체크 이력 (최근 100개)
dashboard                 # 대시보드 집계 데이터
stats                     # 통계 데이터
```

---

## 🔄 데이터 흐름

### Agent 등록 플로우 (A2A Discovery)

```mermaid
sequenceDiagram
    participant Client
    participant API as Agent Catalog
    participant Cache as Redis
    participant DB as PostgreSQL
    participant Agent as AI Agent

    Client->>API: POST /api/agents/register/url
    Note over Client,API: {"url": "http://agent:5012"}
    
    API->>Agent: GET /.well-known/agent.json
    Agent-->>API: Agent Card JSON
    
    API->>DB: INSERT agent_cards
    DB-->>API: Created
    
    API->>Cache: DELETE agents:* (캐시 무효화)
    API->>Cache: DELETE stats
    
    API-->>Client: AgentInfo 반환
```

### 헬스체크 플로우

```mermaid
sequenceDiagram
    participant Loop as Background Loop
    participant Registry
    participant Agent as AI Agents
    participant Cache as Redis
    participant DB as PostgreSQL

    loop Every 60 seconds
        Registry->>Cache: GET agents:all
        Cache-->>Registry: Agent 목록
        
        loop For each Agent
            Registry->>Agent: GET /.well-known/agent.json
            alt 응답 성공
                Agent-->>Registry: 200 OK
                Registry->>Registry: status = online
            else 응답 실패
                Registry->>Registry: status = offline
            end
            
            Registry->>Cache: SET agent:{id}:status
            Registry->>Cache: APPEND health:{id}
            Registry->>Registry: 배치에 추가
        end
        
        alt 배치 크기 >= 10
            Registry->>DB: BATCH INSERT health_check_history
        end
        
        Registry->>Cache: DELETE dashboard
    end
```

### API 조회 플로우 (Cache-Aside)

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Cache as Redis
    participant DB as PostgreSQL

    Client->>API: GET /api/agents
    
    API->>Cache: GET agents:online
    alt Cache HIT
        Cache-->>API: Agent 목록
        API-->>Client: 응답 (빠름)
    else Cache MISS
        Cache-->>API: null
        API->>DB: SELECT * FROM agent_cards
        DB-->>API: Agent 목록
        API->>Cache: SET agents:online (TTL: 60s)
        API-->>Client: 응답
    end
```

---

## 📡 API 엔드포인트

### Agent 관리

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 서비스 헬스체크 |
| GET | `/api/agents` | Agent 목록 조회 |
| GET | `/api/agents/search` | Agent 검색 |
| GET | `/api/agents/{id}` | Agent 상세 조회 |
| POST | `/api/agents/register` | Agent 등록 (직접 입력) |
| POST | `/api/agents/register/url` | Agent 등록 (URL - A2A Discovery) |
| DELETE | `/api/agents/{id}` | Agent 삭제 |
| POST | `/api/agents/{id}/refresh` | Agent 정보 갱신 |

### 헬스 모니터링

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/health/dashboard` | 전체 Agent 상태 대시보드 |
| GET | `/api/health/history` | 헬스체크 이력 (전체) |
| GET | `/api/health/history/{id}` | 헬스체크 이력 (Agent별) |
| POST | `/api/health/check-all` | 전체 Agent 헬스체크 실행 |
| POST | `/api/agents/{id}/health-check` | 개별 Agent 헬스체크 |
| DELETE | `/api/health/history/cleanup` | 오래된 이력 삭제 |

### 통계

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/stats` | 카탈로그 통계 |

---

## 🚀 빠른 시작

### Docker로 실행 (권장)

```bash
# 1. mcphub_default 네트워크 확인 (없으면 생성)
docker network create mcphub_default 2>/dev/null || true

# 2. 빌드 및 실행
docker build -t agent-catalog-service:1.3.0 .

docker run -d \
  --name agent-catalog-service \
  --network mcphub_default \
  -p 8080:8080 \
  -e DATABASE_URL="postgresql://mcphub:mcphub@mcphub-postgres-local:5432/agent_catalog" \
  -e REDIS_URL="redis://kjarvis-redis:6379/1" \
  agent-catalog-service:1.3.0

# 3. 로그 확인
docker logs -f agent-catalog-service
```

### Docker Compose로 실행

```bash
docker-compose up -d
```

### 헬스체크

```bash
curl http://localhost:8080/health
```

```json
{
  "status": "healthy",
  "service": "agent-catalog-service",
  "version": "1.3.0",
  "persistence": "postgresql",
  "agents_online": 2,
  "agents_total": 2
}
```

---

## ⚙️ 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 | `postgresql://mcphub:mcphub@mcphub-postgres-local:5432/agent_catalog` |
| `REDIS_URL` | Redis 연결 문자열 | `redis://kjarvis-redis:6379/1` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |

---

## 📝 API 사용 예시

### Agent 목록 조회

```bash
curl http://localhost:8080/api/agents
```

### Agent 등록 (URL - 권장)

```bash
curl -X POST http://localhost:8080/api/agents/register/url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://kjarvis-github-agent:5012"}'
```

### Agent 검색

```bash
# 이름/설명으로 검색
curl "http://localhost:8080/api/agents/search?q=github"

# 도메인으로 검색
curl "http://localhost:8080/api/agents/search?domain=development"
```

### 헬스 대시보드 조회

```bash
curl http://localhost:8080/api/health/dashboard
```

```json
[
  {
    "id": "97ceb09f-...",
    "name": "GitHub AI Agent",
    "status": "online",
    "last_seen": "2026-01-06T07:04:25.662294+00:00",
    "health_check_failures": 0,
    "avg_response_time_1h": 3.28,
    "uptime_24h": 100.0
  }
]
```

### 전체 Agent 헬스체크

```bash
curl -X POST http://localhost:8080/api/health/check-all
```

```json
{
  "total": 2,
  "online": 2,
  "offline": 0,
  "results": [
    {"agent_id": "...", "name": "Jira AI Agent", "healthy": true, "status": "online"},
    {"agent_id": "...", "name": "GitHub AI Agent", "healthy": true, "status": "online"}
  ]
}
```

### 통계 조회

```bash
curl http://localhost:8080/api/stats
```

```json
{
  "total_agents": 2,
  "online_agents": 2,
  "offline_agents": 0,
  "total_skills": 7,
  "agents_by_domain": {
    "development": 1,
    "project_management": 1
  }
}
```

---

## 🔗 MCPHub Frontend 연동

### TypeScript 예시

```typescript
const CATALOG_URL = 'http://agent-catalog-service:8080';

// Agent 목록 조회
const agents = await fetch(`${CATALOG_URL}/api/agents`).then(r => r.json());

// Agent 등록
await fetch(`${CATALOG_URL}/api/agents/register/url`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: 'http://my-agent:5010' })
});

// 대시보드 조회
const dashboard = await fetch(`${CATALOG_URL}/api/health/dashboard`).then(r => r.json());
```

---

## 🗄️ 데이터베이스 스키마

### agent_cards 테이블

```sql
CREATE TABLE agent_cards (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL UNIQUE,
    version VARCHAR(50),
    protocol_version VARCHAR(20),
    skills JSONB,
    capabilities JSONB,
    extensions JSONB,          -- K-Jarvis 확장 (requirements, routing)
    security_schemes JSONB,    -- A2A 표준
    security JSONB,
    provider JSONB,
    status VARCHAR(20),
    last_seen TIMESTAMP,
    last_health_check TIMESTAMP,
    health_check_failures INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### health_check_history 테이블

```sql
CREATE TABLE health_check_history (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agent_cards(id),
    status VARCHAR(20),
    response_time_ms INTEGER,
    error_message TEXT,
    checked_at TIMESTAMP
);
```

---

## 🐳 Docker 네트워크

이 서비스는 `mcphub_default` 네트워크에서 동작합니다.

```bash
# 네트워크 확인
docker network ls | grep mcphub

# Redis를 같은 네트워크에 연결 (필요시)
docker network connect mcphub_default kjarvis-redis
```

---

## 📊 성능 지표

| 지표 | 값 |
|------|-----|
| Cache HIT 응답 시간 | ~8-9ms |
| Cache MISS 응답 시간 | ~14ms |
| 헬스체크 간격 | 60초 |
| 배치 쓰기 크기 | 10개 |
| 최대 캐시 이력 | 100개/Agent |

---

## 🔧 트러블슈팅

### Redis 연결 실패

```bash
# Redis가 같은 네트워크에 있는지 확인
docker network connect mcphub_default kjarvis-redis

# 서비스 재시작
docker restart agent-catalog-service
```

### 캐시 초기화

```bash
# Redis DB 1 초기화
docker exec kjarvis-redis redis-cli -n 1 FLUSHDB
```

---

## 📁 프로젝트 구조

```
agent-catalog-service/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 앱 & 라우터
│   ├── models.py        # Pydantic 모델 (AgentInfo, AgentCard 등)
│   ├── registry.py      # Agent 관리 로직 (Cache-Aside)
│   ├── cache.py         # Redis 캐시 매니저
│   └── database.py      # PostgreSQL 연결 & CRUD
├── db/
│   └── schema.sql       # 데이터베이스 스키마
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 📜 라이선스

Internal Use Only - KT

---

## 🔗 관련 링크

- **GitHub**: https://github.com/OG056501-Opensource-Poc/agent-card
- **K-Jarvis Orchestrator**: http://localhost:4001
- **MCPHub (K-ARC)**: http://localhost:3000
