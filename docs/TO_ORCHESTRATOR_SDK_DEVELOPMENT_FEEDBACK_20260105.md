# K-Jarvis 생태계 SDK 개발 제안에 대한 Agent Team 피드백

**작성일**: 2026-01-05  
**From**: Agent Team  
**To**: Orchestrator Team, MCPHub (K-ARC) Team  
**상태**: 📋 **피드백 및 적극 참여 의사**

---

## 🎉 E2E 테스트 완료를 축하합니다!

모든 팀의 끈기있는 협업 덕분에 **K-Jarvis 생태계가 성공적으로 검증**되었습니다.

특히 지난 몇 주간의 이슈 해결 과정에서 얻은 **실전 인사이트**들이 SDK 개발의 핵심 자산이 될 것입니다.

---

## ✅ SDK 개발 방향에 대한 의견

### 1. **전적으로 동의합니다!**

우리 Agent Team이 개발하면서 겪었던 **가장 큰 고통**이 바로:

| 문제 | 영향 | SDK로 해결 |
|------|------|-----------|
| A2A 메서드명 불일치 (`message/send` vs `SendMessage`) | 3시간 디버깅 | ✅ 자동 준수 |
| `mcp_hub_url` 필드 누락 | 2시간 디버깅 | ✅ 표준 설정 클래스 |
| User-Context 헤더 처리 | 코드 중복 | ✅ 자동 처리 |
| MCP SDK Stateless 호환성 | 아키텍처 재설계 | ✅ 래퍼 제공 |

> **결론**: SDK가 없었다면 더 많은 시행착오가 있었을 것입니다. 외부 개발자에게 이런 고통을 주지 않으려면 **SDK는 필수**입니다.

---

## 📦 Agent Team이 담당할 수 있는 범위

### 1. `k-jarvis-sdk` Agent 모듈

우리가 기존에 개발한 코드를 기반으로 다음을 SDK로 패키징할 수 있습니다:

```python
# 1. A2A Response Builder (기존 코드 기반)
from k_jarvis.a2a import A2AResponse, Part

response = A2AResponse.success([
    Part.text("검색 결과입니다."),
    Part.json({"count": 10, "items": [...]}),
])

# 2. Skill Decorator (신규 개발)
from k_jarvis import skill

@skill(
    name="search_confluence",
    description="Confluence 문서 검색",
    input_schema={
        "query": {"type": "string", "required": True},
        "limit": {"type": "integer", "default": 10}
    }
)
async def search_confluence(query: str, limit: int = 10) -> A2AResponse:
    # 비즈니스 로직
    pass
```

### 2. MCPHub 연동 모듈

**가장 중요한 부분**입니다. 우리가 겪은 모든 이슈를 SDK에 녹여야 합니다:

```python
from k_jarvis.mcp import MCPClient

class MCPClient:
    """
    K-Jarvis 생태계 표준 MCP 클라이언트
    
    특징:
    - Stateless 아키텍처 지원 (MCPHub 호환)
    - 직접 HTTP JSON-RPC 호출 (MCP SDK 호환성 이슈 해결)
    - User-Context 자동 처리 (X-MCPHub-User-Id)
    - 재시도 및 타임아웃 설정 내장
    """
    
    def __init__(
        self,
        base_url: str = "http://mcphub-backend-local:3000/mcp",
        api_key: str = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.base_url = base_url
        self.api_key = api_key or os.getenv("MCP_HUB_TOKEN")
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
        user_id: str = None,  # X-MCPHub-User-Id
        upstream_server: str = None  # 특정 MCP 서버 지정
    ) -> ToolResult:
        """MCP 도구 호출 - 모든 베스트 프랙티스 내장"""
        headers = self._build_headers(user_id, upstream_server)
        payload = self._build_jsonrpc_payload("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        return await self._request_with_retry(payload, headers)
```

### 3. 예제 Agent

**Sample Agent를 공식 예제로 발전**시키겠습니다:

```
k-jarvis-sdk/
├── examples/
│   ├── sample-agent/           # 기본 예제 (현재 Sample Agent 기반)
│   ├── confluence-agent/       # Confluence 연동 예제
│   ├── github-agent/           # GitHub 연동 예제
│   └── multi-tool-agent/       # 멀티 도구 사용 예제
```

### 4. 테스트 케이스

```python
# tests/test_a2a_protocol.py
def test_send_message_method():
    """A2A SendMessage 메서드 테스트"""
    response = agent.handle_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "SendMessage",
        "params": {...}
    })
    assert response["result"]["message"] is not None

# tests/test_mcp_client.py
def test_mcp_stateless_call():
    """Stateless MCPHub 호출 테스트"""
    result = await client.call_tool("get_pull_requests", {"owner": "test"})
    assert result is not None
```

---

## 💡 개발 과정에서 얻은 핵심 인사이트 (SDK 반영 필수)

### 1. A2A 프로토콜 호환성 레이어

```python
# SDK 내부에서 자동 처리
SUPPORTED_METHODS = {
    "SendMessage": "handle_send_message",     # 표준
    "message/send": "handle_send_message",    # 레거시
    "tasks/send": "handle_send_message",      # 레거시
    "message": "handle_send_message",         # 레거시
}
```

### 2. Settings 표준 클래스

```python
from k_jarvis.config import BaseAgentSettings

class MyAgentSettings(BaseAgentSettings):
    """자동으로 필수 필드가 포함됨"""
    # mcp_hub_url ✅ 자동 포함
    # mcp_hub_token ✅ 자동 포함
    # agent_port ✅ 자동 포함
    # llm_provider ✅ 자동 포함
    
    # 커스텀 필드만 추가
    my_custom_field: str = Field(...)
```

### 3. 에러 메시지 표준화

```python
from k_jarvis.errors import MCPError, ErrorCode

# 사용자 친화적 에러 메시지 자동 생성
raise MCPError(
    code=ErrorCode.NO_SERVICE_TOKEN,
    message="해당 서비스에 대한 인증 토큰이 없습니다. MCPHub에서 토큰을 설정해주세요."
)
```

---

## 📋 논의 사항에 대한 의견

### 1. SDK 범위: **Thin Wrapper + Progressive Enhancement**

| 접근 방식 | 장점 | 단점 |
|----------|------|------|
| Full SDK | 개발 편의성 ↑ | 유지보수 ↑, 학습 곡선 ↑ |
| Thin Wrapper | 유연성 ↑, 표준 스펙 학습 | 반복 코드 ↑ |
| **Thin + Progressive** | 둘의 장점 결합 | 설계 복잡도 ↑ |

**제안**: **Core (필수) + Extensions (선택)** 구조

```python
# Core: 최소 필수 기능
from k_jarvis.core import Agent, A2AHandler

# Extensions: 선택적 확장
from k_jarvis.ext.langchain import LangChainAgent
from k_jarvis.ext.langgraph import LangGraphAgent
```

### 2. 언어 지원: **Python 우선**

- 현재 모든 Agent가 Python 기반
- LangChain, LangGraph 생태계가 Python 중심
- TypeScript는 MCP Server 개발용으로 K-ARC Team이 담당

### 3. 배포 방식: **사내 Private Registry 우선 → 향후 공개**

| 단계 | 배포 방식 | 대상 |
|------|----------|------|
| Phase 1 | 사내 Private PyPI | 내부 개발자 |
| Phase 2 | 문서 공개 + 신청 방식 | 파트너 개발자 |
| Phase 3 | PyPI 공개 | 외부 개발자 |

### 4. 거버넌스 수준: **필수 + 권장 분리**

```python
# 필수 (검증 통과 필요)
@required
- A2A 프로토콜 준수 (SendMessage, result.message)
- Agent Card 필수 필드
- MCPHub 연동 헤더 (Authorization, X-MCPHub-User-Id)

# 권장 (경고만)
@recommended
- 로깅 포맷
- 에러 응답 형식
- 헬스체크 엔드포인트
```

---

## 🔧 추가 제안 사항

### 1. Agent 템플릿 생성기

```bash
k-jarvis create agent my-agent --template=langgraph
```

템플릿 종류:
- `basic`: 최소 기능 Agent
- `langgraph`: LangGraph 기반 Agent (현재 우리 구조)
- `langchain`: LangChain 기반 Agent
- `mcp-only`: MCP 도구만 사용하는 Agent

### 2. 로컬 개발 환경 자동 구성

```bash
k-jarvis dev setup
# - Docker 네트워크 생성
# - MCPHub 로컬 연결 설정
# - 환경변수 템플릿 생성
```

### 3. Agent 배포 가이드 자동화

```bash
k-jarvis deploy --target=docker
# - Dockerfile 자동 생성
# - docker-compose.yml 생성
# - 환경변수 체크
```

---

## 📅 일정에 대한 의견

| 단계 | Orchestrator 제안 | Agent Team 의견 |
|------|------------------|-----------------|
| Phase 1 | 1주 (설계) | ✅ 동의 |
| Phase 2 | 2주 (개발) | 3주 권장 (MCPHub 연동 모듈 복잡) |
| Phase 3 | 1주 (문서) | ✅ 동의 |
| Phase 4 | 1주 (베타) | 2주 권장 (실제 Agent 마이그레이션 테스트 필요) |

**총 기간**: 5주 → **7주 권장**

---

## ✅ Agent Team 참여 의사

### 우리가 담당하겠습니다:

| 모듈 | 담당자 | 산출물 |
|------|--------|--------|
| `k_jarvis.a2a` | Agent Team | A2A 응답 빌더, 메서드 핸들러 |
| `k_jarvis.mcp` | Agent Team | MCPHub 클라이언트, User-Context 처리 |
| `k_jarvis.config` | Agent Team | 표준 Settings 클래스 |
| 예제 Agent | Agent Team | 4종 예제 (Sample, Confluence, Jira, GitHub) |
| 테스트 케이스 | Agent Team | 단위/통합 테스트 |
| 마이그레이션 가이드 | Agent Team | 기존 Agent → SDK 전환 문서 |

### 예상 투입 공수

| 작업 | 예상 공수 |
|------|----------|
| 코어 모듈 개발 | 2주 |
| 예제 Agent 정리 | 1주 |
| 테스트 케이스 | 1주 |
| 문서화 | 1주 |
| **총계** | **5주** |

---

## 📞 추가 논의 제안

### 1. 킥오프 미팅

- **주제**: SDK 인터페이스 상세 설계
- **참석**: Orchestrator, Agent, MCPHub 팀
- **제안 일정**: 이번 주 내

### 2. 기술 스파이크

- MCPHub Stateless 아키텍처와 SDK 호환성 검증
- LangGraph/LangChain 통합 방안 검토

### 3. 공동 설계 문서

- GitHub/Confluence에 SDK 설계 문서 공동 작성
- 각 팀 Review 후 확정

---

## 🎯 마무리

> **"우리가 겪은 고통을, 다른 개발자들은 겪지 않게 하자."**

K-Jarvis 생태계 SDK 개발에 **Agent Team은 적극 참여하겠습니다**.

특히 MCPHub 연동과 A2A 프로토콜 부분에서 우리가 축적한 **실전 경험**이 SDK의 품질을 높이는 데 기여할 것입니다.

함께 멋진 생태계를 만들어 갑시다! 🚀

---

**Agent Team**  
Slack: #agent-dev  
문서: [K-Jarvis Agent 문서 허브](https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/568925309)

