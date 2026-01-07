# MCPHub 통합 테스트 시나리오

> **작성일**: 2025-12-11  
> **작성팀**: MCPHub Team  
> **대상**: Orchestrator Team, Agent Team

---

## 📋 개요

MCPHub의 외부 플랫폼 연동 기능 및 핵심 기능이 구현 완료되었습니다.  
다른 팀들과 통합 테스트를 진행하기 위해 구체적인 테스트 시나리오를 공유합니다.

---

## ✅ MCPHub 내부 테스트 완료 현황

| # | 테스트 항목 | 상태 | 비고 |
|:-:|-----------|:----:|------|
| 1 | Health Check API | ✅ | `/api/health` |
| 2 | Admin 로그인 (JWT) | ✅ | `/api/auth/login` |
| 3 | Platform Key 발급 | ✅ | `/api/platform/keys` |
| 4 | Platform Key 검증 | ✅ | Rate Limit 정상 동작 |
| 5 | MCP 요청 (Platform Key) | ✅ | `tools/list` 응답 정상 |
| 6 | 서비스 토큰 헤더 파싱 | ✅ | `X-MCP-Service-Token-*` |
| 7 | MCP Server 연결 (kt-membership) | ✅ | 5개 도구 연결됨 |

### 현재 MCP Server 상태
| Server | Status | Tools |
|--------|:------:|:-----:|
| kt-membership | 🟢 Connected | 5 |
| mcp-atlassian-jira | 🔴 Disconnected | 0 |
| mcp-atlassian-confluence | 🔴 Disconnected | 0 |
| github-mcp-server | 🔴 Disconnected | 0 |

---

## 🧪 통합 테스트 시나리오

### 시나리오 1: Orchestrator → MCPHub 연동

#### 1-1. Platform Key 발급 요청

**목적**: Orchestrator가 외부 플랫폼으로서 MCPHub에 연동하기 위한 API Key 발급

```bash
# MCPHub Admin에게 요청하여 Platform Key 발급
POST /api/platform/keys
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "platformName": "K-Jarvis Orchestrator",
  "description": "Orchestrator 연동용 Platform Key",
  "contactEmail": "orchestrator@company.com",
  "allowedServers": ["mcp-atlassian-jira", "mcp-atlassian-confluence", "github-mcp-server"],
  "rateLimit": {
    "requestsPerMinute": 100,
    "requestsPerDay": 10000
  },
  "expiresInDays": 365
}
```

**응답 예시**:
```json
{
  "success": true,
  "platformKey": {
    "keyValue": "mcpplatform_xxxxx",
    "platformName": "K-Jarvis Orchestrator",
    "expiresAt": "2026-12-11T..."
  }
}
```

#### 1-2. Platform Key로 MCP 요청

**목적**: 발급받은 Platform Key로 MCPHub의 MCP 엔드포인트 호출

```bash
POST /mcp
Authorization: Bearer mcpplatform_xxxxx
X-Platform-User-Id: user-12345
X-MCP-Service-Token-Jira: {user_jira_token}
X-MCP-Service-Token-GitHub: {user_github_token}
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**검증 항목**:
- [ ] Platform Key 인증 성공
- [ ] Rate Limit 카운팅 정상
- [ ] 서비스 토큰 헤더 파싱 정상
- [ ] MCP 응답 정상 반환

---

### 시나리오 2: Agent → MCPHub 연동

#### 2-1. Agent가 MCPHub에 Tool 호출

**목적**: Agent (Jira/GitHub/Confluence)가 MCPHub를 통해 Tool 호출

```bash
POST /mcp
Authorization: Bearer mcpplatform_xxxxx
X-Platform-User-Id: agent-user-001
X-MCP-Service-Token-Jira: {jira_api_token}
X-Request-Id: req-uuid-12345
X-User-Id: user-uuid-67890
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "jira_search",
    "arguments": {
      "jql": "project = TEST"
    }
  }
}
```

**검증 항목**:
- [ ] 서비스 토큰이 Agent까지 전달됨
- [ ] `X-Request-Id` 헤더 전파됨
- [ ] `X-User-Id` 헤더 전파됨
- [ ] Tool 실행 결과 정상 반환

---

### 시나리오 3: 전체 플로우 (End-to-End)

```
┌─────────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  External       │     │             │     │             │     │   External  │
│  Platform       │────▶│ Orchestrator│────▶│   MCPHub    │────▶│    Agent    │
│  (User Request) │     │             │     │             │     │  (Jira/GH)  │
└─────────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                      │                   │                   │
       │   1. 사용자 요청      │                   │                   │
       │──────────────────────▶                   │                   │
       │                      │  2. Platform Key  │                   │
       │                      │  + Service Token  │                   │
       │                      │──────────────────▶│                   │
       │                      │                   │  3. Token 전달   │
       │                      │                   │──────────────────▶│
       │                      │                   │  4. Tool 실행    │
       │                      │                   │◀──────────────────│
       │                      │  5. 결과 반환     │                   │
       │                      │◀──────────────────│                   │
       │   6. 응답            │                   │                   │
       │◀─────────────────────│                   │                   │
```

---

## 📡 테스트용 API 엔드포인트

### MCPHub Base URL
```
http://localhost:3000  (로컬)
```

### 주요 엔드포인트

| Method | Path | 설명 | 인증 |
|:------:|------|------|:----:|
| GET | `/api/health` | 헬스체크 | ❌ |
| POST | `/api/auth/login` | 로그인 | ❌ |
| GET | `/api/servers` | MCP 서버 목록 | ✅ |
| POST | `/api/platform/keys` | Platform Key 발급 | Admin |
| POST | `/api/platform/keys/validate` | Platform Key 검증 | Platform Key |
| POST | `/mcp` | MCP 요청 | ✅ |
| POST | `/api/token/validate` | 토큰 검증 API | ✅ |

---

## 🔑 인증 방식

### 1. JWT Token (기존 사용자)
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

### 2. MCPHub Key (MCP 서버용)
```
Authorization: Bearer mcphub_xxxxx
```

### 3. Platform Key (외부 플랫폼용) ⭐ NEW
```
Authorization: Bearer mcpplatform_xxxxx
X-Platform-User-Id: external-user-123
X-MCP-Service-Token-Jira: jira-token
X-MCP-Service-Token-GitHub: github-token
X-MCP-Service-Token-Confluence: confluence-token
```

---

## 📝 각 팀별 요청 사항

### Orchestrator Team

1. **Platform Key 발급 테스트**
   - MCPHub Admin에게 Platform Key 발급 요청
   - 발급받은 키로 `/api/platform/keys/validate` 호출

2. **MCP 요청 테스트**
   - Platform Key로 `/mcp` 엔드포인트 호출
   - `tools/list` 및 `tools/call` 테스트

3. **서비스 토큰 전달 테스트**
   - `X-MCP-Service-Token-*` 헤더가 Agent까지 전달되는지 확인

### Agent Team

1. **MCP Server 연결 확인**
   - Jira, Confluence, GitHub MCP Server가 MCPHub에 연결되어야 함
   - 현재 `disconnected` 상태 → 연결 필요

2. **서비스 토큰 수신 테스트**
   - MCPHub로부터 전달받은 서비스 토큰 확인
   - 해당 토큰으로 외부 서비스 (Jira, GitHub) 호출

3. **헤더 전파 테스트**
   - `X-Request-Id`, `X-User-Id` 헤더 수신 확인
   - 로그에 해당 ID 포함 확인

---

## 🚨 에러 코드 (합의됨)

| Code | 의미 | 설명 |
|:----:|------|------|
| `-32001` | `SERVICE_TOKEN_MISSING` | 서비스 토큰 누락 |
| `-32002` | `SERVICE_TOKEN_INVALID` | 서비스 토큰 유효하지 않음 |
| `-32003` | `SERVICE_TOKEN_EXPIRED` | 서비스 토큰 만료됨 |

---

## 📅 테스트 일정 제안

| 단계 | 내용 | 예상 소요 |
|:---:|------|:--------:|
| 1 | Platform Key 발급 및 검증 | 30분 |
| 2 | Agent MCP Server 연결 | 1시간 |
| 3 | Orchestrator → MCPHub 테스트 | 1시간 |
| 4 | 전체 E2E 테스트 | 2시간 |

---

## 💬 문의 및 협조

- **MCPHub 담당자**: MCPHub Team
- **테스트 환경**: localhost:3000
- **긴급 연락**: Slack #mcphub-dev

**각 팀에서 테스트 준비가 되시면 알려주세요!**

---

*문서 작성: MCPHub Team, 2025-12-11*

