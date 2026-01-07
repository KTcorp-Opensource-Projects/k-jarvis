# K-ARC Team → All Teams: K-Jarvis 풀 통합 테스트 준비 완료

**작성일**: 2025-12-17  
**작성팀**: K-ARC Team  
**수신팀**: Orchestrator Team, Agent Team  
**상태**: ✅ 모든 서버 기동 완료

---

## 🚀 서버 상태 요약

| 서버 | 포트 | 상태 | 엔드포인트 |
|------|------|------|-----------|
| **K-ARC Backend** | 3000 | ✅ Running | http://localhost:3000 |
| **K-ARC Frontend** | 5173 | ✅ Running | http://localhost:5173 |
| **Demo MCP Server (TS)** | 8080 | ✅ Running | http://localhost:8080 |
| **Demo MCP Server (Python)** | 8081 | ✅ Running | http://localhost:8081 |
| **PostgreSQL** | 5432 | ✅ Running | localhost:5432 |

---

## 📡 K-ARC Backend API 정보

### 기본 정보

| 항목 | 값 |
|------|-----|
| **Base URL** | `http://localhost:3000` |
| **API Prefix** | `/api` |
| **Health Check** | `GET /api/health` |
| **Swagger UI** | `http://localhost:3000/api-docs` |

### 주요 엔드포인트

#### 인증 (Auth)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/auth/login` | 로그인 (JWT 발급) |
| POST | `/api/auth/register` | 회원가입 |
| GET | `/api/auth/me` | 현재 사용자 정보 |

#### MCP (도구 호출)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/mcp` | MCP JSON-RPC 엔드포인트 |
| GET | `/api/mcp/servers` | 서버 목록 조회 |
| POST | `/api/mcp/tools/list` | 도구 목록 조회 |
| POST | `/api/mcp/tools/call` | 도구 호출 |

#### SSE (Server-Sent Events)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/sse` | SSE 스트리밍 연결 |

### 인증 헤더

```
Authorization: Bearer <JWT_TOKEN>
X-MCPHub-User-Id: <user_id>  # K-ARC가 MCP 서버로 전달
X-Request-Id: <request_id>   # 요청 추적용
```

### 테스트 계정

| 계정 | 사용자명 | 비밀번호 | 권한 |
|------|---------|---------|------|
| **관리자** | jungchihoon | 1234 | Admin |
| **일반 사용자** | testkarc | testpass123 | User |

---

## 🔧 Demo MCP Server 정보

### TypeScript 버전 (포트 8080)

| 항목 | 값 |
|------|-----|
| **Base URL** | `http://localhost:8080` |
| **MCP Endpoint** | `POST /mcp` |
| **Health Check** | `GET /health` |

#### 제공 도구

| 도구 | 설명 | 필요 토큰 |
|------|------|----------|
| `calculate` | 사칙연산 | ❌ 없음 |
| `get_user_info` | 사용자 정보 | ✅ 인증 필요 |
| `fetch_data` | 외부 데이터 조회 | ✅ EXTERNAL_API_TOKEN |

### Python 버전 (포트 8081)

| 항목 | 값 |
|------|-----|
| **Base URL** | `http://localhost:8081` |
| **MCP Endpoint** | `POST /mcp` |
| **Health Check** | `GET /health` |

#### 제공 도구 (동일)

| 도구 | 설명 | 필요 토큰 |
|------|------|----------|
| `calculate` | 사칙연산 | ❌ 없음 |
| `get_user_info` | 사용자 정보 | ✅ 인증 필요 |
| `fetch_data` | 외부 데이터 조회 | ✅ EXTERNAL_API_TOKEN |

---

## 🧪 테스트 시나리오

### 시나리오 1: 기본 도구 호출 (인증 불필요)

```bash
# TypeScript 버전
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "calculate",
      "arguments": {"operation": "add", "a": 10, "b": 5}
    },
    "id": 1
  }'

# 예상 결과: {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"{'expression': '10 add 5', 'result': 15}"}]},"id":1}
```

### 시나리오 2: 인증 필요 도구 (X-MCPHub-User-Id 전달)

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "X-MCPHub-User-Id: test-user-123" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_user_info",
      "arguments": {}
    },
    "id": 2
  }'

# 예상 결과: 사용자 정보 반환 (user_id, timestamp, has_service_tokens 등)
```

### 시나리오 3: 서비스 토큰 필요 도구

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "X-MCPHub-User-Id: test-user-123" \
  -H "X-Service-EXTERNAL-API-TOKEN: my-secret-token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "fetch_data",
      "arguments": {"endpoint": "/api/users"}
    },
    "id": 3
  }'

# 예상 결과: 데이터 조회 성공
```

### 시나리오 4: 토큰 없이 호출 (에러 테스트)

```bash
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_user_info",
      "arguments": {}
    },
    "id": 4
  }'

# 예상 결과: {"jsonrpc":"2.0","error":{"code":-32001,"message":"인증이 필요합니다"},"id":4}
```

---

## 🔗 K-ARC Gateway → MCP Server 헤더 전달

K-ARC Backend가 MCP 서버로 요청을 전달할 때 포함하는 헤더:

| 헤더 | 설명 | 예시 |
|------|------|------|
| `X-MCPHub-User-Id` | K-ARC 사용자 ID | `user-123` |
| `X-KAuth-User-Id` | K-Auth SSO ID | `kauth-456` |
| `X-Request-Id` | 요청 추적 ID | `req-789` |
| `X-Service-{NAME}` | 서비스 토큰 | `X-Service-JIRA-TOKEN: abc` |

**서비스 토큰 변환 규칙**:
```
X-Service-JIRA-TOKEN     → JIRA_TOKEN
X-Service-EXTERNAL-API-TOKEN → EXTERNAL_API_TOKEN
```

---

## 📊 Agent Team을 위한 정보

### k-jarvis-utils 연동

```python
from k_jarvis_utils import MCPHubClient, KJarvisHeaders

# K-ARC 클라이언트 생성
client = MCPHubClient(base_url="http://localhost:3000")

# 헤더 설정
headers = KJarvisHeaders(
    user_id="test-user-123",
    request_id="req-001"
)

# 도구 호출
result = await client.call_tool(
    server_name="k-arc-demo-mcp-server",
    tool_name="calculate",
    arguments={"operation": "add", "a": 10, "b": 5},
    headers=headers
)
```

### Agent → K-ARC → MCP Server 플로우

```
┌─────────────┐      ┌─────────────────┐      ┌──────────────────┐
│   Agent     │      │    K-ARC        │      │   MCP Server     │
│             │      │   Gateway       │      │                  │
└─────────────┘      └─────────────────┘      └──────────────────┘
       │                     │                        │
       │ 1. tools/call       │                        │
       │ X-MCPHub-User-Id    │                        │
       │ ─────────────────▶ │                        │
       │                     │ 2. tools/call          │
       │                     │ X-MCPHub-User-Id       │
       │                     │ X-Service-*            │
       │                     │ ──────────────────────▶│
       │                     │                        │
       │                     │ 3. 결과                │
       │                     │ ◀──────────────────────│
       │ 4. 결과             │                        │
       │ ◀───────────────── │                        │
       │                     │                        │
```

---

## 📊 Orchestrator Team을 위한 정보

### 전체 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                     K-Jarvis 생태계                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐   ┌───────────────┐   ┌─────────────────┐   │
│  │ Orchestrator │──▶│    Agent      │──▶│    K-ARC        │   │
│  │              │   │               │   │   (MCPHub)      │   │
│  └──────────────┘   └───────────────┘   └─────────────────┘   │
│         │                  │                    │             │
│         │                  │                    │             │
│         ▼                  ▼                    ▼             │
│    K-Auth SSO        k-jarvis-utils      MCP Servers         │
│                                          ┌─────────────────┐ │
│                                          │ Demo TS (8080)  │ │
│                                          │ Demo Py (8081)  │ │
│                                          │ Jira, GitHub... │ │
│                                          └─────────────────┘ │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 통합 테스트 엔드포인트

| 서비스 | URL | 용도 |
|--------|-----|------|
| K-ARC Backend | http://localhost:3000 | API Gateway |
| K-ARC Frontend | http://localhost:5173 | 웹 UI |
| Demo MCP (TS) | http://localhost:8080 | 테스트용 MCP |
| Demo MCP (Py) | http://localhost:8081 | 테스트용 MCP |

---

## ✅ 체크리스트

### K-ARC Team (완료)

- [x] K-ARC Backend 기동 (포트 3000)
- [x] K-ARC Frontend 기동 (포트 5173)
- [x] Demo MCP Server (TS) 기동 (포트 8080)
- [x] Demo MCP Server (Py) 기동 (포트 8081)
- [x] PostgreSQL 기동 (포트 5432)
- [x] 테스트 계정 준비
- [x] 문서 공유

### Agent Team (대기)

- [ ] Sample Agent 기동
- [ ] k-jarvis-utils 연동 테스트
- [ ] K-ARC → MCP Server 플로우 테스트

### Orchestrator Team (대기)

- [ ] 전체 통합 테스트 시작
- [ ] 각 시나리오별 검증
- [ ] 테스트 결과 공유

---

## 📞 연락처

문제 발생 시 즉시 문서로 공유해주세요!

---

## 📝 추가 참고 문서

| 문서 | 위치 |
|------|------|
| K-ARC MCP 서버 개발 가이드 | [Confluence](https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/566471017) |
| k-arc-utils README | `/chihoon/k-arc-utils-python/README.md` |
| Swagger API 문서 | http://localhost:3000/api-docs |

---

**K-ARC Team** 🌀

**풀 통합 테스트 준비 완료! 테스트를 시작해주세요!** 🚀

