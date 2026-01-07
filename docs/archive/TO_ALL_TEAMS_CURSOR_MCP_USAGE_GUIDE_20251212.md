# Cursor MCP 사용 가이드 - 모든 팀 필독

## 1. Cursor에서 MCP 도구 사용하기

Cursor IDE에는 MCP 서버를 직접 연결하여 Confluence, Jira, GitHub 등의 도구를 AI 어시스턴트가 직접 사용할 수 있습니다.

## 2. mcp.json 설정 위치

```
~/.cursor/mcp.json
```

macOS 기준: `/Users/{username}/.cursor/mcp.json`

## 3. mcp.json 설정 예시

```json
{
  "mcpServers": {
    "mcp-hub": {
      "type": "streamable-http",
      "url": "https://mcphub-backend.redrock-1ca7a56f.koreacentral.azurecontainerapps.io/mcp",
      "headers": {
        "Authorization": "Bearer {YOUR_MCPHUB_KEY}"
      }
    },
    "mcp-hub-local": {
      "type": "streamable-http",
      "url": "http://localhost:3000/mcp",
      "headers": {
        "Authorization": "Bearer {YOUR_LOCAL_MCPHUB_KEY}",
        "X-MCPHub-User-Id": "{YOUR_KAUTH_USER_ID}"
      }
    }
  }
}
```

## 4. 중요 설정 값 설명

### 4.1 Authorization Header
```
"Authorization": "Bearer mcphub_xxxxxxxx..."
```
- MCPHub에서 발급받은 **MCPHub Key**
- MCPHub 로그인 후 > Keys 메뉴 > Create Key로 생성

### 4.2 X-MCPHub-User-Id Header (Option C 아키텍처)
```
"X-MCPHub-User-Id": "717dabfd-70b1-4d5c-999a-5de90d850be6"
```
- **K-Auth User ID** (UUID 형식)
- 이 값으로 MCPHub가 해당 사용자의 서비스 토큰을 조회함
- K-Auth 로그인 후 JWT의 `sub` 클레임에서 확인 가능

## 5. 서버 선택

| 서버 이름 | URL | 용도 |
|----------|-----|------|
| `mcp-hub` | Azure 배포 | 프로덕션/공용 |
| `mcp-hub-local` | localhost:3000 | 로컬 개발/테스트 |
| `mcp-hub-company` | 회사 내부 서버 | 사내 전용 |

## 6. Confluence 문서 작성 방법

### 6.1 AI에게 요청 예시
```
"Cursor의 mcp-hub를 사용해서 CNCORE 스페이스에 
'K-Jarvis 1.0 가이드'라는 제목으로 문서를 작성해줘"
```

### 6.2 AI가 호출하는 도구
```
mcp_mcp-hub_create_page
- space_key: "CNCORE"
- title: "K-Jarvis 1.0 가이드"
- content: "..."
- content_format: "markdown"
```

## 7. 사전 조건 (중요!)

### 7.1 MCPHub에 서비스 토큰 등록 필수
Cursor에서 Confluence 도구를 사용하려면:
1. MCPHub에 로그인
2. Confluence MCP 서버 구독
3. **Atlassian API Token** 등록
   - `CONFLUENCE_API_TOKEN`
   - `CONFLUENCE_URL`
   - `CONFLUENCE_EMAIL`

### 7.2 X-MCPHub-User-Id 설정 필수
- 로컬 서버 사용 시 반드시 `X-MCPHub-User-Id` 헤더 추가
- 이 값이 없으면 MCPHub가 서비스 토큰을 찾을 수 없음

## 8. 트러블슈팅

### 8.1 "Error calling tool 'create_page'" 에러
**원인**: 서비스 토큰 미등록 또는 X-MCPHub-User-Id 누락

**해결**:
1. MCPHub에 로그인하여 Confluence 토큰 등록 확인
2. mcp.json에 X-MCPHub-User-Id 헤더 추가

### 8.2 MCP 도구가 보이지 않음
**원인**: Cursor 재시작 필요

**해결**:
1. mcp.json 수정 후 Cursor 완전 종료
2. Cursor 재시작

### 8.3 연결 실패
**원인**: MCPHub 서버가 실행 중이지 않음

**해결**:
- 로컬: `cd mcphubproject && pnpm dev`
- Azure: 서버 상태 확인

## 9. 사용 가능한 MCP 도구 목록

Cursor에서 `mcp-hub` 연결 시 사용 가능한 도구:

### Confluence
- `mcp_mcp-hub_create_page` - 페이지 생성
- `mcp_mcp-hub_update_page` - 페이지 수정
- `mcp_mcp-hub_get_page` - 페이지 조회
- `mcp_mcp-hub_get_page_children` - 하위 페이지 조회

### Jira
- `mcp_mcp-hub_create_issue` - 이슈 생성
- `mcp_mcp-hub_update_issue` - 이슈 수정
- `mcp_mcp-hub_search` - JQL 검색
- `mcp_mcp-hub_get_issue` - 이슈 조회

### GitHub
- `mcp_mcp-hub_create_pull_request` - PR 생성
- `mcp_mcp-hub_get_pull_requests` - PR 목록
- `mcp_mcp-hub_get_pull_request_diff` - PR diff 조회

## 10. 각 팀별 필요 작업

### Orchestrator 팀
- [x] mcp.json 설정 완료
- [ ] Confluence 토큰 MCPHub에 등록 확인

### Agent 팀
- [ ] mcp.json 설정
- [ ] 자체 테스트용 MCPHub Key 생성

### MCPHub 팀
- [ ] Cursor MCP 연동 테스트
- [ ] 서비스 토큰 관리 UI 안내 문서

---

**작성일**: 2024-12-12
**작성팀**: K-Jarvis Orchestrator Team

