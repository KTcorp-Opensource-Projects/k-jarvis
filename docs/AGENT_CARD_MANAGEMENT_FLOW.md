# Agent Card 관리 플로우 상세 가이드

## 1. 개요

Agent Card는 A2A(Agent-to-Agent) 프로토콜의 핵심 구성 요소로, AI Agent의 메타데이터를 표준화된 JSON 형식으로 정의합니다. Agent Catalog Service는 이러한 Agent Card들을 중앙에서 관리하고, K-Jarvis Orchestrator와 MCPHub(K-ARC)가 Agent 정보를 조회할 수 있도록 합니다.

---

## 2. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           K-Jarvis Ecosystem                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  K-Jarvis        │    │  MCPHub (K-ARC)  │    │  Agent Catalog   │       │
│  │  Frontend        │    │  Frontend        │    │  Service         │       │
│  │  (localhost:4000)│    │  (localhost:5173)│    │  (localhost:8080)│       │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘       │
│           │                       │                       │                  │
│           ▼                       ▼                       ▼                  │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  K-Jarvis        │◄──►│  MCPHub          │◄──►│  Agent Registry  │       │
│  │  Orchestrator    │    │  Backend         │    │  (In-Memory)     │       │
│  │  (localhost:4001)│    │  (localhost:3000)│    │                  │       │
│  └────────┬─────────┘    └──────────────────┘    └────────┬─────────┘       │
│           │                                               │                  │
│           │         ┌─────────────────────────────────────┘                  │
│           │         │                                                        │
│           ▼         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        AI Agents (A2A Protocol)                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │    │
│  │  │ GitHub Agent │  │ Jira Agent   │  │ Confluence   │  │ Sample   │ │    │
│  │  │ :5012        │  │ :5011        │  │ Agent :5010  │  │ Agent    │ │    │
│  │  │              │  │              │  │              │  │ :5020    │ │    │
│  │  │ /.well-known │  │ /.well-known │  │ /.well-known │  │          │ │    │
│  │  │ /agent.json  │  │ /agent.json  │  │ /agent.json  │  │          │ │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Card 구조 (A2A 표준)

```json
{
  "protocolVersion": "0.3.0",
  "name": "GitHub AI Agent",
  "description": "GitHub 저장소 관리를 위한 AI 에이전트",
  "url": "http://kjarvis-github-agent:5012",
  "version": "2.0.0",
  "skills": [
    {
      "id": "get_prs",
      "name": "get_pull_requests",
      "description": "GitHub PR 목록 조회",
      "tags": ["github", "pr", "pull-request"],
      "examples": ["최근 PR 보여줘", "PR 목록 조회해줘"],
      "inputModes": ["text/plain"],
      "outputModes": ["text/plain"]
    }
  ],
  "capabilities": {
    "multiTurn": true,
    "streaming": true,
    "tools": true
  },
  "requirements": {
    "mcpHubToken": true,
    "mcpServers": ["github-server"]
  },
  "routing": {
    "domain": "development",
    "category": "github",
    "keywords": ["github", "깃허브", "PR", "이슈", "커밋"],
    "capabilities": ["search", "read", "create", "update"]
  }
}
```

### 주요 필드 설명

| 필드 | 설명 | 필수 |
|------|------|------|
| `name` | Agent 이름 | ✅ |
| `description` | Agent 설명 | ✅ |
| `url` | Agent 서버 URL | ✅ |
| `version` | Agent 버전 | ✅ |
| `skills` | Agent가 제공하는 기능 목록 | ✅ |
| `capabilities` | Agent 기능 (스트리밍, 멀티턴 등) | ⚪ |
| `requirements` | 필요한 리소스 (MCPHub 토큰 등) | ⚪ |
| `routing` | 라우팅 메타데이터 (키워드, 도메인) | ⚪ |

---

## 4. Agent 등록 플로우

### 4.1 URL 기반 등록 (A2A Discovery) - 권장

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Admin     │     │  Agent Catalog  │     │   AI Agent      │
│   User      │     │  Service        │     │   Server        │
└──────┬──────┘     └────────┬────────┘     └────────┬────────┘
       │                     │                       │
       │  1. POST /api/agents/register/url           │
       │     {"url": "http://agent:5012"}            │
       │────────────────────►│                       │
       │                     │                       │
       │                     │  2. GET /.well-known/agent.json
       │                     │──────────────────────►│
       │                     │                       │
       │                     │  3. Return Agent Card │
       │                     │◄──────────────────────│
       │                     │                       │
       │                     │  4. Parse & Validate  │
       │                     │  Agent Card           │
       │                     │                       │
       │                     │  5. Store in Registry │
       │                     │  (In-Memory)          │
       │                     │                       │
       │  6. Return AgentInfo│                       │
       │◄────────────────────│                       │
       │                     │                       │
```

### 4.2 직접 등록

```
┌─────────────┐     ┌─────────────────┐
│   Admin     │     │  Agent Catalog  │
│   User      │     │  Service        │
└──────┬──────┘     └────────┬────────┘
       │                     │
       │  1. POST /api/agents/register
       │     {                
       │       "name": "My Agent",
       │       "description": "...",
       │       "url": "http://...",
       │       "skills": [...]
       │     }                
       │────────────────────►│
       │                     │
       │                     │  2. Validate Input
       │                     │
       │                     │  3. Create AgentInfo
       │                     │
       │                     │  4. Store in Registry
       │                     │
       │  5. Return AgentInfo│
       │◄────────────────────│
       │                     │
```

---

## 5. Agent 조회 플로우

### 5.1 K-Jarvis Frontend에서 Agent 목록 조회

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  K-Jarvis   │     │  K-Jarvis       │     │  Agent Catalog  │
│  Frontend   │     │  Orchestrator   │     │  Service        │
└──────┬──────┘     └────────┬────────┘     └────────┬────────┘
       │                     │                       │
       │  1. GET /api/agents │                       │
       │────────────────────►│                       │
       │                     │                       │
       │                     │  2. Return Agent List │
       │                     │  (from internal       │
       │                     │   registry)           │
       │                     │                       │
       │  3. Display Agents  │                       │
       │◄────────────────────│                       │
       │                     │                       │
```

### 5.2 MCPHub Frontend에서 Agent 카탈로그 조회

```
┌─────────────┐     ┌─────────────────┐
│  MCPHub     │     │  Agent Catalog  │
│  Frontend   │     │  Service        │
└──────┬──────┘     └────────┬────────┘
       │                     │
       │  1. GET /api/agents │
       │────────────────────►│
       │                     │
       │  2. Return Agent    │
       │     Catalog List    │
       │◄────────────────────│
       │                     │
       │  3. Display Agent   │
       │     Catalog UI      │
       │                     │
```

---

## 6. Agent 헬스체크 플로우

Agent Catalog Service는 60초 간격으로 등록된 모든 Agent의 상태를 확인합니다.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Agent Catalog  │     │   AI Agent 1    │     │   AI Agent 2    │
│  Service        │     │   (GitHub)      │     │   (Jira)        │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │  [Every 60 seconds]   │                       │
         │                       │                       │
         │  1. GET /.well-known/agent.json               │
         │──────────────────────►│                       │
         │                       │                       │
         │  2. 200 OK            │                       │
         │◄──────────────────────│                       │
         │                       │                       │
         │  3. Update status:    │                       │
         │     ONLINE            │                       │
         │                       │                       │
         │  4. GET /.well-known/agent.json               │
         │──────────────────────────────────────────────►│
         │                       │                       │
         │  5. Connection Failed │                       │
         │◄ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
         │                       │                       │
         │  6. Check last_seen   │                       │
         │     > 180s? → OFFLINE │                       │
         │                       │                       │
```

### 헬스체크 로직

```python
async def check_agent_health(self, agent: AgentInfo) -> bool:
    try:
        # 1. /.well-known/agent.json 시도
        response = await client.get(f"{agent.url}/.well-known/agent.json")
        if response.status_code == 200:
            agent.status = AgentStatus.ONLINE
            agent.last_seen = datetime.utcnow()
            return True
        
        # 2. /health 엔드포인트 시도
        response = await client.get(f"{agent.url}/health")
        if response.status_code == 200:
            agent.status = AgentStatus.ONLINE
            agent.last_seen = datetime.utcnow()
            return True
            
    except Exception:
        pass
    
    # 3. 180초 이상 응답 없으면 OFFLINE
    if agent.last_seen < datetime.utcnow() - timedelta(seconds=180):
        agent.status = AgentStatus.OFFLINE
    
    return False
```

---

## 7. Agent 라우팅 플로우 (K-Jarvis Orchestrator)

사용자 메시지가 들어오면 Orchestrator가 적절한 Agent를 선택합니다.

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User      │     │  K-Jarvis       │     │   AI Agent      │
│             │     │  Orchestrator   │     │   (Selected)    │
└──────┬──────┘     └────────┬────────┘     └────────┬────────┘
       │                     │                       │
       │  1. "GitHub PR 보여줘"                      │
       │────────────────────►│                       │
       │                     │                       │
       │                     │  2. Analyze Message   │
       │                     │     - Keywords: github, PR
       │                     │     - Domain: development
       │                     │                       │
       │                     │  3. Search Agents     │
       │                     │     - Match routing.keywords
       │                     │     - Match routing.domain
       │                     │     - LLM fallback    │
       │                     │                       │
       │                     │  4. Select: GitHub Agent
       │                     │                       │
       │                     │  5. POST /a2a (SendMessage)
       │                     │──────────────────────►│
       │                     │                       │
       │                     │  6. Agent Response    │
       │                     │◄──────────────────────│
       │                     │                       │
       │  7. Return Response │                       │
       │◄────────────────────│                       │
       │                     │                       │
```

### 라우팅 우선순위

1. **키워드 매칭**: `routing.keywords`에 사용자 메시지 키워드 포함 여부
2. **도메인 매칭**: `routing.domain` 일치 여부
3. **RAG 기반 검색**: pgvector를 사용한 의미 기반 검색
4. **LLM 폴백**: 위 방법으로 결정 못하면 LLM이 판단

---

## 8. Agent 삭제 플로우

```
┌─────────────┐     ┌─────────────────┐
│   Admin     │     │  Agent Catalog  │
│   User      │     │  Service        │
└──────┬──────┘     └────────┬────────┘
       │                     │
       │  1. DELETE /api/agents/{agent_id}
       │────────────────────►│
       │                     │
       │                     │  2. Find Agent by ID
       │                     │
       │                     │  3. Remove from Registry
       │                     │
       │                     │  4. Stop Health Check
       │                     │
       │  5. Return Success  │
       │◄────────────────────│
       │                     │
```

---

## 9. 데이터 동기화 플로우

현재 Agent Catalog Service와 K-Jarvis Orchestrator는 각각 독립적인 Registry를 가지고 있습니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Current Architecture                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐       ┌─────────────────────┐          │
│  │  Agent Catalog      │       │  K-Jarvis           │          │
│  │  Service            │       │  Orchestrator       │          │
│  │                     │       │                     │          │
│  │  ┌───────────────┐  │       │  ┌───────────────┐  │          │
│  │  │ In-Memory     │  │       │  │ In-Memory     │  │          │
│  │  │ Registry      │  │       │  │ Registry      │  │          │
│  │  │               │  │       │  │               │  │          │
│  │  │ - GitHub      │  │       │  │ - GitHub      │  │          │
│  │  │ - Jira        │  │  ═══  │  │ - Jira        │  │          │
│  │  │ - Confluence  │  │ 동기화 │  │ - Confluence  │  │          │
│  │  │ - Sample      │  │ 필요  │  │ - Sample      │  │          │
│  │  └───────────────┘  │       │  └───────────────┘  │          │
│  └─────────────────────┘       └─────────────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 향후 개선 방안

1. **단일 소스 (Single Source of Truth)**: Agent Catalog Service를 유일한 Agent 저장소로 사용
2. **이벤트 기반 동기화**: Agent 등록/삭제 시 Webhook으로 Orchestrator에 알림
3. **PostgreSQL 영속화**: In-Memory 대신 DB 저장으로 재시작 시에도 데이터 유지

---

## 10. API 엔드포인트 요약

### Agent Catalog Service (Port: 8080)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 서비스 헬스체크 |
| GET | `/api/agents` | Agent 목록 조회 |
| GET | `/api/agents/search` | Agent 검색 |
| GET | `/api/agents/{id}` | Agent 상세 조회 |
| POST | `/api/agents/register` | Agent 등록 (직접) |
| POST | `/api/agents/register/url` | Agent 등록 (URL) |
| DELETE | `/api/agents/{id}` | Agent 삭제 |
| POST | `/api/agents/{id}/refresh` | Agent 정보 갱신 |
| POST | `/api/agents/{id}/health-check` | 헬스체크 트리거 |
| GET | `/api/stats` | 통계 조회 |

---

## 11. 실제 사용 예시

### Agent 등록

```bash
# URL 기반 등록 (권장)
curl -X POST http://localhost:8080/api/agents/register/url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://kjarvis-github-agent:5012"}'

# 직접 등록
curl -X POST http://localhost:8080/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Custom Agent",
    "description": "Custom AI Agent",
    "url": "http://my-agent:5000",
    "version": "1.0.0",
    "skills": [
      {"id": "skill1", "name": "do_something", "description": "Does something"}
    ]
  }'
```

### Agent 조회

```bash
# 전체 목록
curl http://localhost:8080/api/agents

# 오프라인 포함
curl "http://localhost:8080/api/agents?include_offline=true"

# 검색
curl "http://localhost:8080/api/agents/search?q=github"

# 통계
curl http://localhost:8080/api/stats
```

---

## 12. 결론

Agent Card 관리 시스템은 K-Jarvis 생태계의 핵심 인프라로서:

1. **표준화**: A2A 프로토콜 기반의 표준화된 Agent 메타데이터 관리
2. **자동 발견**: URL만으로 Agent 정보를 자동으로 가져오는 A2A Discovery
3. **헬스 모니터링**: 60초 간격의 자동 헬스체크로 Agent 상태 실시간 파악
4. **확장성**: MCPHub, Orchestrator 등 다양한 서비스에서 활용 가능

이를 통해 개발자들은 Agent 개발에만 집중하고, 플랫폼 연동은 표준화된 방식으로 자동화할 수 있습니다.

