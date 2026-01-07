# Agent Team 액션 아이템 확인 및 일정 동의

**작성일**: 2026-01-05  
**작성팀**: Agent Team  
**대상**: Orchestrator Team, MCPHub Team  
**상태**: ✅ 액션 아이템 확인 완료

---

## 📋 검토 문서

`TO_ALL_TEAMS_E2E_REVIEW_RESPONSE_AND_ACTION_ITEMS_20260105.md`

---

## ✅ Agent Team 액션 아이템 확인

### 할당된 작업

| # | 작업 | 우선순위 | 마감 | 상태 |
|---|------|----------|------|------|
| 1 | docker-compose 네트워크 설정 추가 | 🔴 높음 | 2026-01-08 | ✅ **수락** |
| 2 | 전용 MCPHub Key 설정 | 🔴 높음 | 2026-01-09 | ✅ **수락** (Key 발급 대기) |
| 3 | 도구별 타임아웃 설정 | 🟡 중간 | 2026-01-10 | ✅ **수락** |
| 4 | 에러 핸들링 개선 | 🟡 중간 | 2026-01-12 | ✅ **수락** |
| 5 | 재시도 로직 추가 | 🟡 중간 | 2026-01-12 | ✅ **수락** |
| 6 | Atlassian Agent 테스트 | 🟡 중간 | TBD | ✅ **수락** (MCP Server 복구 대기) |

---

## 🔧 즉시 진행 가능한 작업

### 1. docker-compose 네트워크 설정 추가

**현재 상태**: `mcphub_kjarvis-network`만 연결  
**변경 계획**: `mcphub_default` 네트워크 추가

```yaml
# docker-compose.agents.yml 수정 예정
networks:
  mcphub_default:
    external: true
  mcphub_kjarvis-network:
    external: true

services:
  github-agent:
    networks:
      - mcphub_default        # MCPHub 통신용
      - mcphub_kjarvis-network # Orchestrator 통신용
```

**예상 완료**: 2026-01-06 (내일)

---

### 2. 도구별 타임아웃 설정

**현재 상태**: 고정 30초  
**변경 계획**: 도구별 타임아웃 분리

```python
# 도구별 타임아웃 설정
TOOL_TIMEOUTS = {
    "github_list_pull_requests": 60.0,
    "github_get_file_contents": 45.0,
    "jira_search": 45.0,
    "confluence_search": 45.0,
    "default": 30.0
}
```

**예상 완료**: 2026-01-09

---

### 3. 에러 핸들링 개선

**현재 상태**: 단순 예외 처리  
**변경 계획**: 구조화된 에러 클래스 및 재시도 로직

```python
class MCPError(Exception):
    def __init__(self, code: int, message: str, retryable: bool = False):
        self.code = code
        self.message = message
        self.retryable = retryable

class MCPTimeoutError(MCPError):
    pass

class MCPAuthError(MCPError):
    pass

# 재시도 로직
@retry(
    max_attempts=3,
    backoff=exponential(base=1, max=10),
    retry_on=(MCPTimeoutError,)
)
async def call_tool(self, name: str, arguments: dict):
    ...
```

**예상 완료**: 2026-01-11

---

## ⏳ MCPHub 팀 대기 작업

### 전용 MCPHub Key 설정

| 에이전트 | 구독 MCP 서버 | Key 발급 상태 |
|---------|--------------|--------------|
| GitHub Agent | `github-mcp-server` | ⏳ 대기 |
| Sample Agent | `mcp-atlassian`, `kt-membership` | ⏳ 대기 |
| Confluence Agent | `mcp-atlassian` (Confluence) | ⏳ 대기 |
| Jira Agent | `mcp-atlassian` (Jira) | ⏳ 대기 |

**MCPHub 팀 요청**: Key 발급 후 알려주시면 즉시 적용하겠습니다.

---

## 📊 역질문 답변 확인

### Q1. K-Auth JWT 전달 가능 여부

**Orchestrator 팀 답변**: ✅ 가능

```python
headers["Authorization"] = f"Bearer {kauth_jwt_token}"  # 추가 가능
```

**Agent Team 의견**: 
- ✅ 방안 A (JWT 전달) 동의
- Agent는 수신한 JWT를 그대로 MCPHub에 전달하면 됨
- 추가 개발 최소화

---

### Q2. 에이전트 선택 로직

**Orchestrator 팀 답변**: LLM + RAG 하이브리드 라우팅

**Agent Team 확인**: 
- ✅ 이해했습니다
- Agent Card 정보가 정확해야 올바른 라우팅 가능
- Agent Card 업데이트 필요 시 알려주세요

---

### Q3. 타임아웃 설정

**Orchestrator 팀 답변**: 현재 60초 → 90초 조정 예정

**Agent Team 의견**:
- ✅ 90초 적절
- Agent 내부 타임아웃은 80초로 설정하여 Orchestrator보다 먼저 타임아웃 방지

---

## 🔐 보안 방안 의견

### X-MCPHub-User-Id 보안 강화

| 방안 | Agent Team 의견 |
|------|----------------|
| A. JWT 토큰 전달 | ✅ **선호** - 추가 개발 최소화 |
| B. HMAC 서명 | 🟡 가능 - 공유 키 관리 필요 |
| C. mTLS | 🟡 가능 - 인증서 관리 복잡 |

**Agent Team 결론**: **방안 A (JWT 전달) 동의**

---

## 📅 Agent Team 일정표

| 날짜 | 작업 |
|------|------|
| **2026-01-06** | docker-compose 네트워크 설정 추가 |
| **2026-01-07** | 진행 상황 점검 회의 참석 |
| **2026-01-08** | 네트워크 설정 완료, 테스트 |
| **2026-01-09** | 전용 MCPHub Key 설정 (Key 발급 후) |
| **2026-01-10** | 도구별 타임아웃 설정 완료 |
| **2026-01-11-12** | 에러 핸들링 및 재시도 로직 |
| **TBD** | Atlassian Agent 테스트 (MCP Server 복구 후) |

---

## ❓ 추가 확인 필요 사항

### MCPHub 팀에게

1. **에이전트별 Key 발급 일정**
   - GitHub Agent Key: 언제?
   - Sample Agent Key: 언제?

2. **Atlassian MCP Server 연결 복구 일정**
   - 현재 `Reconnecting` 상태
   - Confluence/Jira Agent 테스트 대기 중

3. **토큰 폴백 로직 제거 시 에러 메시지**
   - 사용자에게 어떤 메시지가 표시되나요?
   - Agent가 이 에러를 어떻게 처리해야 하나요?

### Orchestrator 팀에게

1. **JWT 토큰 전달 구현 일정**
   - 방안 A 선택 시 언제부터 JWT가 전달되나요?
   - Agent에서 테스트할 수 있는 시점은?

2. **멀티 에이전트 체이닝 (Phase 2)**
   - 예상 일정은?
   - Agent 측에서 준비해야 할 사항은?

---

## 🎯 결론

**Agent Team은 모든 할당된 액션 아이템을 수락합니다.**

- ✅ 일정 동의
- ✅ 보안 방안 A (JWT 전달) 동의
- ✅ 프로덕션 준비 목표 동의

**협조 부탁드립니다!** 🚀

---

## 📞 연락처

**Agent Team**  
Slack: #agent-dev

---

**다음 회의**: 2026-01-07 (화) - 진행 상황 점검

