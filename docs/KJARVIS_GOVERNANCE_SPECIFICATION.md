# K-Jarvis 생태계 거버넌스 명세서

**버전**: 1.0.0  
**작성일**: 2026-01-05  
**담당**: Orchestrator Team

---

## 📋 개요

이 문서는 K-Jarvis 생태계에서 Agent와 MCP Server를 개발할 때 준수해야 하는 거버넌스 규칙을 정의합니다.

---

## 🔷 1. Agent Card 거버넌스

### 1.1 필수 필드

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `name` | string | 에이전트 이름 (영문, 공백 가능) | "GitHub AI Agent" |
| `description` | string | 에이전트 설명 (50자 이상 권장) | "GitHub 저장소 관리를 위한 AI 에이전트" |
| `version` | string | 시맨틱 버전 | "1.0.0" |
| `protocolVersion` | string | A2A 프로토콜 버전 | "0.3.0" |
| `skills` | array | 스킬 목록 (최소 1개) | 아래 참조 |

### 1.2 Skill 정의 규칙

```json
{
  "skills": [
    {
      "id": "get_pull_requests",
      "name": "get_pull_requests",
      "description": "GitHub 저장소의 Pull Request 목록을 조회합니다",
      "tags": ["github", "pr", "pull-request"],
      "examples": [
        "microsoft/vscode 저장소의 최근 PR 조회해줘",
        "langchain-ai/langgraph의 오픈된 PR 알려줘"
      ],
      "inputModes": ["text/plain"],
      "outputModes": ["text/plain", "application/json"]
    }
  ]
}
```

#### Skill 필수 필드
| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | ✅ | 스킬 고유 식별자 (snake_case) |
| `name` | ✅ | 스킬 이름 |
| `description` | ✅ | 스킬 설명 (30자 이상) |
| `tags` | ⚠️ 권장 | 라우팅용 태그 (한/영) |
| `examples` | ⚠️ 권장 | 사용 예시 (RAG 라우팅에 활용) |

### 1.3 라우팅 메타데이터 (routing)

```json
{
  "routing": {
    "domain": "project_management",
    "category": "github",
    "keywords": ["github", "깃허브", "pr", "풀리퀘스트", "이슈", "커밋"],
    "capabilities": ["search", "create", "update"]
  }
}
```

| 필드 | 설명 |
|------|------|
| `domain` | 도메인 분류: `project_management`, `documentation`, `communication`, `development` |
| `category` | 서비스 카테고리: `github`, `jira`, `confluence`, `slack` |
| `keywords` | 라우팅 키워드 (한국어/영어 모두 포함 권장) |
| `capabilities` | 지원 기능: `search`, `create`, `update`, `delete` |

### 1.4 MCPHub 요구사항 (requirements)

```json
{
  "requirements": {
    "mcpHubToken": true,
    "mcpServers": ["github-mcp-server", "mcp-atlassian"]
  }
}
```

---

## 🔷 2. A2A 프로토콜 거버넌스

### 2.1 메서드 명명 규칙

| 표준 메서드 | 설명 |
|------------|------|
| `SendMessage` | 메시지 전송 (PascalCase) |
| `GetTaskStatus` | 작업 상태 조회 |
| `CancelTask` | 작업 취소 |

**⚠️ 레거시 호환**: `message/send` 형식도 지원하나, 신규 개발 시 PascalCase 사용 권장

### 2.2 요청 형식

```json
{
  "jsonrpc": "2.0",
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        { "text": "microsoft/vscode 저장소의 최근 PR 조회해줘" }
      ]
    }
  },
  "id": "req-001"
}
```

### 2.3 응답 형식

#### 성공 응답
```json
{
  "jsonrpc": "2.0",
  "result": {
    "message": {
      "role": "agent",
      "parts": [
        { "text": "조회 결과입니다..." }
      ]
    }
  },
  "id": "req-001"
}
```

#### 에러 응답
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32000,
    "message": "Agent execution failed",
    "data": {
      "errorCode": "TOOL_EXECUTION_FAILED",
      "details": "GitHub API rate limit exceeded"
    }
  },
  "id": "req-001"
}
```

---

## 🔷 3. 에러 코드 표준

| 코드 | 이름 | 설명 |
|------|------|------|
| `AGENT_NOT_FOUND` | 에이전트 없음 | 요청된 에이전트를 찾을 수 없음 |
| `SKILL_NOT_FOUND` | 스킬 없음 | 요청된 스킬을 찾을 수 없음 |
| `TOOL_EXECUTION_FAILED` | 도구 실행 실패 | MCP 도구 호출 실패 |
| `MCPHUB_CONNECTION_FAILED` | MCPHub 연결 실패 | MCPHub 서버 연결 불가 |
| `MCPHUB_TOKEN_MISSING` | 토큰 없음 | 사용자의 서비스 토큰 미등록 |
| `AUTHENTICATION_FAILED` | 인증 실패 | JWT 토큰 검증 실패 |
| `RATE_LIMIT_EXCEEDED` | 요청 제한 초과 | API 호출 제한 초과 |
| `TIMEOUT` | 타임아웃 | 요청 처리 시간 초과 (90초) |

---

## 🔷 4. 인증 거버넌스

### 4.1 K-Auth JWT 토큰

모든 요청에는 K-Auth에서 발급한 JWT 토큰이 필요합니다.

```
Authorization: Bearer <JWT_TOKEN>
```

JWT Payload 구조:
```json
{
  "sub": "username",
  "user_id": "uuid",
  "kauth_user_id": "uuid",
  "is_admin": false,
  "exp": 1234567890
}
```

### 4.2 X-MCPHub-User-Id 헤더

Agent가 MCPHub를 호출할 때, Orchestrator가 전달한 사용자 ID를 포함해야 합니다.

```
X-MCPHub-User-Id: <kauth_user_id>
```

---

## 🔷 5. 로깅 표준

### 5.1 로그 레벨

| 레벨 | 용도 |
|------|------|
| `DEBUG` | 개발/디버깅용 상세 로그 |
| `INFO` | 정상 동작 로그 |
| `WARNING` | 주의 필요 상황 |
| `ERROR` | 오류 발생 |
| `CRITICAL` | 시스템 장애 |

### 5.2 로그 형식

```json
{
  "timestamp": "2026-01-05T12:00:00.000Z",
  "level": "INFO",
  "service": "github-agent",
  "request_id": "req-001",
  "user_id": "uuid",
  "message": "Skill execution started",
  "data": {
    "skill": "get_pull_requests",
    "params": {"repo": "microsoft/vscode"}
  }
}
```

---

## 🔷 6. 헬스체크 표준

### 6.1 엔드포인트

모든 Agent는 다음 엔드포인트를 제공해야 합니다:

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/.well-known/agent.json` | GET | Agent Card 반환 |
| `/health` | GET | 헬스체크 |

### 6.2 헬스체크 응답

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "dependencies": {
    "mcphub": "connected",
    "database": "connected"
  }
}
```

---

## 🔷 7. SDK에서 제공할 검증 기능

### 7.1 Agent Card Validator

```python
from k_jarvis.validation import AgentCardValidator

validator = AgentCardValidator()
result = validator.validate("agent.json")

if not result.is_valid:
    for error in result.errors:
        print(f"❌ {error.field}: {error.message}")
```

### 7.2 검증 항목

| 항목 | 검증 내용 |
|------|----------|
| 필수 필드 | name, description, version, skills |
| Skill 형식 | id, name, description 필수 |
| 버전 형식 | 시맨틱 버전 (X.Y.Z) |
| URL 형식 | 유효한 HTTP(S) URL |
| 라우팅 메타데이터 | domain, keywords 권장 |

---

## 📝 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2026-01-05 | 초기 버전 |

---

**Orchestrator Team**  
K-Jarvis 생태계 거버넌스 담당


