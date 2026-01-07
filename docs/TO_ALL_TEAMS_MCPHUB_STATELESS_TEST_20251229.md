# MCPHub Stateless 아키텍처 테스트 요청 (2025-12-29)

안녕하세요 Agent 팀,

MCPHub의 **Stateless 아키텍처 전환이 완료**되었습니다. 테스트를 요청드립니다.

---

## 1. 변경 사항 요약

### Stateless 아키텍처로 전환
- ❌ **제거됨**: 세션 관리 (`sessionManager.ts`, `redisSessionStore.ts`, `redisEventStore.ts`)
- ❌ **제거됨**: `Mcp-Session-Id` 헤더 의존성
- ✅ **유지됨**: `tools/list`, `tools/call` 기능
- ✅ **유지됨**: MCPHub Key 인증, 서비스 토큰 처리

### 동작 방식
```
Agent → MCPHub → MCP Server (매 요청마다 새 연결)
```
- 세션 유지 없음
- 각 요청은 독립적으로 처리

---

## 2. 테스트 환경 정보

### MCPHub 엔드포인트
```
URL: http://localhost:3000/mcp (로컬 테스트 시)
상용: https://mcphub.ambitiousbush-a8bf4bcd.koreacentral.azurecontainerapps.io/mcp
```

### 테스트 계정 정보
- **사용자명**: `testuser`
- **비밀번호**: K-Auth SSO 로그인 사용

### MCPHub Key
```
mcphub_eafb7db1099049968905c6e6
```

### 서비스 토큰 (설정됨)
- **GITHUB_TOKEN**: `ghp_xxx_REDACTED`

---

## 3. 테스트 요청 사항

### 3.1 tools/list 테스트
```bash
curl -X POST "http://localhost:3000/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mcphub_eafb7db1099049968905c6e6" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

**예상 결과**: 58개 도구 목록 반환 (Jira, Confluence, GitHub, kt-membership)

### 3.2 tools/call 테스트 (GitHub)
```bash
curl -X POST "http://localhost:3000/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mcphub_eafb7db1099049968905c6e6" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_pull_requests",
      "arguments": {
        "owner": "langchain-ai",
        "repo": "langgraph",
        "state": "open",
        "limit": 5
      }
    }
  }'
```

### 3.3 tools/call 테스트 (kt-membership)
```bash
curl -X POST "http://localhost:3000/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mcphub_eafb7db1099049968905c6e6" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "membership_overview",
      "arguments": {}
    }
  }'
```

---

## 4. 확인 사항

### ✅ 정상 동작해야 하는 것
- [ ] `tools/list` 호출 시 모든 MCP 서버의 도구 목록 반환
- [ ] `tools/call` 호출 시 해당 도구 실행 및 결과 반환
- [ ] MCPHub Key 인증 정상 동작
- [ ] 서비스 토큰이 MCP 서버로 전달

### ❌ 지원하지 않는 것 (Stateless 특성)
- Server→Client 실시간 알림
- 세션 기반 상태 유지
- `Mcp-Session-Id` 헤더

---

## 5. 알려진 이슈

### GitHub MCP 서버
- **상태**: ✅ 정상 동작 (이미지 재배포 완료: `giglepeople/github-mcp-server:v1`)
- **직접 호출**: ✅ 성공
- **MCPHub 경유**: ✅ 성공 (langgraph PR 조회 테스트 완료)

### Jira/Confluence MCP 서버
- **상태**: ⚠️ IP 허용 목록 문제
- Atlassian 측 정책 변경으로 접근 제한

### kt-membership 서버
- **상태**: ✅ 정상 동작

---

## 6. 피드백 요청

테스트 후 다음 사항을 알려주세요:
1. `tools/list` 정상 동작 여부
2. `tools/call` 정상 동작 여부
3. 응답 시간 (타임아웃 발생 여부)
4. 에러 발생 시 에러 메시지

---

## 7. 연락처

문의사항은 Slack #mcphub-dev 채널로 연락 부탁드립니다.

감사합니다!
MCPHub Team
