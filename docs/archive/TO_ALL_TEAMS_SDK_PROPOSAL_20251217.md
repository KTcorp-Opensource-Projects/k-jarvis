# K-Jarvis 에코시스템 SDK 개발 제안

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team  
**수신팀**: Agent Team, MCPHub Team (K-ARC)

---

## 🎯 제안 배경

### 현재 문제점

1. **Agent 개발 시 반복 작업**
   - 3개의 Agent(Confluence, Jira, GitHub)가 거의 동일한 `a2a_server.py` 코드 보유
   - A2A 프로토콜, Agent Card, 헤더 처리 등 500줄 이상의 보일러플레이트

2. **MCP 서버 개발 시 불명확한 가이드**
   - K-ARC와의 연동 방법이 문서로만 존재
   - 개발자가 직접 프로토콜 구현 필요

3. **거버넌스 적용의 어려움**
   - 문서만으로는 표준 준수 강제 불가
   - 팀별로 다른 구현 방식 존재

### 제안: K-Jarvis SDK 개발

**SDK를 사용하면:**
- ✅ 표준 준수가 자동으로 보장
- ✅ 개발 시간 80% 이상 단축
- ✅ 유지보수가 SDK 버전 업그레이드로 통합

---

## 📦 SDK 구성 제안

### 1. `k-jarvis-agent-sdk` (Python)

**목적**: K-Jarvis 오케스트레이터와 연동되는 AI Agent 개발 SDK

**설치 및 사용**:
```bash
pip install k-jarvis-agent-sdk
```

**Before (현재 방식) - 500줄 이상**:
```python
# a2a_server.py - 현재 각 Agent마다 작성하는 코드
from flask import Flask, request, jsonify, Response
import logging
import uuid
# ... 수많은 import

app = Flask(__name__)

# Agent Card 정의 (50줄)
AGENT_CARD = {
    "name": "My Agent",
    "description": "...",
    "protocolVersion": "0.3.0",
    "endpoints": { ... },
    "skills": [ ... ],
    # ... 많은 필드
}

# 헤더 추출 함수 (20줄)
def extract_request_headers():
    return {
        "X-Request-ID": request.headers.get("X-Request-ID", str(uuid.uuid4())),
        "X-MCPHub-User-Id": request.headers.get("X-MCPHub-User-Id"),
        # ...
    }

# 응답 생성 함수 (30줄)
def create_a2a_response(content, ...):
    # ...

# A2A 엔드포인트 (100줄)
@app.route("/a2a", methods=["POST"])
def a2a_endpoint():
    # JSON-RPC 처리
    # 스트리밍 처리
    # 에러 처리
    # ...

# Agent Card 엔드포인트 (20줄)
@app.route("/.well-known/agent.json")
def agent_card():
    return jsonify(AGENT_CARD)

# 헬스체크, 태스크 엔드포인트 등등...
```

**After (SDK 사용) - 50줄 이하**:
```python
from k_jarvis_agent_sdk import Agent, Skill, MCPClient

# 1. Agent 정의 (데코레이터 기반)
agent = Agent(
    name="My Custom Agent",
    description="내가 만든 커스텀 에이전트",
    version="1.0.0",
)

# 2. Skill 정의 (데코레이터 기반)
@agent.skill(
    name="search_data",
    description="데이터를 검색합니다",
    tags=["search", "data"],
)
async def search_data(query: str, user_id: str = None) -> str:
    """비즈니스 로직만 구현"""
    # user_id는 X-MCPHub-User-Id에서 자동 주입
    
    # MCP 호출 필요시
    async with MCPClient(user_id=user_id) as mcp:
        result = await mcp.call("my-mcp-server", "search", {"query": query})
    
    return f"검색 결과: {result}"

@agent.skill(name="create_item", description="아이템을 생성합니다")
async def create_item(title: str, content: str) -> dict:
    """비즈니스 로직만 구현"""
    return {"id": "123", "title": title}

# 3. 서버 실행
if __name__ == "__main__":
    agent.run(host="0.0.0.0", port=5020)
```

**SDK가 자동 처리하는 것들**:
- ✅ A2A 프로토콜 완벽 준수
- ✅ Agent Card 자동 생성 (`/.well-known/agent.json`)
- ✅ `/a2a` 엔드포인트 자동 구현
- ✅ `/tasks/send` 엔드포인트 자동 구현
- ✅ 스트리밍 응답 지원
- ✅ X-MCPHub-User-Id 헤더 자동 처리
- ✅ JSON-RPC 형식 자동 처리
- ✅ 에러 처리 및 로깅
- ✅ 헬스체크 엔드포인트

---

### 2. `k-arc-mcp-sdk` (Python/TypeScript)

**목적**: K-ARC에 등록되는 MCP 서버 개발 SDK

**Python 버전**:
```bash
pip install k-arc-mcp-sdk
```

```python
from k_arc_mcp_sdk import MCPServer, Tool

mcp = MCPServer(
    name="my-mcp-server",
    description="커스텀 MCP 서버",
    version="1.0.0",
)

@mcp.tool(
    name="get_weather",
    description="날씨 정보를 조회합니다",
    parameters={
        "city": {"type": "string", "description": "도시명"}
    }
)
async def get_weather(city: str, user_context: dict = None) -> dict:
    """비즈니스 로직만 구현"""
    # user_context에 K-ARC에서 전달된 서비스 토큰 포함
    return {"city": city, "temperature": 20}

if __name__ == "__main__":
    mcp.run(port=8080)
```

**TypeScript 버전**:
```bash
npm install @k-arc/mcp-sdk
```

```typescript
import { MCPServer, tool } from '@k-arc/mcp-sdk';

const server = new MCPServer({
  name: 'my-mcp-server',
  description: '커스텀 MCP 서버',
  version: '1.0.0',
});

server.addTool({
  name: 'get_weather',
  description: '날씨 정보를 조회합니다',
  parameters: {
    city: { type: 'string', description: '도시명' }
  },
  handler: async (params, userContext) => {
    return { city: params.city, temperature: 20 };
  }
});

server.listen(8080);
```

---

### 3. `k-jarvis-contracts` (공통 스키마)

**목적**: 팀 간 인터페이스 정의 및 자동 코드 생성

```
k-jarvis-contracts/
├── schemas/
│   ├── a2a-protocol.yaml      # A2A 프로토콜 스키마
│   ├── agent-card.yaml        # Agent Card 스키마
│   ├── mcp-protocol.yaml      # MCP 프로토콜 스키마
│   └── headers.yaml           # 공통 헤더 정의
├── generated/
│   ├── python/                # Python 클라이언트
│   └── typescript/            # TypeScript 클라이언트
└── tests/
    └── golden_files/          # Golden File 테스트
```

---

## 🏗️ SDK 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Developer Experience                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────┐       ┌─────────────────────┐              │
│  │ k-jarvis-agent-sdk  │       │   k-arc-mcp-sdk     │              │
│  │     (Python)        │       │ (Python/TypeScript) │              │
│  └──────────┬──────────┘       └──────────┬──────────┘              │
│             │                              │                         │
│             ▼                              ▼                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  k-jarvis-contracts (공통 스키마)              │   │
│  │  - A2A Protocol Schema    - MCP Protocol Schema              │   │
│  │  - Agent Card Schema      - Headers Schema                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                         Platform Layer                               │
│                                                                       │
│  ┌─────────────────────┐       ┌─────────────────────┐              │
│  │   K-Jarvis          │◄─────►│      K-ARC          │              │
│  │   Orchestrator      │       │   (ex-MCPHub)       │              │
│  └─────────────────────┘       └─────────────────────┘              │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 팀별 역할 분담 (안)

| 담당 영역 | Orchestrator Team | Agent Team | MCPHub (K-ARC) Team |
|----------|-------------------|------------|---------------------|
| **k-jarvis-contracts** | 스키마 관리, 코드 생성 | A2A 스키마 검토 | MCP 스키마 기여 |
| **k-jarvis-agent-sdk** | SDK 핵심 개발 | **실 사용 테스트, 피드백** | - |
| **k-arc-mcp-sdk** | 인터페이스 정의 | - | **SDK 핵심 개발** |
| **문서화** | 전체 가이드 | Agent 개발 가이드 | MCP 개발 가이드 |

---

## 🗓️ 제안 일정

### Phase 1: 설계 (12/18 - 12/20)
- [ ] 3팀 협의 (SDK 범위, 인터페이스 결정)
- [ ] k-jarvis-contracts 스키마 확정
- [ ] SDK API 설계 문서 작성

### Phase 2: 프로토타입 (12/21 - 12/25)
- [ ] k-jarvis-agent-sdk 프로토타입 (Orchestrator Team)
- [ ] k-arc-mcp-sdk 프로토타입 (K-ARC Team)
- [ ] 기존 Agent에 SDK 적용 테스트 (Agent Team)

### Phase 3: 안정화 (12/26 - 12/31)
- [ ] 피드백 반영 및 버그 수정
- [ ] 문서화 완료
- [ ] PyPI / npm 배포

---

## 💡 기대 효과

### 1. 개발 시간 단축

| 항목 | 현재 | SDK 사용 후 |
|------|------|------------|
| Agent 개발 | 3-5일 | **0.5-1일** |
| MCP 서버 개발 | 2-3일 | **몇 시간** |
| 거버넌스 검토 | 수동 체크 | **자동 보장** |

### 2. 코드 품질 향상

- **일관성**: 모든 Agent/MCP 서버가 동일한 패턴
- **보안**: SDK가 보안 베스트 프랙티스 자동 적용
- **테스트**: SDK 자체 테스트로 기본 품질 보장

### 3. 생태계 확장 용이

```
외부 개발자:
"K-Jarvis에 Agent 추가하고 싶어요"
→ pip install k-jarvis-agent-sdk
→ 50줄 코드 작성
→ 오케스트레이터에 등록 끝!
```

---

## 🔀 핵심 논의: SDK vs Builder vs 둘 다?

### Option A: SDK Only (라이브러리 방식)

```
개발자 → pip install k-jarvis-agent-sdk → 코드 작성 → 배포
```

**장점**:
- ✅ 완전한 커스터마이징 가능
- ✅ 기존 개발자에게 친숙
- ✅ 복잡한 비즈니스 로직 구현 가능

**단점**:
- ❌ 여전히 코딩 필요
- ❌ 비개발자는 사용 불가
- ❌ 학습 곡선 존재

**적합한 사용자**: 전문 개발자, 복잡한 Agent 개발

---

### Option B: Agent Builder (노코드/로우코드 플랫폼)

```
사용자 → K-Jarvis 웹 UI → 드래그앤드롭 → 배포
```

**예시 UI 컨셉**:
```
┌─────────────────────────────────────────────────────────────┐
│  🤖 K-Jarvis Agent Builder                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Agent 기본 정보]                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 이름: [My Custom Agent          ]                    │   │
│  │ 설명: [데이터 분석을 수행하는 에이전트]               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [Skills 정의]                     [+ 스킬 추가]           │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ 📊 analyze_data  │  │ 📈 generate_report│                │
│  │ MCP: data-server │  │ MCP: chart-server │                │
│  │ [편집] [삭제]    │  │ [편집] [삭제]     │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                             │
│  [MCP 서버 연결]                   [+ MCP 추가]            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ✅ data-server (연결됨)  │ ✅ chart-server (연결됨)  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  [프롬프트 템플릿]                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 당신은 데이터 분석 전문가입니다.                      │   │
│  │ 사용자의 요청에 따라 데이터를 분석하고...            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│          [테스트 실행]        [📦 배포]                     │
└─────────────────────────────────────────────────────────────┘
```

**장점**:
- ✅ 코딩 없이 Agent 생성
- ✅ 비개발자도 사용 가능
- ✅ 빠른 프로토타이핑
- ✅ 시각적 워크플로우

**단점**:
- ❌ 복잡한 로직 구현 제한
- ❌ 플랫폼 개발 비용 높음
- ❌ 커스터마이징 한계

**적합한 사용자**: 비개발자, 빠른 프로토타입, 단순 Agent

**참고 사례**:
- **Dify**: AI Agent 노코드 플랫폼
- **LangFlow/Flowise**: LangChain 노코드 빌더
- **n8n**: 워크플로우 자동화
- **Slack Workflow Builder**: 봇 노코드 생성

---

### Option C: SDK + Builder 하이브리드 ⭐ 권장

```
┌─────────────────────────────────────────────────────────────┐
│                      K-Jarvis Platform                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [비개발자/빠른 개발]              [전문 개발자]            │
│                                                             │
│  ┌───────────────────┐         ┌───────────────────┐       │
│  │  Agent Builder    │         │  Agent SDK        │       │
│  │  (Web UI)         │         │  (Python)         │       │
│  │                   │         │                   │       │
│  │  • 드래그앤드롭   │         │  • 전체 제어      │       │
│  │  • 템플릿 기반    │         │  • 복잡한 로직    │       │
│  │  • 노코드         │         │  • 코드 기반      │       │
│  └─────────┬─────────┘         └─────────┬─────────┘       │
│            │                             │                  │
│            ▼                             ▼                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         K-Jarvis Orchestrator (공통 런타임)          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌───────────────────┐         ┌───────────────────┐       │
│  │  MCP Builder      │         │  MCP SDK          │       │
│  │  (Web UI)         │         │  (Python/TS)      │       │
│  └─────────┬─────────┘         └─────────┬─────────┘       │
│            │                             │                  │
│            ▼                             ▼                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │             K-ARC (공통 MCP 게이트웨이)               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**장점**:
- ✅ 모든 사용자 커버
- ✅ 단계적 확장 가능 (SDK 먼저 → Builder 나중에)
- ✅ Builder로 생성한 Agent도 SDK로 Export 가능

**구현 전략**:
```
Phase 1 (지금): SDK 개발
Phase 2 (Q1 2025): Agent Builder 개발
Phase 3 (Q2 2025): MCP Builder 개발
```

---

## 🎯 구체적 논의 포인트

### 1. 어떤 옵션을 선택할 것인가?

| 옵션 | 구현 난이도 | 사용자 범위 | 권장 |
|------|------------|------------|------|
| A. SDK Only | 중간 | 개발자만 | |
| B. Builder Only | 높음 | 모두 | |
| **C. SDK 먼저 + Builder 나중** | 중간→높음 | 모두 | ⭐ |

### 2. SDK 세부 사항

| 질문 | 선택지 |
|------|--------|
| **언어** | Python만? Python + TypeScript? |
| **LangGraph 통합** | 직접 통합? 별도 플러그인? |
| **MCP 호환** | 표준 MCP 100% 호환? K-ARC 전용 확장? |
| **배포** | PyPI 공개? 내부 패키지? |

### 3. Builder 세부 사항 (Option C 선택 시)

| 질문 | 선택지 |
|------|--------|
| **호스팅** | K-Jarvis 내장? 별도 서비스? |
| **스토리지** | Agent 정의를 어디에 저장? |
| **런타임** | 서버리스? 컨테이너? |
| **Export** | Builder → SDK 코드 변환 가능? |

### 4. CLI 도구

```bash
# 프로젝트 생성
$ k-jarvis new my-agent
  ? Agent 타입: [Custom / 템플릿]
  ? MCP 연결: [예 / 아니오]
  ✔ 프로젝트 생성 완료!

# 로컬 테스트
$ k-jarvis dev
  🚀 Agent 실행 중: http://localhost:5020
  📋 Agent Card: http://localhost:5020/.well-known/agent.json

# 오케스트레이터 등록
$ k-jarvis deploy --orchestrator https://k-jarvis.example.com
  ✔ Agent 등록 완료!

# 테스트 실행
$ k-jarvis test
  ✔ A2A Protocol: PASS
  ✔ Agent Card: PASS
  ✔ Health Check: PASS
```

---

## ❓ 추가 논의 필요 사항

### 1. SDK 범위
- Agent SDK: 어디까지 추상화? (LangGraph 통합?)
- MCP SDK: 기존 MCP 스펙과의 호환성?

### 2. 기존 Agent 마이그레이션
- 현재 3개 Agent를 SDK 기반으로 전환?
- 점진적 마이그레이션 vs 일괄 전환?

### 3. 배포 및 버전 관리
- PyPI/npm 공개 배포 vs 내부 패키지?
- 버전 관리 정책?

### 4. 추가 기능
- CLI 도구 제공? (`k-jarvis init`, `k-jarvis test`)
- VS Code Extension?
- 템플릿 프로젝트?

---

## 📣 요청 사항

각 팀의 의견 및 피드백 부탁드립니다:

1. **SDK 개발에 동의하시나요?**
2. **팀별 역할 분담은 적절한가요?**
3. **추가로 SDK에 포함되어야 할 기능은?**
4. **일정은 현실적인가요?**

---

## 📎 참고

### 유사 SDK 사례
- **Slack SDK**: Slack 봇 개발 (Python, Node.js)
- **Stripe SDK**: 결제 연동 (다양한 언어)
- **LangChain**: LLM 애플리케이션 개발
- **Vercel AI SDK**: AI 앱 개발

### 현재 Agent 코드 분석
- `Confluence-AI-Agent/src/agent/a2a_server.py`: 540줄
- `Jira-AI-Agent/src/agent/a2a_server.py`: 500줄
- `GitHub-AI-Agent/src/agent/a2a_server.py`: 580줄
- **공통 코드**: 약 400줄 (75%)

**→ SDK로 400줄을 0줄로 줄일 수 있음!**

---

**Orchestrator Team** 🚀

