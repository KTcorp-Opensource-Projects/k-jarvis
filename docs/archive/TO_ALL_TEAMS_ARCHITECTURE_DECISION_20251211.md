# [응답] 아키텍처 검토 피드백에 대한 결정 및 구현 시작

**발신**: MCPHub팀  
**수신**: Orchestrator팀, Agent팀  
**작성일**: 2025-12-11  
**유형**: ✅ 결정 및 구현 시작

---

## 1. 피드백 요약 및 결정

### 1.1 Orchestrator팀 피드백 → MCPHub 결정

| # | 피드백 | MCPHub 결정 |
|:-:|-------|:----------:|
| 1 | 우선순위 조정: 에러처리 → 서버필터링 → 포털 | ✅ 동의 |
| 2 | Agent별 MCPHub Key 분리 - MVP에서 우선순위 낮음 | ✅ 동의 (Phase 2로 이동) |
| 3 | MCPHub 포털 UI - MVP 이후로 연기 | ✅ 동의 |
| 4 | portal_url - 포털 개발 후 추가 | ✅ 동의 |

### 1.2 Agent팀 피드백 → MCPHub 결정

| # | 피드백 | MCPHub 결정 |
|:-:|-------|:----------:|
| 1 | Agent별 전용 MCPHub Key 발급 요청 | ✅ Phase 2에서 발급 예정 |
| 2 | allowedServers 여러 개 지정 가능 여부 | ✅ 가능 |
| 3 | 토큰 에러 시 retry 정책 | ✅ retry 불필요, 바로 사용자 안내 |

---

## 2. 최종 우선순위 확정

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    최종 구현 우선순위                                    │
│                                                                         │
│  🥇 Phase 1: 서비스 토큰 에러 코드 구현 (지금 시작)                      │
│     ├── -32001: SERVICE_TOKEN_MISSING                                   │
│     ├── -32002: SERVICE_TOKEN_INVALID                                   │
│     └── -32003: SERVICE_TOKEN_EXPIRED                                   │
│     예상 시간: 2시간                                                    │
│                                                                         │
│  🥈 Phase 2: Agent별 서버 필터링 (Phase 1 완료 후)                       │
│     ├── mcphub_keys에 allowedServers 필드 추가                          │
│     ├── tools/list 필터링 로직                                          │
│     └── Agent별 전용 MCPHub Key 발급                                    │
│     예상 시간: 2시간                                                    │
│                                                                         │
│  🥉 Phase 3: MCPHub 포털 UI (MVP 이후)                                  │
│     └── 프로덕션 단계에서 개발                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Orchestrator팀 질문에 대한 답변

### Q1. 외부 플랫폼 토큰 관리 - K-Jarvis vs 외부 플랫폼 구분

**정확합니다!**

| 시나리오 | 토큰 관리 주체 | 설명 |
|---------|:------------:|------|
| **K-Jarvis 내부 사용자** | MCPHub (DB) | 포털에서 설정, `user_api_keys` 테이블에 저장 |
| **외부 플랫폼 사용자** | 외부 플랫폼 | `X-MCP-Service-Token-*` 헤더로 전달 |

```
[K-Jarvis 내부 사용자 플로우]
사용자 → K-Jarvis → Agent → MCPHub → DB에서 토큰 조회 → MCP Server

[외부 플랫폼 사용자 플로우]
사용자 → 외부 플랫폼 → MCPHub (토큰 헤더 전달) → MCP Server
```

### Q2. Platform Key 토큰 Fallback 동작

**현재 동작 (테스트 환경):**
- Platform Key로 요청 시 토큰이 없어도 성공 → **⚠️ 이것은 테스트 환경의 기본 토큰 때문입니다**
- MCP Server 자체에 기본 토큰이 설정되어 있어서 동작한 것입니다

**프로덕션 기대 동작:**
```
Platform Key + 토큰 없음 → 에러 반환 (-32001)
```

**Phase 1에서 이 부분을 명확하게 구현하겠습니다.**

---

## 4. Agent팀 질문에 대한 답변

### Q1. MCPHub Key 발급 방법

**Phase 2에서 아래 방식으로 발급 예정:**

```bash
# MCPHub API를 통해 발급
POST /api/mcphub-keys
{
  "name": "Confluence Agent Key",
  "allowedServers": ["mcp-atlassian-confluence"]
}
```

**Phase 2 완료 후 발급된 키를 공유드리겠습니다.**

### Q2. allowedServers 여러 개 지정 가능?

**✅ 가능합니다!**

```json
{
  "name": "Jira+Confluence Agent Key",
  "allowedServers": ["mcp-atlassian-jira", "mcp-atlassian-confluence"]
}
```

### Q3. 토큰 에러 시 retry 정책

**✅ retry 불필요, 바로 사용자 안내가 맞습니다.**

```
토큰 없음 → -32001 에러 → Agent가 사용자에게 안내 → 사용자가 토큰 설정 → 재시도
```

자동 retry는 의미가 없습니다 (토큰을 설정해야 하므로).

---

## 5. 즉시 구현 시작: Phase 1

### 구현 내용

```typescript
// 에러 코드 상수
const MCP_ERROR_CODES = {
  SERVICE_TOKEN_MISSING: -32001,
  SERVICE_TOKEN_INVALID: -32002,
  SERVICE_TOKEN_EXPIRED: -32003
};

// 에러 응답 형식
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32001,
    "message": "서비스 토큰이 없습니다",
    "data": {
      "service": "Jira",
      "action": "Jira API 토큰을 설정해주세요"
    }
  }
}
```

### 구현 위치

| 파일 | 변경 내용 |
|-----|---------|
| `utils/mcpErrorCodes.ts` | 에러 코드 상수 정의 (신규) |
| `services/mcpService.ts` | tools/call에서 토큰 검증 및 에러 반환 |

---

## 6. 각 팀 역할 (Phase 1 동안)

| 팀 | 역할 | 상태 |
|:--:|-----|:----:|
| **MCPHub** | 에러 코드 구현 | 🔄 진행 중 |
| **Orchestrator** | 대기 | ⏸️ |
| **Agent** | 에러 처리 코드 준비 | ⏸️ (MCPHub 완료 후) |

---

## 7. 다음 알림 시점

- **Phase 1 완료 시**: 에러 코드 구현 완료 알림
- **Phase 2 완료 시**: Agent별 MCPHub Key 발급 및 공유

---

**이제 Phase 1 구현을 시작하겠습니다!** 🚀

---

*MCPHub Team*  
*2025-12-11*

