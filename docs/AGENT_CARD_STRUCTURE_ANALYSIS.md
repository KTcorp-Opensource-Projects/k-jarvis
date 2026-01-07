# Agent Card 구조 상세 분석 보고서

## 📋 분석 개요

현재 K-Jarvis Agent Catalog Service의 Agent Card 구조를 Google A2A 공식 스펙과 비교하여 향후 발생할 수 있는 문제점을 분석합니다.

---

## 1. 현재 구조 vs A2A 표준 비교

### 1.1 현재 K-Jarvis Agent Card 구조

```python
class AgentCard(BaseModel):
    protocolVersion: str = "0.3.0"
    name: str
    description: str
    url: Optional[str] = None
    version: str = "1.0.0"
    skills: List[AgentSkill] = []
    capabilities: Dict[str, Any] = {...}
    requirements: AgentRequirements  # 커스텀 필드
    routing: Optional[AgentRoutingInfo] = None  # 커스텀 필드
    defaultInputModes: List[str] = ["text/plain"]
    defaultOutputModes: List[str] = ["text/plain"]
```

### 1.2 Google A2A 표준 Agent Card 구조

```json
{
  "protocolVersion": "0.3.0",
  "name": "...",
  "description": "...",
  "url": "...",
  "preferredTransport": "JSONRPC",
  "additionalInterfaces": [...],
  "provider": {
    "organization": "...",
    "url": "..."
  },
  "capabilities": {...},
  "securitySchemes": {...},
  "security": [...],
  "defaultInputModes": [...],
  "defaultOutputModes": [...],
  "skills": [...],
  "supportsAuthenticatedExtendedCard": true
}
```

---

## 2. 🚨 심각도별 문제점 분석

### 2.1 🔴 심각 (Critical) - 즉시 해결 필요

#### 문제 1: 보안 스키마 미구현 (`securitySchemes`, `security`)

| 항목 | 현재 상태 | A2A 표준 |
|------|----------|---------|
| securitySchemes | ❌ 없음 | ✅ 필수 |
| security | ❌ 없음 | ✅ 필수 |

**영향:**
- 외부 개발자가 Agent를 개발할 때 인증 방식을 알 수 없음
- K-Auth와의 통합 정보 제공 불가
- 보안 감사 시 문제 발생 가능

**해결 방안:**
```python
class SecurityScheme(BaseModel):
    type: str  # "openIdConnect", "oauth2", "apiKey", "http"
    openIdConnectUrl: Optional[str] = None
    flows: Optional[Dict] = None  # OAuth2 flows
    scheme: Optional[str] = None  # "bearer", "basic"
    bearerFormat: Optional[str] = None
    in_: Optional[str] = None  # "header", "query" (for apiKey)
    name: Optional[str] = None  # header/query param name

class AgentCard(BaseModel):
    # ... 기존 필드
    securitySchemes: Dict[str, SecurityScheme] = {}
    security: List[Dict[str, List[str]]] = []
```

---

#### 문제 2: Provider 정보 누락

| 항목 | 현재 상태 | A2A 표준 |
|------|----------|---------|
| provider.organization | ❌ 없음 | ✅ 권장 |
| provider.url | ❌ 없음 | ✅ 권장 |

**영향:**
- Agent 제공자 식별 불가
- 신뢰성 검증 어려움
- 에이전트 마켓플레이스 구축 시 필수 정보 부재

**해결 방안:**
```python
class AgentProvider(BaseModel):
    organization: str
    url: Optional[str] = None
    email: Optional[str] = None

class AgentCard(BaseModel):
    # ... 기존 필드
    provider: Optional[AgentProvider] = None
```

---

### 2.2 🟠 높음 (High) - 빠른 시일 내 해결 권장

#### 문제 3: Transport 정보 누락

| 항목 | 현재 상태 | A2A 표준 |
|------|----------|---------|
| preferredTransport | ❌ 없음 | ✅ 선택 |
| additionalInterfaces | ❌ 없음 | ✅ 선택 |

**영향:**
- 다중 프로토콜 지원 불가 (JSON-RPC, gRPC, HTTP+JSON)
- 향후 gRPC 등 추가 시 구조 변경 필요

**해결 방안:**
```python
class AgentInterface(BaseModel):
    url: str
    transport: str  # "JSONRPC", "GRPC", "HTTP+JSON"

class AgentCard(BaseModel):
    # ... 기존 필드
    preferredTransport: str = "JSONRPC"
    additionalInterfaces: List[AgentInterface] = []
```

---

#### 문제 4: In-Memory 저장소 (데이터 영속성)

| 항목 | 현재 상태 | 권장 |
|------|----------|------|
| 저장소 | In-Memory Dict | PostgreSQL |
| 서버 재시작 시 | ❌ 데이터 손실 | ✅ 데이터 유지 |

**영향:**
- 서버 재시작 시 모든 Agent 등록 정보 손실
- 스케일 아웃 시 인스턴스 간 데이터 불일치
- 프로덕션 환경 부적합

**해결 방안:**
```python
# PostgreSQL 테이블 추가
CREATE TABLE agent_cards (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL UNIQUE,
    version VARCHAR(50),
    card_json JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'unknown',
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agent_cards_url ON agent_cards(url);
CREATE INDEX idx_agent_cards_status ON agent_cards(status);
```

---

### 2.3 🟡 중간 (Medium) - 계획적으로 해결

#### 문제 5: 커스텀 필드 (`requirements`, `routing`)

| 필드 | 상태 | 설명 |
|------|------|------|
| requirements | K-Jarvis 전용 | MCPHub 토큰 요구사항 |
| routing | K-Jarvis 전용 | 라우팅 메타데이터 |

**영향:**
- A2A 표준 호환성 저하
- 외부 A2A 에이전트와 상호운용 시 무시될 수 있음

**권장 방안:**
- `x-kjarvis-requirements`, `x-kjarvis-routing`으로 네이밍 변경 (확장 필드 명시)
- 또는 `extensions` 필드 내에 배치

```python
class AgentCard(BaseModel):
    # A2A 표준 필드들
    ...
    # K-Jarvis 확장 필드
    extensions: Dict[str, Any] = {
        "x-kjarvis-requirements": {...},
        "x-kjarvis-routing": {...}
    }
```

---

#### 문제 6: Skill ID 자동 생성 미지원

| 항목 | 현재 상태 | 권장 |
|------|----------|------|
| skill.id | 빈 문자열 허용 | UUID 자동 생성 |

**영향:**
- 동일 이름의 Skill 구분 불가
- Skill 참조 시 문제 발생 가능

**해결 방안:**
```python
class AgentSkill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # ...
```

---

#### 문제 7: 인증된 확장 카드 미지원

| 항목 | 현재 상태 | A2A 표준 |
|------|----------|---------|
| supportsAuthenticatedExtendedCard | ❌ 없음 | ✅ 선택 |
| agent/getAuthenticatedExtendedCard | ❌ 미구현 | ✅ 선택 |

**영향:**
- 인증 후 추가 정보 제공 불가
- 비공개 Skill 노출 제어 불가

---

### 2.4 🟢 낮음 (Low) - 향후 개선 고려

#### 문제 8: 버전 관리 전략 부재

| 항목 | 현재 상태 | 권장 |
|------|----------|------|
| 버전 이력 | ❌ 없음 | 버전별 카드 저장 |
| 하위 호환성 | 미정의 | 마이그레이션 전략 필요 |

**영향:**
- Agent Card 스펙 변경 시 기존 데이터 마이그레이션 어려움
- 롤백 불가

---

#### 문제 9: Rate Limiting / Quota 정보 없음

| 항목 | 현재 상태 | 권장 |
|------|----------|------|
| rateLimit | ❌ 없음 | 추가 권장 |
| quotas | ❌ 없음 | 추가 권장 |

**영향:**
- 클라이언트가 Agent 호출 제한을 알 수 없음
- 과부하 방지 어려움

---

## 3. 📊 문제점 요약 매트릭스

| # | 문제 | 심각도 | 영향도 | 해결 난이도 | 우선순위 |
|---|------|--------|--------|------------|---------|
| 1 | 보안 스키마 미구현 | 🔴 Critical | 높음 | 중간 | **P0** |
| 2 | Provider 정보 누락 | 🔴 Critical | 중간 | 낮음 | **P0** |
| 3 | Transport 정보 누락 | 🟠 High | 중간 | 낮음 | **P1** |
| 4 | In-Memory 저장소 | 🟠 High | 높음 | 높음 | **P1** |
| 5 | 커스텀 필드 네이밍 | 🟡 Medium | 낮음 | 낮음 | **P2** |
| 6 | Skill ID 자동 생성 | 🟡 Medium | 낮음 | 낮음 | **P2** |
| 7 | 인증 확장 카드 | 🟡 Medium | 중간 | 중간 | **P2** |
| 8 | 버전 관리 전략 | 🟢 Low | 중간 | 중간 | **P3** |
| 9 | Rate Limiting | 🟢 Low | 낮음 | 낮음 | **P3** |

---

## 4. 🛠️ 권장 해결 로드맵

### Phase 1: 즉시 (1주일 내)
- [ ] `securitySchemes`, `security` 필드 추가
- [ ] `provider` 필드 추가
- [ ] Skill ID 자동 생성 로직 추가

### Phase 2: 단기 (2-3주)
- [ ] PostgreSQL 영속화 구현
- [ ] `preferredTransport`, `additionalInterfaces` 추가
- [ ] 커스텀 필드 `x-kjarvis-*` 네이밍 변경

### Phase 3: 중기 (1-2개월)
- [ ] 인증된 확장 카드 API 구현
- [ ] 버전 관리 시스템 구축
- [ ] Rate Limiting 정보 추가

---

## 5. 📝 개선된 Agent Card 구조 제안

```python
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class SecuritySchemeType(str, Enum):
    OPENID_CONNECT = "openIdConnect"
    OAUTH2 = "oauth2"
    API_KEY = "apiKey"
    HTTP = "http"


class SecurityScheme(BaseModel):
    """A2A 표준 보안 스키마"""
    type: SecuritySchemeType
    openIdConnectUrl: Optional[str] = None
    flows: Optional[Dict[str, Any]] = None
    scheme: Optional[str] = None  # "bearer", "basic"
    bearerFormat: Optional[str] = None
    in_: Optional[str] = Field(None, alias="in")  # "header", "query"
    name: Optional[str] = None


class AgentProvider(BaseModel):
    """Agent 제공자 정보"""
    organization: str
    url: Optional[str] = None
    email: Optional[str] = None


class AgentInterface(BaseModel):
    """추가 인터페이스"""
    url: str
    transport: str  # "JSONRPC", "GRPC", "HTTP+JSON"


class AgentSkill(BaseModel):
    """Agent Skill - A2A 표준 준수"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    tags: List[str] = []
    examples: List[str] = []
    inputModes: List[str] = ["text/plain"]
    outputModes: List[str] = ["text/plain"]


class AgentCapabilities(BaseModel):
    """Agent 기능"""
    streaming: bool = True
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


class KJarvisExtensions(BaseModel):
    """K-Jarvis 플랫폼 전용 확장 필드"""
    requirements: Dict[str, Any] = {
        "mcpHubToken": False,
        "mcpServers": []
    }
    routing: Dict[str, Any] = {
        "domain": "general",
        "category": "",
        "keywords": [],
        "capabilities": []
    }


class AgentCard(BaseModel):
    """A2A 표준 + K-Jarvis 확장 Agent Card"""
    
    # === A2A 표준 필드 ===
    protocolVersion: str = "0.3.0"
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    
    # Provider 정보 (A2A 표준)
    provider: Optional[AgentProvider] = None
    
    # Transport 정보 (A2A 표준)
    preferredTransport: str = "JSONRPC"
    additionalInterfaces: List[AgentInterface] = []
    
    # 기능 (A2A 표준)
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    
    # 보안 (A2A 표준) - 중요!
    securitySchemes: Dict[str, SecurityScheme] = {}
    security: List[Dict[str, List[str]]] = []
    
    # 입출력 모드 (A2A 표준)
    defaultInputModes: List[str] = ["text/plain"]
    defaultOutputModes: List[str] = ["text/plain"]
    
    # Skills (A2A 표준)
    skills: List[AgentSkill] = []
    
    # 인증 확장 카드 지원 (A2A 표준)
    supportsAuthenticatedExtendedCard: bool = False
    
    # === K-Jarvis 확장 필드 ===
    extensions: KJarvisExtensions = Field(
        default_factory=KJarvisExtensions,
        description="K-Jarvis 플랫폼 전용 확장 필드"
    )
    
    class Config:
        # 알 수 없는 필드 허용 (향후 확장성)
        extra = "allow"
```

---

## 6. 결론

### 현재 구조의 전체 평가: ⚠️ **60점 / 100점**

| 영역 | 점수 | 설명 |
|------|------|------|
| A2A 호환성 | 65/100 | 핵심 필드는 있으나 보안/Provider 누락 |
| 확장성 | 70/100 | 커스텀 필드 있으나 네이밍 비표준 |
| 운영 안정성 | 40/100 | In-Memory 저장소로 프로덕션 부적합 |
| 보안 | 50/100 | securitySchemes 미구현 |

### 핵심 권장사항

1. **즉시**: `securitySchemes`, `security`, `provider` 필드 추가
2. **단기**: PostgreSQL 영속화로 전환
3. **중기**: 인증 확장 카드 및 버전 관리 구현

이러한 개선을 통해 K-Jarvis Agent Card는 A2A 표준 완전 호환 + 플랫폼 확장이 가능한 구조로 발전할 수 있습니다.

