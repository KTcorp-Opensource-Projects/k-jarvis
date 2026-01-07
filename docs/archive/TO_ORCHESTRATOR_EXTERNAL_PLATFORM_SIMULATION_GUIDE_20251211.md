# [가이드] 외부 플랫폼 시뮬레이션 테스트 - MCPHub 연동 방법

**발신**: MCPHub팀  
**수신**: Orchestrator팀  
**작성일**: 2025-12-11  
**유형**: 📖 외부 플랫폼 연동 가이드

---

## 1. 개요

외부 플랫폼이 MCPHub와 연동하여 MCP 도구를 사용하는 시나리오를 시뮬레이션할 때 참고할 가이드입니다.

---

## 2. 연동 방식 비교

### 2.1 기존 방식 (MCPHub Key)
```
Agent → MCPHub (MCPHub Key) → MCP Server
```
- **용도**: MCPHub 내부 사용자/Agent
- **키 형식**: `mcphub_xxx`
- **서비스 토큰**: MCPHub에서 관리

### 2.2 외부 플랫폼 방식 (Platform Key) ⭐ NEW
```
External Platform → MCPHub (Platform Key) → MCP Server
```
- **용도**: 외부 플랫폼 (타사 서비스)
- **키 형식**: `mcpplatform_xxx`
- **서비스 토큰**: **외부 플랫폼에서 관리하여 전달**

---

## 3. 외부 플랫폼 연동 플로우

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    외부 플랫폼 → MCPHub 연동 플로우                       │
│                                                                         │
│  ┌──────────────────┐                                                   │
│  │ External Platform │                                                  │
│  │   (Orchestrator) │                                                   │
│  └────────┬─────────┘                                                   │
│           │                                                             │
│           │ 1. Platform Key 발급 요청 (최초 1회)                         │
│           │    POST /api/platform/keys                                  │
│           ▼                                                             │
│  ┌──────────────────┐                                                   │
│  │     MCPHub       │  → Platform Key 발급 (mcpplatform_xxx)            │
│  └────────┬─────────┘                                                   │
│           │                                                             │
│           │ 2. 사용자 요청 시                                            │
│           │    - Platform Key로 인증                                    │
│           │    - 사용자의 서비스 토큰을 헤더로 전달                       │
│           │                                                             │
│  ┌──────────────────┐                                                   │
│  │ External Platform │                                                  │
│  │                   │                                                  │
│  │  사용자A의 요청:  │                                                   │
│  │  - Jira 토큰     │                                                   │
│  │  - GitHub 토큰   │                                                   │
│  └────────┬─────────┘                                                   │
│           │                                                             │
│           │ 3. MCP 요청                                                 │
│           │    Authorization: Bearer mcpplatform_xxx                    │
│           │    X-Platform-User-Id: user-123                             │
│           │    X-MCP-Service-Token-Jira: user_jira_token               │
│           │    X-MCP-Service-Token-GitHub: user_github_token           │
│           ▼                                                             │
│  ┌──────────────────┐                                                   │
│  │     MCPHub       │                                                   │
│  │                   │                                                  │
│  │  - Platform Key 검증                                                 │
│  │  - Rate Limit 체크                                                   │
│  │  - 서비스 토큰 추출                                                  │
│  └────────┬─────────┘                                                   │
│           │                                                             │
│           │ 4. MCP Server에 토큰 전달                                   │
│           ▼                                                             │
│  ┌──────────────────┐                                                   │
│  │   MCP Server     │  → 사용자 토큰으로 API 호출                       │
│  └──────────────────┘                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 테스트용 Platform Key

### 이미 발급된 테스트용 키
```
Platform Name: Test External Platform
Platform Key: mcpplatform_075f73ec6b32aa7de66238f553e88377ad78e2ff248e9654a6285c1393a74a76
Allowed Servers: jira-server, confluence-server, github-server
Rate Limit: 100/min, 10000/day
Expires: 2026-01-10
```

---

## 5. 외부 플랫폼 시뮬레이션 테스트 코드

### 5.1 tools/list 요청 (토큰 불필요)

```bash
PLATFORM_KEY="mcpplatform_075f73ec6b32aa7de66238f553e88377ad78e2ff248e9654a6285c1393a74a76"

curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PLATFORM_KEY" \
  -H "X-Platform-User-Id: external-user-001" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### 5.2 tools/call 요청 (서비스 토큰 필요)

```bash
PLATFORM_KEY="mcpplatform_075f73ec6b32aa7de66238f553e88377ad78e2ff248e9654a6285c1393a74a76"

# Jira 검색 예시
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PLATFORM_KEY" \
  -H "X-Platform-User-Id: external-user-001" \
  -H "X-MCP-Service-Token-Jira: <user_jira_api_token>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "jira_search",
      "arguments": {
        "jql": "project = AUT ORDER BY created DESC",
        "limit": 5
      }
    }
  }'
```

### 5.3 Python 예시 (외부 플랫폼 SDK 시뮬레이션)

```python
import httpx
import json

class MCPHubExternalClient:
    """외부 플랫폼용 MCPHub 클라이언트"""
    
    def __init__(self, platform_key: str, mcphub_url: str = "http://localhost:3000/mcp"):
        self.platform_key = platform_key
        self.mcphub_url = mcphub_url
    
    def _get_headers(self, user_id: str, service_tokens: dict = None):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.platform_key}",
            "X-Platform-User-Id": user_id
        }
        
        # 사용자의 서비스 토큰 추가
        if service_tokens:
            for service, token in service_tokens.items():
                headers[f"X-MCP-Service-Token-{service}"] = token
        
        return headers
    
    async def list_tools(self, user_id: str):
        """도구 목록 조회 (토큰 불필요)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.mcphub_url,
                headers=self._get_headers(user_id),
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                }
            )
            return response.json()
    
    async def call_tool(self, user_id: str, tool_name: str, arguments: dict, service_tokens: dict):
        """도구 호출 (서비스 토큰 필요)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.mcphub_url,
                headers=self._get_headers(user_id, service_tokens),
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
            )
            return response.json()

# 사용 예시
async def main():
    client = MCPHubExternalClient(
        platform_key="mcpplatform_075f73ec6b32aa7de66238f553e88377ad78e2ff248e9654a6285c1393a74a76"
    )
    
    # 사용자별 서비스 토큰 (외부 플랫폼에서 관리)
    user_tokens = {
        "Jira": "user_jira_api_token_here",
        "GitHub": "user_github_token_here"
    }
    
    # 도구 목록 조회
    tools = await client.list_tools(user_id="user-123")
    print(f"Available tools: {len(tools['result']['tools'])}")
    
    # Jira 검색 호출
    result = await client.call_tool(
        user_id="user-123",
        tool_name="jira_search",
        arguments={"jql": "project = AUT", "limit": 5},
        service_tokens=user_tokens
    )
    print(f"Jira result: {result}")
```

---

## 6. 핵심 포인트

### 6.1 서비스 토큰 관리 책임

| 항목 | MCPHub Key | Platform Key |
|-----|:----------:|:------------:|
| 서비스 토큰 저장 | MCPHub | **외부 플랫폼** |
| 토큰 전달 방식 | DB에서 조회 | **헤더로 전달** |
| 사용자 구분 | MCPHub User ID | **X-Platform-User-Id** |

### 6.2 헤더 매핑

```
X-MCP-Service-Token-Jira       → MCP Server의 JIRA_API_TOKEN
X-MCP-Service-Token-GitHub     → MCP Server의 GITHUB_TOKEN
X-MCP-Service-Token-Confluence → MCP Server의 CONFLUENCE_API_TOKEN
```

### 6.3 에러 코드

| Code | 의미 | 조치 |
|:----:|------|------|
| `-32001` | 서비스 토큰 누락 | 헤더에 X-MCP-Service-Token-* 추가 |
| `-32002` | 서비스 토큰 무효 | 토큰 갱신 필요 |
| `-32003` | 서비스 토큰 만료 | 토큰 재발급 필요 |

---

## 7. Rate Limit

Platform Key는 Rate Limit이 적용됩니다:

```json
{
  "rateLimit": {
    "requestsPerMinute": 100,
    "requestsPerDay": 10000,
    "currentMinute": 2,
    "currentDay": 6
  }
}
```

### Rate Limit 확인 API
```bash
curl -X POST http://localhost:3000/api/platform/keys/validate \
  -H "Authorization: Bearer mcpplatform_xxx"
```

---

## 8. 시뮬레이션 체크리스트

### 외부 플랫폼 역할
- [ ] Platform Key 보관
- [ ] 사용자별 서비스 토큰 관리 (DB 저장, 암호화)
- [ ] 요청 시 서비스 토큰을 헤더로 전달
- [ ] Rate Limit 모니터링

### MCPHub 역할 (이미 구현됨)
- [x] Platform Key 검증
- [x] Rate Limit 적용
- [x] 서비스 토큰 헤더 파싱
- [x] MCP Server로 토큰 전달

---

## 9. 질문이 있으시면 연락주세요!

- **Slack**: #mcphub-dev
- **테스트 지원**: 필요시 실시간 지원 가능

---

*MCPHub Team*  
*2025-12-11*

