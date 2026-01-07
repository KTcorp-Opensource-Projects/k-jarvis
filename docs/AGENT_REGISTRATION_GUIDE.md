# 🤖 K-Jarvis Agent 등록 가이드

**버전**: 1.0.0  
**최종 수정일**: 2024-12-12  
**작성팀**: Orchestrator Team

---

## 📋 개요

이 문서는 K-Jarvis Orchestrator에 새로운 AI Agent를 등록하는 방법을 설명합니다.
Agent 개발자는 이 가이드를 따라 Agent를 개발하고 Orchestrator에 등록할 수 있습니다.

---

## 🏗️ 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                    K-Jarvis 플랫폼                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [사용자] ──► [Orchestrator] ──► [Your Agent] ──► [MCPHub]      │
│                    │                  │              │          │
│                    │                  │              ▼          │
│              라우팅/체이닝        A2A Protocol    MCP Server     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ 필수 요구사항

### 1. A2A Protocol 엔드포인트

| 엔드포인트 | 메서드 | 설명 | 필수 |
|-----------|--------|------|:----:|
| `/.well-known/agent.json` | GET | Agent Card (메타데이터) | ✅ |
| `/tasks/send` | POST | 메시지 처리 | ✅ |
| `/tasks/sendSubscribe` | POST | 스트리밍 응답 (SSE) | ⚠️ 권장 |
| `/health` | GET | 헬스체크 | ⚠️ 권장 |

### 2. Agent Card (`/.well-known/agent.json`)

```json
{
  "name": "Your Agent Name",
  "description": "Agent의 역할과 기능을 설명합니다. 라우팅에 사용되므로 상세히 작성하세요.",
  "url": "http://your-agent-url:port",
  "version": "1.0.0",
  
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "stateTransitionHistory": false
  },
  
  "skills": [
    {
      "id": "skill_search",
      "name": "검색 기능",
      "description": "데이터를 검색합니다",
      "tags": ["search", "query"]
    },
    {
      "id": "skill_create",
      "name": "생성 기능", 
      "description": "새로운 항목을 생성합니다",
      "tags": ["create", "new"]
    }
  ],
  
  "routing": {
    "domain": "your-domain",
    "category": "category-name",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "capabilities": ["search", "create", "update"]
  },
  
  "requirements": {
    "mcpHubToken": true,
    "mcpServers": ["your-mcp-server-name"]
  }
}
```

### 3. 필수 필드 설명

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `name` | string | Agent 표시 이름 | "Jira AI Agent" |
| `description` | string | Agent 기능 설명 (라우팅에 사용) | "Jira 이슈 관리..." |
| `url` | string | Agent 서버 URL | "http://localhost:5011" |
| `version` | string | Agent 버전 | "1.0.0" |
| `capabilities.streaming` | boolean | 스트리밍 지원 여부 | true |
| `skills` | array | Agent가 제공하는 스킬 목록 | [...] |
| `routing.keywords` | array | 라우팅 키워드 | ["jira", "issue", "ticket"] |
| `requirements.mcpHubToken` | boolean | MCPHub 토큰 필요 여부 | true |
| `requirements.mcpServers` | array | 필요한 MCP 서버 목록 | ["mcp-atlassian-jira"] |

---

## 🔌 API 스펙

### POST `/tasks/send`

**요청:**
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/send",
  "params": {
    "id": "task-uuid",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "사용자 메시지 내용"
        }
      ]
    }
  }
}
```

**응답:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "id": "task-uuid",
    "status": {
      "state": "completed"
    },
    "artifacts": [
      {
        "parts": [
          {
            "type": "text",
            "text": "Agent 응답 내용"
          }
        ]
      }
    ]
  }
}
```

**에러 응답:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "서비스 토큰이 등록되지 않았습니다",
    "data": {
      "help": "MCPHub(http://localhost:5173)에서 토큰을 등록해주세요"
    }
  }
}
```

---

## 🔐 Option C: X-MCPHub-User-Id 헤더 처리

### 개요

K-Jarvis는 **Option C (MCPHub Proxy)** 아키텍처를 사용합니다.
Orchestrator가 사용자의 K-Auth ID를 Agent에게 전달하고, Agent는 이를 MCPHub에 전달하여 사용자별 서비스 토큰을 조회합니다.

### 토큰 플로우

```
User (K-Auth 로그인)
    │
    ▼
Orchestrator (JWT에서 kauth_user_id 추출)
    │
    │  X-MCPHub-User-Id: "user-kauth-uuid"
    ▼
Your Agent
    │
    │  Authorization: Bearer {AGENT_MCPHUB_KEY}
    │  X-MCPHub-User-Id: "user-kauth-uuid"
    ▼
MCPHub (사용자별 서비스 토큰 조회/적용)
    │
    ▼
External API (Jira, GitHub, Confluence...)
```

### Agent 구현 예시 (Python)

```python
from fastapi import FastAPI, Request, Header
from typing import Optional

app = FastAPI()

@app.post("/tasks/send")
async def tasks_send(
    request: Request,
    x_mcphub_user_id: Optional[str] = Header(None, alias="X-MCPHub-User-Id")
):
    # 1. X-MCPHub-User-Id 헤더 추출
    mcphub_user_id = x_mcphub_user_id
    
    # 2. MCPHub 호출 시 헤더 전달
    headers = {
        "Authorization": f"Bearer {os.environ['MCP_HUB_TOKEN']}",
        "X-MCPHub-User-Id": mcphub_user_id  # 반드시 전달!
    }
    
    # 3. MCPHub API 호출
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MCP_HUB_URL}/mcp/tools/call",
            headers=headers,
            json=tool_request
        )
    
    return response.json()
```

### 주의사항

⚠️ **Lazy Initialization 필수!**

Agent 초기화 시 `X-MCPHub-User-Id`가 없을 수 있습니다.
MCPHub 연결은 **요청 처리 시점**에 수행해야 합니다.

```python
# ❌ 잘못된 예시
class Agent:
    def __init__(self):
        self.mcp_client = MCPClient()
        self.mcp_client.connect()  # 초기화 시점에 연결 (X)

# ✅ 올바른 예시
class Agent:
    def __init__(self):
        self.mcp_client = MCPClient()
        # connect()는 process_message()에서 호출
    
    async def process_message(self, message, mcphub_user_id):
        await self.mcp_client.connect(mcphub_user_id)  # 요청 시점에 연결 (O)
```

---

## 🛠️ 환경 변수

Agent 서버에 필요한 환경 변수:

```bash
# MCPHub 연동 (필수)
MCP_HUB_URL=http://localhost:3000/mcp
MCP_HUB_TOKEN=mcphub_xxxxxxxx  # Agent 전용 MCPHub Key

# LLM Provider (필수)
LLM_PROVIDER=azure  # or openai
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_ENDPOINT=xxx
AZURE_OPENAI_DEPLOYMENT_NAME=xxx

# 서버 설정
PORT=5010
```

---

## 📝 Orchestrator 등록 절차

### 방법 1: Admin UI에서 등록

1. Orchestrator Admin UI 접속 (`http://localhost:4000`)
2. Admin 계정으로 로그인
3. "Agent 관리" 메뉴 이동
4. "새 Agent 등록" 클릭
5. Agent URL 입력 (예: `http://localhost:5010`)
6. "등록" 클릭 → Agent Card 자동 조회

### 방법 2: API로 등록

```bash
curl -X POST http://localhost:4001/api/agents/register \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:5010"
  }'
```

### 등록 후 확인

```bash
# Agent 목록 조회
curl http://localhost:4001/api/agents \
  -H "Authorization: Bearer {token}"

# Agent Card 직접 확인
curl http://localhost:5010/.well-known/agent.json
```

---

## 🧪 테스트 체크리스트

Agent 등록 전 확인사항:

| # | 항목 | 확인 |
|---|------|:----:|
| 1 | `/.well-known/agent.json` 응답 확인 | [ ] |
| 2 | `/tasks/send` 정상 응답 | [ ] |
| 3 | `/health` 엔드포인트 | [ ] |
| 4 | X-MCPHub-User-Id 헤더 처리 | [ ] |
| 5 | MCPHub 연동 테스트 | [ ] |
| 6 | 토큰 미등록 시 친절한 에러 메시지 | [ ] |
| 7 | 스트리밍 응답 (선택) | [ ] |

### 테스트 명령어

```bash
# 1. Agent Card 확인
curl http://localhost:5010/.well-known/agent.json | jq

# 2. 헬스체크
curl http://localhost:5010/health

# 3. 메시지 전송 테스트
curl -X POST http://localhost:5010/tasks/send \
  -H "Content-Type: application/json" \
  -H "X-MCPHub-User-Id: test-user-id" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tasks/send",
    "params": {
      "id": "test-task-1",
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "테스트 메시지"}]
      }
    }
  }'
```

---

## ❌ 에러 코드

| 코드 | 메시지 | 설명 |
|------|--------|------|
| -32001 | Token not registered | 서비스 토큰 미등록 |
| -32002 | MCPHub connection failed | MCPHub 연결 실패 |
| -32003 | Tool execution failed | MCP 도구 실행 실패 |
| -32600 | Invalid request | 잘못된 요청 형식 |
| -32603 | Internal error | 내부 오류 |

---

## 📚 참고 자료

- [A2A Protocol 스펙](https://github.com/google/A2A)
- [MCPHub Integration Guide](../../mcphubproject/mcphub/docs/MCPHUB_INTEGRATION_GUIDE.md)
- [Confluence Agent 예제](../../Confluence-AI-Agent/)

---

## 📞 문의

- **Orchestrator Team**: #orchestrator-dev
- **Agent Team**: #agent-dev
- **MCPHub Team**: #mcphub-dev

---

*K-Jarvis Orchestrator Team*  
*2024-12-12*


