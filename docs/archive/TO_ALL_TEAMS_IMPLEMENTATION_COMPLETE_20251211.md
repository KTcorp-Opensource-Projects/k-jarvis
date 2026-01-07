# [공유] MCPHub Phase 1 & 2 구현 완료

**발신**: MCPHub팀  
**수신**: Orchestrator팀, Agent팀  
**작성일**: 2025-12-11  
**유형**: ✅ 구현 완료

---

## 1. 구현 완료 사항

### ✅ Phase 1: 서비스 토큰 에러 코드 (완료)

```typescript
// apps/backend/src/utils/mcpErrorCodes.ts

export const MCP_ERROR_CODES = {
  SERVICE_TOKEN_MISSING: -32001,  // 토큰 없음
  SERVICE_TOKEN_INVALID: -32002,  // 토큰 유효하지 않음
  SERVICE_TOKEN_EXPIRED: -32003,  // 토큰 만료
};
```

**에러 응답 예시:**

```json
{
  "content": [{
    "type": "text",
    "text": "{\"error\":{\"code\":-32001,\"message\":\"Jira 서비스 토큰이 설정되지 않았습니다\",\"data\":{\"service\":\"Jira\",\"action\":\"Jira API 토큰을 설정해주세요\",\"required_tokens\":[\"JIRA_API_TOKEN\",\"ATLASSIAN_API_TOKEN\"]}}}"
  }],
  "isError": true
}
```

**서비스별 필요 토큰 매핑:**

| MCP Server | 필요 토큰 |
|-----------|---------|
| `mcp-atlassian-jira` | JIRA_API_TOKEN, ATLASSIAN_API_TOKEN |
| `mcp-atlassian-confluence` | CONFLUENCE_API_TOKEN, ATLASSIAN_API_TOKEN |
| `github-mcp-server` | GITHUB_TOKEN, GITHUB_PERSONAL_ACCESS_TOKEN |
| `kt-membership-mcp-server` | (토큰 필요 없음) |

---

### ✅ Phase 2: Agent별 서버 필터링 (완료)

**MCPHub Key에 allowedServers 필드 추가:**

```typescript
// apps/backend/src/db/entities/MCPHubKey.ts

@Column({ type: 'jsonb', nullable: true })
allowedServers?: string[];
```

**tools/list에서 필터링 로직 구현:**

```typescript
// MCPHub Key의 allowedServers가 설정된 경우
// 해당 서버의 도구만 반환됨
if (hasKeyAllowedServers) {
  const isAllowedByKey = keyAllowedServers.includes(serverInfo.name);
  if (!isAllowedByKey) return false;
}
```

---

## 2. Agent별 전용 MCPHub Key 발급 완료

### 발급된 키 목록

| Agent | MCPHub Key | 허용 서버 | 예상 도구 수 |
|------|-----------|----------|:-----------:|
| **Confluence Agent** | `mcphub_0757bc9f92ba7ab331ea0d74cd788ade7fb8b5d5d8241ecefa23fd5e10083ebd` | `["mcp-atlassian-confluence"]` | 11개 |
| **Jira Agent** | `mcphub_62aeab0f7a8e21321c457c49dae78c7afdb296f42a090d345d201b66907dc112` | `["mcp-atlassian-jira"]` | 32개 |
| **GitHub Agent** | `mcphub_ef315e4ed85ad7c67a39affd3865025a269dc50de8e4afb3ff004469d9c752c4` | `["github-mcp-server"]` | 10개 |

### 사용 방법

```bash
# Confluence Agent 예시
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mcphub_0757bc9f92ba7ab331ea0d74cd788ade7fb8b5d5d8241ecefa23fd5e10083ebd" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# 응답: Confluence 도구 11개만 반환됨
```

---

## 3. 전체 기존 키 (모든 서버 접근)

| 키 이름 | MCPHub Key | 허용 서버 |
|-------|-----------|---------|
| **MCPHub Key (기존)** | `mcphub_0a7fb098aa06396213ff4e317f0d80694a1d5e0e065828c9b3aa684a8a32ff43` | 모든 서버 (58개 도구) |

**참고:** 기존 키는 `allowedServers`가 null이므로 모든 서버에 접근 가능합니다.

---

## 4. Agent팀 적용 방법

### 4.1 환경 변수 변경

```python
# 기존 (모든 Agent가 동일한 키 사용)
MCP_HUB_TOKEN=mcphub_0a7fb098aa06396213ff4e317f0d80694a1d5e0e065828c9b3aa684a8a32ff43

# 변경 (Agent별 전용 키)
# Confluence Agent
MCP_HUB_TOKEN=mcphub_0757bc9f92ba7ab331ea0d74cd788ade7fb8b5d5d8241ecefa23fd5e10083ebd

# Jira Agent
MCP_HUB_TOKEN=mcphub_62aeab0f7a8e21321c457c49dae78c7afdb296f42a090d345d201b66907dc112

# GitHub Agent  
MCP_HUB_TOKEN=mcphub_ef315e4ed85ad7c67a39affd3865025a269dc50de8e4afb3ff004469d9c752c4
```

### 4.2 에러 처리 구현

```python
# langgraph_agent.py
async def handle_mcp_error(error: dict) -> str:
    code = error.get("code")
    data = error.get("data", {})
    
    if code == -32001:  # SERVICE_TOKEN_MISSING
        service = data.get("service", "서비스")
        return f"⚠️ {service} 토큰이 설정되지 않았습니다. MCPHub에서 토큰을 설정해주세요."
    elif code == -32002:  # SERVICE_TOKEN_INVALID
        return "⚠️ 서비스 토큰이 유효하지 않습니다."
    elif code == -32003:  # SERVICE_TOKEN_EXPIRED
        return "⚠️ 서비스 토큰이 만료되었습니다."
    else:
        return f"⚠️ 오류: {error.get('message')}"
```

---

## 5. 테스트 방법

### 5.1 Agent별 도구 개수 확인

```bash
# Confluence Agent Key로 테스트 (11개 예상)
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mcphub_0757bc9f92ba7ab331ea0d74cd788ade7fb8b5d5d8241ecefa23fd5e10083ebd" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' | jq '.result.tools | length'

# Jira Agent Key로 테스트 (32개 예상)
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mcphub_62aeab0f7a8e21321c457c49dae78c7afdb296f42a090d345d201b66907dc112" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' | jq '.result.tools | length'

# GitHub Agent Key로 테스트 (10개 예상)
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mcphub_ef315e4ed85ad7c67a39affd3865025a269dc50de8e4afb3ff004469d9c752c4" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' | jq '.result.tools | length'
```

### 5.2 서비스 토큰 에러 테스트

```bash
# 토큰 없이 tool 호출 → -32001 에러 예상
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mcphub_62aeab0f7a8e21321c457c49dae78c7afdb296f42a090d345d201b66907dc112" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"mcp_mcp-hub_jira_search","arguments":{"jql":"project=TEST"}},"id":1}'
```

---

## 6. 다음 단계

| 단계 | 담당 | 상태 |
|-----|:----:|:----:|
| Agent별 전용 키 적용 | Agent팀 | ⏳ 진행 예정 |
| 에러 처리 구현 | Agent팀 | ⏳ 진행 예정 |
| 통합 테스트 | 전체 | ⏳ Agent팀 적용 후 |

---

## 7. 요약

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        구현 완료 요약                                    │
│                                                                         │
│  ✅ Phase 1: 서비스 토큰 에러 코드                                       │
│     - -32001 (MISSING), -32002 (INVALID), -32003 (EXPIRED)              │
│     - tools/call 시 토큰 검증 후 에러 반환                              │
│                                                                         │
│  ✅ Phase 2: Agent별 서버 필터링                                         │
│     - MCPHub Key에 allowedServers 필드 추가                             │
│     - tools/list에서 필터링 로직 구현                                   │
│                                                                         │
│  ✅ Agent별 전용 키 발급                                                 │
│     - Confluence Agent: mcphub_0757bc9f... (11개 도구)                  │
│     - Jira Agent: mcphub_62aeab0f... (32개 도구)                        │
│     - GitHub Agent: mcphub_ef315e4e... (10개 도구)                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

**Agent팀에서 위 키를 적용 후 테스트 진행 부탁드립니다!** 🙏

---

*MCPHub Team*  
*2025-12-11*

