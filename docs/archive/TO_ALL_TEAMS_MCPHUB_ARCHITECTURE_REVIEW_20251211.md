# [공유] MCPHub 아키텍처 정밀 검토 결과 및 제안

**발신**: MCPHub팀  
**수신**: Orchestrator팀, Agent팀  
**작성일**: 2025-12-11  
**유형**: 🏗️ 아키텍처 검토 및 제안

---

## 1. 배경

K-Jarvis 및 외부 플랫폼 연동 시 다음 요구사항이 논의되었습니다:

1. **Agent별 MCP Server 필터링**: Confluence Agent는 Confluence 도구만, Jira Agent는 Jira 도구만 노출
2. **사용자별 서비스 토큰 관리**: MCPHub에서 사용자(K-Auth 계정)별로 서비스 토큰 관리
3. **토큰 없을 시 안내**: 서비스 토큰이 없으면 MCPHub 포털에서 입력하라는 안내

---

## 2. 목표 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      K-Jarvis / 외부 플랫폼 아키텍처                      │
│                                                                         │
│                         ┌───────────────┐                               │
│                         │    K-Auth     │                               │
│                         │  (SSO 중앙)   │                               │
│                         └───────┬───────┘                               │
│                                 │                                       │
│         ┌───────────────────────┼───────────────────────┐               │
│         │                       │                       │               │
│         ▼                       ▼                       ▼               │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐           │
│  │ K-Jarvis    │       │   MCPHub    │       │ 외부 플랫폼 │           │
│  │ (Orch+Agent)│       │   포털      │       │    X, Y     │           │
│  └──────┬──────┘       └──────┬──────┘       └──────┬──────┘           │
│         │                     │                     │                   │
│         │                     │                     │                   │
│         │              ┌──────┴──────┐              │                   │
│         │              │ 사용자별     │              │                   │
│         │              │ 서비스 토큰  │              │                   │
│         │              │ 관리         │              │                   │
│         │              └──────┬──────┘              │                   │
│         │                     │                     │                   │
│         └─────────────────────┼─────────────────────┘                   │
│                               │                                         │
│                               ▼                                         │
│                      ┌─────────────────┐                                │
│                      │     MCPHub      │                                │
│                      │     Backend     │                                │
│                      └────────┬────────┘                                │
│                               │                                         │
│          ┌────────────────────┼────────────────────┐                    │
│          ▼                    ▼                    ▼                    │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐               │
│  │ Jira MCP    │     │ Confluence  │     │ GitHub MCP  │               │
│  │ Server (32) │     │ MCP (11)    │     │ Server (10) │               │
│  └─────────────┘     └─────────────┘     └─────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 현재 MCPHub 구현 상태

### 3.1 ✅ 이미 구현된 기능

| # | 기능 | 상태 | 위치 |
|:-:|-----|:----:|------|
| 1 | 사용자별 서버 구독 | ✅ | `user_server_subscriptions` 테이블 |
| 2 | 사용자별 서비스 토큰 저장 | ✅ | `user_api_keys` 테이블 (암호화) |
| 3 | 구독 서버 기반 tools/list 필터링 | ✅ | `mcpService.ts` |
| 4 | K-Auth SSO 연동 | ✅ | `kauth-routes.ts` |
| 5 | MCPHub Key 인증 | ✅ | `auth.ts` 미들웨어 |
| 6 | Platform Key 인증 | ✅ | 외부 플랫폼용 |

### 3.2 ⚠️ 추가 구현 필요 사항

| # | 기능 | 상태 | 설명 |
|:-:|-----|:----:|------|
| 1 | Agent용 서버 필터링 (MCPHub Key 레벨) | ⚠️ | Agent별 허용 서버 지정 |
| 2 | 서비스 토큰 에러 코드 | ⚠️ | `-32001`, `-32002`, `-32003` |
| 3 | MCPHub 포털 UI (서버 구독/토큰 설정) | ⚠️ | 사용자 설정 화면 |
| 4 | 토큰 없을 시 안내 메시지 | ⚠️ | MCPHub 포털 링크 포함 |

---

## 4. 상세 플로우

### 4.1 K-Jarvis 사용자 플로우

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 사용자: "Jarvis에서 컨플 문서 검색해줘"                                  │
│                                                                         │
│ 1️⃣ K-Jarvis (Orchestrator)                                             │
│    - 사용자 K-Auth UUID: user-123                                       │
│    - "컨플" 키워드 → Confluence Agent 라우팅                            │
│                                                                         │
│ 2️⃣ Confluence Agent                                                    │
│    - MCPHub에 MCP 요청                                                  │
│    - 헤더: X-User-Id: user-123                                          │
│    - 헤더: Authorization: Bearer mcphub_xxx (Agent용 키)                │
│                                                                         │
│ 3️⃣ MCPHub                                                              │
│    - Agent 인증 (MCPHub Key)                                            │
│    - 사용자 user-123의 Confluence 서비스 토큰 조회                      │
│    - 토큰 있음 → MCP Server에 전달                                      │
│    - 토큰 없음 → 에러: "MCPHub 포털에서 토큰 설정 필요"                  │
│                                                                         │
│ 4️⃣ Confluence MCP Server                                               │
│    - 사용자 토큰으로 Confluence API 호출                                │
│    - 결과 반환                                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Agent별 도구 필터링 플로우

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Agent별 도구 필터링                                   │
│                                                                         │
│  Confluence Agent → MCPHub                                              │
│  ├── MCPHub Key: mcphub_confluence_agent_xxx                            │
│  ├── 허용 서버: ["mcp-atlassian-confluence"]                            │
│  └── tools/list 결과: 11개 (Confluence 도구만)                          │
│                                                                         │
│  Jira Agent → MCPHub                                                    │
│  ├── MCPHub Key: mcphub_jira_agent_xxx                                  │
│  ├── 허용 서버: ["mcp-atlassian-jira"]                                  │
│  └── tools/list 결과: 32개 (Jira 도구만)                                │
│                                                                         │
│  GitHub Agent → MCPHub                                                  │
│  ├── MCPHub Key: mcphub_github_agent_xxx                                │
│  ├── 허용 서버: ["github-mcp-server"]                                   │
│  └── tools/list 결과: 10개 (GitHub 도구만)                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 외부 플랫폼 사용자 플로우

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 외부 플랫폼 사용자 플로우                                                │
│                                                                         │
│ 1️⃣ 사용자가 외부 플랫폼에서 K-Auth로 로그인                             │
│    - K-Auth UUID: user-456                                              │
│                                                                         │
│ 2️⃣ 사용자가 MCPHub 포털에 접속 (K-Auth SSO)                             │
│    - 동일한 K-Auth UUID: user-456                                       │
│    - 원하는 MCP Server 구독                                             │
│    - 서비스 토큰 설정 (Jira 토큰, GitHub 토큰 등)                        │
│                                                                         │
│ 3️⃣ 외부 플랫폼에서 MCP 도구 사용 요청                                   │
│    - Platform Key: mcpplatform_xxx                                      │
│    - X-Platform-User-Id: user-456                                       │
│                                                                         │
│ 4️⃣ MCPHub가 user-456의 토큰 조회                                        │
│    - user_api_keys 테이블에서 토큰 조회                                 │
│    - MCP Server에 토큰 전달                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. 데이터 모델

### 5.1 현재 테이블 구조

```sql
-- 사용자별 MCP Server 구독
user_server_subscriptions
├── id           (UUID)
├── user_id      (UUID, FK → users.id)  -- K-Auth UUID
├── server_id    (INTEGER, FK → mcp_servers.id)
├── is_active    (BOOLEAN)
├── settings     (JSONB)
└── ...

-- 사용자별 서비스 토큰 (암호화)
user_api_keys
├── id             (INTEGER)
├── userId         (INTEGER, FK → users.id)
├── serverId       (INTEGER, FK → mcp_servers.id)
├── varName        (VARCHAR) -- 예: JIRA_API_TOKEN
├── encryptedValue (TEXT)    -- 암호화된 토큰
└── ...

-- MCPHub Key (Agent/사용자용)
mcphub_keys
├── id           (UUID)
├── keyValue     (VARCHAR)  -- mcphub_xxx
├── userId       (UUID)     -- 소유자
├── allowedServers (JSONB)  -- ⭐ 허용 서버 목록 (추가 필요)
└── ...
```

### 5.2 추가 필요 필드

```sql
-- MCPHub Key에 허용 서버 목록 추가
ALTER TABLE mcphub_keys ADD COLUMN "allowedServers" JSONB;

-- 예시 데이터
-- Confluence Agent용 키
UPDATE mcphub_keys 
SET "allowedServers" = '["mcp-atlassian-confluence"]'
WHERE name = 'Confluence Agent Key';

-- Jira Agent용 키
UPDATE mcphub_keys 
SET "allowedServers" = '["mcp-atlassian-jira"]'
WHERE name = 'Jira Agent Key';
```

---

## 6. 에러 처리

### 6.1 서비스 토큰 관련 에러 코드 (합의됨)

| Code | 이름 | 메시지 | 조치 안내 |
|:----:|-----|-------|---------|
| `-32001` | SERVICE_TOKEN_MISSING | 서비스 토큰이 없습니다 | MCPHub 포털(URL)에서 토큰을 설정해주세요 |
| `-32002` | SERVICE_TOKEN_INVALID | 서비스 토큰이 유효하지 않습니다 | MCPHub 포털(URL)에서 토큰을 갱신해주세요 |
| `-32003` | SERVICE_TOKEN_EXPIRED | 서비스 토큰이 만료되었습니다 | MCPHub 포털(URL)에서 토큰을 재발급해주세요 |

### 6.2 에러 응답 예시

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32001,
    "message": "서비스 토큰이 없습니다",
    "data": {
      "service": "Jira",
      "action": "MCPHub 포털에서 Jira API 토큰을 설정해주세요",
      "portal_url": "https://mcphub.example.com/settings/tokens"
    }
  }
}
```

---

## 7. 구현 계획

### 7.1 Phase 1: Agent별 서버 필터링 (MCPHub)

| 작업 | 담당 | 예상 시간 |
|-----|:----:|:--------:|
| mcphub_keys 테이블에 allowedServers 필드 추가 | MCPHub | 30분 |
| tools/list에서 allowedServers 기반 필터링 | MCPHub | 1시간 |
| Agent별 MCPHub Key 생성 | Agent/MCPHub | 30분 |

### 7.2 Phase 2: 서비스 토큰 에러 처리 (MCPHub)

| 작업 | 담당 | 예상 시간 |
|-----|:----:|:--------:|
| 에러 코드 상수 정의 | MCPHub | 30분 |
| tools/call에서 토큰 검증 및 에러 반환 | MCPHub | 1시간 |
| 에러 응답에 portal_url 포함 | MCPHub | 30분 |

### 7.3 Phase 3: MCPHub 포털 UI (MCPHub)

| 작업 | 담당 | 예상 시간 |
|-----|:----:|:--------:|
| 서버 구독 관리 UI | MCPHub | 2시간 |
| 서비스 토큰 설정 UI | MCPHub | 2시간 |
| K-Auth 연동 테스트 | MCPHub | 1시간 |

---

## 8. 각 팀 역할

### MCPHub팀
- [ ] MCPHub Key에 allowedServers 필드 추가
- [ ] Agent별 서버 필터링 구현
- [ ] 서비스 토큰 에러 코드 구현
- [ ] MCPHub 포털 UI 개발

### Agent팀
- [ ] Agent별 전용 MCPHub Key 발급 요청
- [ ] X-User-Id 헤더로 사용자 ID 전달
- [ ] 에러 응답 처리 (토큰 없음 시 사용자에게 안내)

### Orchestrator팀
- [ ] 사용자 K-Auth UUID를 Agent에 전달
- [ ] Agent 에러 응답을 사용자에게 표시

---

## 9. 결론

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           핵심 요약                                      │
│                                                                         │
│  1️⃣ Agent별 MCP Server 필터링                                           │
│     - MCPHub Key에 allowedServers 필드 추가                             │
│     - Confluence Agent → Confluence 도구만                              │
│     - Jira Agent → Jira 도구만                                          │
│                                                                         │
│  2️⃣ 사용자별 서비스 토큰 관리                                            │
│     - K-Auth UUID 기반 사용자 식별                                       │
│     - MCPHub 포털에서 토큰 설정                                          │
│     - user_api_keys 테이블에 암호화 저장                                 │
│                                                                         │
│  3️⃣ 토큰 없을 시 안내                                                   │
│     - 에러 코드: -32001 (SERVICE_TOKEN_MISSING)                         │
│     - MCPHub 포털 URL 포함하여 안내                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. 다음 단계

1. **각 팀 검토 요청**: 이 아키텍처에 동의하시나요?
2. **세부 일정 조율**: Phase별 구현 일정 논의
3. **우선순위 결정**: 어떤 기능부터 구현할지 결정

**피드백 부탁드립니다!** 🙏

---

*MCPHub Team*  
*2025-12-11*

