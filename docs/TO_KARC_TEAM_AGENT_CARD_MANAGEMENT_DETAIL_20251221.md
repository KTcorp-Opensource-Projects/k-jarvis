# Agent Card 관리 상세 가이드 - K-ARC AgentHub 포팅용

**작성일**: 2025-12-21  
**작성팀**: Orchestrator Team  
**대상**: K-ARC (MCPHub) Team  
**목적**: AgentHub 포팅을 위한 Agent Card 관리 방식 상세 설명

---

## 📊 현재 Orchestrator의 Agent Card 관리 구조

### 1. 핵심 데이터 모델

#### AgentCard (A2A 표준)
```python
# backend/app/models.py

class AgentCard(BaseModel):
    """A2A Agent Card - describes agent capabilities"""
    protocolVersion: str = "0.3.0"
    name: str
    description: str
    url: Optional[str] = None
    version: str = "1.0.0"
    skills: List[AgentSkill] = []
    capabilities: Dict[str, Any] = {
        "streaming": True,
        "pushNotifications": False,
        "stateTransitionHistory": False
    }
    requirements: AgentRequirements = Field(default_factory=AgentRequirements)
    routing: Optional[AgentRoutingInfo] = None  # 라우팅 메타데이터
    defaultInputModes: List[str] = ["text/plain"]
    defaultOutputModes: List[str] = ["text/plain"]
    # LangGraph 에이전트 지원
    protocol: Optional[str] = None
    endpoints: Optional[Dict[str, str]] = None
    provider: Optional[Dict[str, str]] = None
```

#### AgentSkill (기술/기능 정의)
```python
class AgentSkill(BaseModel):
    """Agent skill definition - A2A Spec compliant"""
    id: str = ""
    name: str
    description: str
    tags: List[str] = []
    examples: List[str] = []
    inputModes: List[str] = ["text/plain"]
    outputModes: List[str] = ["text/plain"]
```

#### AgentRequirements (MCPHub 토큰 요구사항)
```python
class AgentRequirements(BaseModel):
    """Agent requirements - MCPHub 토큰 등 필요 사항"""
    mcpHubToken: bool = False  # MCPHub 토큰 필요 여부
    mcpServers: List[str] = []  # 필요한 MCP 서버 목록
```

#### AgentRoutingInfo (라우팅 메타데이터)
```python
class AgentRoutingInfo(BaseModel):
    """Agent routing metadata for intelligent routing"""
    domain: str = "general"  # 도메인: project_management, documentation 등
    category: str = ""       # 카테고리: jira, confluence, slack 등
    keywords: List[str] = [] # 라우팅 키워드 (한/영)
    capabilities: List[str] = [] # 지원 기능: search, create, update 등
```

---

## 🔄 Agent Card 등록 플로우

### 방법 1: URL 기반 자동 등록 (A2A Discovery) - **권장**

```
관리자: POST /api/agents/register/url
    { "url": "http://agent-server:5010" }
           ↓
Orchestrator: GET http://agent-server:5010/.well-known/agent.json
           ↓
Agent Server: AgentCard JSON 응답
           ↓
Orchestrator:
    1. AgentCard 파싱
    2. AgentInfo 객체 생성
    3. In-Memory Registry에 저장
    4. Vector Store에 동기화 (RAG 라우팅용)
           ↓
관리자: 등록 완료 응답
```

#### 코드 (registry.py)
```python
async def register_agent_by_url(self, url: str) -> AgentInfo:
    """
    Register an agent by fetching its Agent Card from URL (A2A Discovery).
    This is the A2A standard way to discover and register agents.
    """
    # 1. Agent Card 가져오기
    card = await self._fetch_agent_card(url)
    if not card:
        raise Exception(f"Failed to fetch Agent Card from {url}")
    
    # 2. AgentInfo 생성
    agent = AgentInfo(
        name=card.name,
        description=card.description,
        url=url,
        version=card.version,
        skills=card.skills,
        capabilities=card.capabilities,
        requirements=card.requirements,  # MCPHub 토큰 요구사항
        status=AgentStatus.ONLINE,
        last_seen=datetime.utcnow()
    )
    
    # 3. Registry에 저장
    self._agents[agent.id] = agent
    self._metrics[agent.id] = AgentMetrics()
    
    # 4. Vector Store 동기화 (RAG 라우팅용)
    asyncio.create_task(self._sync_to_vector_store(agent, card))
    
    return agent
```

### 방법 2: 수동 등록

```
관리자: POST /api/agents/register
    {
        "name": "Sample AI Agent",
        "description": "문서 관리를 위한 AI 에이전트",
        "url": "http://agent-server:5020",
        "version": "2.0.0",
        "skills": [...],
        "capabilities": {...}
    }
           ↓
Orchestrator: AgentInfo 생성 및 저장
```

---

## 💾 저장소 구조

### 1. In-Memory Registry (실시간 관리)

```python
# registry.py
class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}      # agent_id → AgentInfo
        self._metrics: Dict[str, AgentMetrics] = {}  # agent_id → 성능 메트릭
```

**특징**:
- 빠른 조회 (O(1))
- 서버 재시작 시 데이터 손실 (현재는 DB 영속화 미구현)
- 헬스체크로 상태 자동 갱신

### 2. Vector Store (RAG 라우팅용)

```sql
-- PostgreSQL + pgvector
CREATE TABLE agent_routing_metadata (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(255) UNIQUE NOT NULL,
    agent_url VARCHAR(500) NOT NULL,
    domain VARCHAR(100) DEFAULT 'general',
    category VARCHAR(100),
    keywords TEXT[],
    capabilities TEXT[],
    description TEXT NOT NULL,
    description_embedding vector(1536),  -- OpenAI text-embedding-3-small
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**특징**:
- 영속적 저장
- 벡터 유사도 검색 (RAG 라우팅)
- 키워드 기반 검색

---

## 🔍 Agent Card 조회 API

### 전체 Agent 목록
```bash
GET /api/agents
Authorization: Bearer <token>

# 응답
[
    {
        "id": "uuid-1234",
        "name": "Confluence AI Agent",
        "description": "Confluence 문서 관리 에이전트",
        "url": "http://kjarvis-confluence-agent:5010",
        "version": "2.0.0",
        "skills": [...],
        "capabilities": {...},
        "requirements": {
            "mcpHubToken": true,
            "mcpServers": ["mcp-atlassian-confluence"]
        },
        "status": "online",
        "last_seen": "2025-12-21T10:30:00Z"
    },
    ...
]
```

### 개별 Agent 조회
```bash
GET /api/agents/{agent_id}
Authorization: Bearer <token>
```

### Agent 헬스 상태 (모니터링)
```bash
GET /api/agents/monitoring
Authorization: Bearer <token>

# 응답
{
    "summary": {
        "total_agents": 4,
        "online_agents": 3,
        "healthy_agents": 3,
        "offline_agents": 1
    },
    "agents": [
        {
            "id": "uuid-1234",
            "name": "Confluence AI Agent",
            "status": "online",
            "health": "healthy",
            "metrics": {
                "total_requests": 150,
                "success_rate": 98.5,
                "avg_response_time_ms": 450
            }
        },
        ...
    ]
}
```

---

## 🏗️ K-ARC AgentHub 포팅 제안

### 1. AgentHub 데이터 모델

```typescript
// K-ARC에서 구현할 Agent Card 스키마
interface AgentCard {
    id: string;
    name: string;
    description: string;
    url: string;
    version: string;
    skills: AgentSkill[];
    capabilities: {
        streaming: boolean;
        pushNotifications: boolean;
        stateTransitionHistory: boolean;
    };
    requirements: {
        mcpHubToken: boolean;
        mcpServers: string[];  // 필요한 MCP 서버 목록
    };
    routing: {
        domain: string;
        category: string;
        keywords: string[];
        capabilities: string[];
    };
    status: 'online' | 'offline' | 'busy' | 'error';
    lastSeen: Date;
    createdAt: Date;
    updatedAt: Date;
}

interface AgentSkill {
    id: string;
    name: string;
    description: string;
    tags: string[];
    examples: string[];
    inputModes: string[];
    outputModes: string[];
}
```

### 2. AgentHub API 설계 제안

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/agents` | GET | 전체 Agent 목록 조회 |
| `/api/agents/{id}` | GET | 개별 Agent 조회 |
| `/api/agents/register` | POST | Agent 수동 등록 |
| `/api/agents/register/url` | POST | URL 기반 자동 등록 |
| `/api/agents/{id}` | DELETE | Agent 삭제 |
| `/api/agents/{id}/refresh` | POST | Agent Card 갱신 |
| `/api/agents/search` | GET | Agent 검색 (키워드, 도메인) |

### 3. Agent Card 캐싱 전략

MCPHub의 MCP Server 도구 캐싱과 유사하게:

```typescript
// In-Memory 캐시
let agentInfos: AgentInfo[] = [];

// 초기화 시 DB에서 로드
export const initializeAgents = async (): Promise<AgentInfo[]> => {
    const agents = await AgentRepository.findAll({ where: { isActive: true } });
    
    for (const agent of agents) {
        // Agent Card 가져오기
        const card = await fetchAgentCard(agent.url);
        if (card) {
            agentInfos.push({
                ...agent,
                skills: card.skills,
                capabilities: card.capabilities,
                status: 'connected'
            });
        }
    }
    
    return agentInfos;
};
```

### 4. Orchestrator 연동 방식

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Orchestrator  │────>│    K-ARC        │────>│   Agent Server  │
│   (라우팅 결정) │     │   (AgentHub)    │     │   (A2A 실행)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                      │                       │
         │  1. Agent 목록 조회  │                       │
         │  GET /api/agents     │                       │
         │<─────────────────────│                       │
         │                      │                       │
         │  2. 라우팅 결정      │                       │
         │  (자체 HybridRouter) │                       │
         │                      │                       │
         │  3. Agent 호출       │                       │
         │──────────────────────┼──────────────────────>│
         │                      │  POST /tasks/send     │
         │<─────────────────────┼───────────────────────│
         │                      │                       │
```

---

## 📋 K-ARC 구현 체크리스트

### Phase 1: 기본 CRUD
- [ ] `agents` 테이블 생성 (PostgreSQL)
- [ ] Agent CRUD API 구현
- [ ] Agent Card 조회 로직 구현

### Phase 2: A2A Discovery
- [ ] URL 기반 Agent Card 가져오기
- [ ] `/.well-known/agent.json` 파싱
- [ ] Agent 자동 등록 API

### Phase 3: 캐싱 & 헬스체크
- [ ] In-Memory 캐시 구현
- [ ] 주기적 헬스체크
- [ ] 상태 자동 갱신

### Phase 4: Orchestrator 연동
- [ ] Agent 목록 API 제공
- [ ] Orchestrator에서 K-ARC AgentHub 호출
- [ ] 통합 테스트

---

## 🔗 참고 자료

### 현재 Orchestrator 코드 위치
- `backend/app/models.py` - 데이터 모델
- `backend/app/registry.py` - Agent Registry 로직
- `backend/app/api.py` - API 엔드포인트
- `backend/app/agent_vector_store.py` - Vector Store
- `backend/app/hybrid_router.py` - RAG 라우팅

### A2A 프로토콜 참고
- Agent Card 위치: `/.well-known/agent.json` 또는 `/.well-known/agent-card.json`
- 필수 필드: `name`, `description`, `skills`, `capabilities`

---

## 📞 질문 & 협의

추가 질문이나 협의가 필요하시면 언제든 연락주세요.

- **담당자**: Orchestrator Team
- **Slack**: #k-jarvis-dev

---

**Orchestrator Team 드림**

