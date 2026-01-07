# K-Jarvis SDK 유지보수 리스크 분석

**작성일**: 2026-01-05  
**담당**: Orchestrator Team  
**상태**: 🔴 **핵심 고민 포인트**

---

## ⚠️ 핵심 문제

> **MCP와 A2A는 외부에서 관리되는 표준 프로토콜로, 버전이 지속적으로 업데이트됩니다.**
> **우리가 SDK를 만들면, 이 외부 스펙 변경에 따른 유지보수 부담이 발생합니다.**

---

## 📊 현재 상황 분석

### 1. MCP (Model Context Protocol) - Anthropic

| 항목 | 현황 |
|------|------|
| **관리 주체** | Anthropic |
| **현재 버전** | 2024-11-05 |
| **업데이트 주기** | 비정기 (주요 기능 추가 시) |
| **Breaking Changes** | 있음 (Stateless 전환 등) |
| **공식 SDK** | `@modelcontextprotocol/sdk` (TypeScript) |

**최근 주요 변경**:
- Stateless HTTP 지원 추가
- Streamable HTTP Transport
- 세션 관리 방식 변경

### 2. A2A (Agent-to-Agent) - Google

| 항목 | 현황 |
|------|------|
| **관리 주체** | Google |
| **현재 버전** | 0.3.0 (Draft) |
| **업데이트 주기** | 비정기 |
| **Breaking Changes** | 가능성 높음 (Draft 상태) |
| **공식 SDK** | 없음 (스펙만 제공) |

**최근 주요 변경**:
- PascalCase 메서드명 표준화
- 응답 구조 변경 (`result.message` vs `result.artifacts`)
- Part 구조 단순화

---

## 🔴 리스크 분석

### 리스크 1: 외부 스펙 변경 추적 부담

```
[외부 스펙 변경]
     ↓
[우리 SDK 수정 필요]
     ↓
[테스트/검증]
     ↓
[SDK 배포]
     ↓
[사용자 마이그레이션 안내]
```

**문제점**:
- Anthropic/Google이 스펙을 변경하면 우리가 따라가야 함
- 변경 사항 모니터링 인력 필요
- Breaking Change 시 대규모 수정 필요

### 리스크 2: 버전 호환성 관리

| 시나리오 | 영향 |
|----------|------|
| MCP 2024-11-05 → 2025-xx-xx | SDK 전체 리팩토링 가능성 |
| A2A 0.3.0 → 1.0.0 (정식) | 메서드/응답 구조 변경 가능성 |
| 동시 변경 | 복합적 수정 필요 |

### 리스크 3: 유지보수 인력/비용

| 항목 | 예상 공수 |
|------|----------|
| 스펙 변경 모니터링 | 주 2시간 |
| 변경 분석 및 설계 | 변경당 1-2일 |
| SDK 수정 및 테스트 | 변경당 3-5일 |
| 문서 업데이트 | 변경당 1일 |
| 사용자 마이그레이션 지원 | 변경당 1주 |

---

## 🤔 대안 비교

### Option A: Full SDK 개발 (현재 제안)

```
장점:
- 개발자 경험 최상
- 거버넌스 강제 적용
- 일관된 코드 품질

단점:
- 유지보수 부담 큼
- 외부 스펙 변경 시 대응 필요
- 인력/비용 지속 투입
```

### Option B: Thin Wrapper만 제공

```
장점:
- 유지보수 부담 최소
- 외부 스펙 변경에 유연

단점:
- 개발자가 스펙 학습 필요
- 거버넌스 강제 어려움
- 코드 품질 편차
```

### Option C: SDK 없이 가이드/템플릿만 제공

```
장점:
- 유지보수 부담 없음
- 외부 스펙 변경에 영향 없음

단점:
- 개발자 진입 장벽 높음
- 거버넌스 준수 어려움
- 생태계 확장 느림
```

### Option D: 하이브리드 접근 (권장)

```
Core (최소 유지보수):
- 공식 SDK 그대로 사용 (MCP SDK, A2A 없으면 직접 JSON-RPC)
- 우리는 "플러그인/확장" 형태로만 제공

Extension (우리 거버넌스):
- K-Auth 연동 헬퍼
- MCPHub 토큰 관리
- Agent Card 생성/검증
- 로깅/모니터링 표준화

이점:
- 외부 스펙 변경 시 Core는 공식 SDK가 처리
- 우리는 Extension만 유지보수
- 거버넌스는 Extension에서 적용
```

---

## 📋 Option D 상세 설계

### 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                  개발자 코드                          │
├─────────────────────────────────────────────────────┤
│  k-jarvis-extensions  │  k-arc-extensions           │
│  ├─ K-Auth Helper     │  ├─ Token Manager           │
│  ├─ Agent Card Gen    │  ├─ Catalog Helper          │
│  ├─ Logging Standard  │  ├─ Health Check            │
│  └─ Error Handler     │  └─ Error Handler           │
├─────────────────────────────────────────────────────┤
│  @modelcontextprotocol/sdk  │  직접 JSON-RPC (A2A)  │
│  (Anthropic 공식)           │  (우리가 최소 래핑)    │
└─────────────────────────────────────────────────────┘
```

### 유지보수 범위 비교

| 영역 | Full SDK | Option D (하이브리드) |
|------|----------|----------------------|
| MCP 프로토콜 | 우리가 유지보수 | Anthropic SDK 사용 |
| A2A 프로토콜 | 우리가 유지보수 | 최소 래퍼 (메서드 호출만) |
| K-Auth 연동 | 우리가 유지보수 | 우리가 유지보수 |
| MCPHub 연동 | 우리가 유지보수 | 우리가 유지보수 |
| 거버넌스 도구 | 우리가 유지보수 | 우리가 유지보수 |

### 구현 예시

```python
# k-jarvis-extensions (Agent 개발용)

# 공식 SDK나 표준 라이브러리를 그대로 사용
# 우리는 "확장"만 제공

from k_jarvis_extensions import (
    KAuthClient,        # K-Auth JWT 검증
    MCPHubHelper,       # MCPHub 토큰 관리
    AgentCardGenerator, # Agent Card 생성
    StandardLogger,     # 로깅 표준화
    ErrorHandler        # 에러 처리 표준화
)

# Agent 개발자는 A2A 스펙을 직접 따르되,
# 우리 확장 도구를 사용하여 K-Jarvis 거버넌스 준수

class MyAgent:
    def __init__(self):
        self.kauth = KAuthClient()
        self.mcphub = MCPHubHelper()
        self.logger = StandardLogger("my-agent")
    
    async def handle_request(self, request):
        # JWT 검증 (우리 확장)
        user = await self.kauth.verify_token(request.headers)
        
        # 비즈니스 로직 (개발자 구현)
        result = await self.process(request)
        
        # 표준 응답 생성 (A2A 스펙 직접 따름)
        return {
            "jsonrpc": "2.0",
            "result": {
                "message": {
                    "role": "agent",
                    "parts": [{"text": result}]
                }
            }
        }
```

```typescript
// k-arc-extensions (MCP Server 개발용)

import { Server } from "@modelcontextprotocol/sdk/server";  // 공식 SDK
import { TokenManager, CatalogHelper } from "@k-arc/extensions";  // 우리 확장

const server = new Server({
  name: "my-server",
  version: "1.0.0"
}, {
  capabilities: { tools: {} }
});

// 공식 SDK의 tool 등록 방식 그대로 사용
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: [...] };
});

// 우리 확장: 토큰 관리
const tokenManager = new TokenManager();

server.setRequestHandler(CallToolRequestSchema, async (request, extra) => {
  // 사용자 토큰 자동 주입 (우리 확장)
  const token = await tokenManager.getServiceToken(
    extra.headers?.["x-mcphub-user-id"],
    "JIRA_TOKEN"
  );
  
  // 비즈니스 로직
  const result = await callExternalAPI(token);
  
  return { content: [{ type: "text", text: result }] };
});
```

---

## ✅ 권장 사항

### 1. Option D (하이브리드) 채택

| 이유 | 설명 |
|------|------|
| **유지보수 최소화** | 외부 스펙 변경은 공식 SDK가 처리 |
| **거버넌스 유지** | Extension에서 우리 규칙 적용 |
| **유연성** | 개발자가 필요한 확장만 선택 사용 |
| **리스크 분산** | 프로토콜 유지보수 부담 외부로 |

### 2. 제공할 Extensions 범위

| Extension | 설명 | 우선순위 |
|-----------|------|----------|
| `k-auth-helper` | JWT 검증, SSO 연동 | 🔴 필수 |
| `mcphub-helper` | 토큰 관리, User-Context | 🔴 필수 |
| `agent-card-tools` | 생성, 검증, 등록 | 🔴 필수 |
| `standard-logger` | 로깅 표준화 | 🟡 권장 |
| `error-handler` | 에러 코드 표준화 | 🟡 권장 |
| `health-check` | 헬스체크 표준화 | 🟢 선택 |

### 3. 버전 관리 전략

```
k-jarvis-extensions v1.x.x
├─ 호환: MCP 2024-11-05, A2A 0.3.x
└─ K-Jarvis Platform v1.x

k-jarvis-extensions v2.x.x (미래)
├─ 호환: MCP 2025-xx-xx, A2A 1.x
└─ K-Jarvis Platform v2.x
```

### 4. 외부 스펙 변경 대응 프로세스

```
1. 모니터링: MCP/A2A 릴리즈 노트 주기적 확인
2. 분석: Breaking Change 여부 판단
3. 대응:
   - Non-Breaking: Extension 호환성 테스트만
   - Breaking: Extension 수정 + 마이그레이션 가이드
4. 공지: 개발자에게 변경 사항 안내
```

---

## 📝 결론

| 항목 | 결정 |
|------|------|
| SDK 전략 | **Option D: 하이브리드 (Extensions만 제공)** |
| MCP | 공식 SDK 사용 (`@modelcontextprotocol/sdk`) |
| A2A | 최소 래퍼 또는 직접 JSON-RPC |
| 우리 역할 | K-Jarvis 거버넌스 Extensions 제공 |
| 유지보수 범위 | Extensions만 (프로토콜 제외) |

**이 전략으로 외부 스펙 변경 리스크를 최소화하면서 거버넌스를 유지할 수 있습니다.**

---

## 📞 논의 필요

각 팀에 이 분석을 공유하고 의견을 받아야 합니다:

1. **MCPHub Team**: `@modelcontextprotocol/sdk` 직접 사용 + Extensions 방식 동의 여부
2. **Agent Team**: A2A 최소 래퍼 + Extensions 방식 동의 여부
3. **전체**: Extensions 범위 및 우선순위 합의


