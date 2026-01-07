# Phase 3 (개발) 시작 - k-jarvis-utils 프로토타입 완성

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team  
**수신팀**: Agent Team, K-ARC Team

---

## 🎉 Phase 3 시작!

Agent Team의 피드백을 반영하여 `k-jarvis-utils` 프로토타입 개발을 완료했습니다.

---

## 📦 k-jarvis-utils v0.1.0 구조

```
packages/k-jarvis-utils/
├── k_jarvis_utils/
│   ├── __init__.py
│   ├── headers/
│   │   ├── __init__.py
│   │   └── kjarvis_headers.py      # ✅ KJarvisHeaders
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── mcphub_client.py        # ✅ MCPHubClient (피드백 반영)
│   ├── errors/
│   │   ├── __init__.py
│   │   └── mcp_error.py            # ✅ MCPError, MCPErrorHandler
│   ├── a2a/
│   │   ├── __init__.py
│   │   ├── response_builder.py     # ✅ A2AResponseBuilder
│   │   └── jsonrpc.py              # ✅ JsonRpcResponse
│   ├── validation/
│   │   ├── __init__.py
│   │   └── agent_card.py           # ✅ AgentCardValidator
│   └── testing/
│       ├── __init__.py
│       └── contract_base.py        # ✅ ContractTestBase
├── pyproject.toml
└── README.md
```

---

## ✅ Agent Team 피드백 반영 내역

### 1. MCPHubClient - MCP SDK 지원 ✅

```python
class MCPHubClient:
    def __init__(
        self,
        base_url: str = None,
        api_key: Optional[str] = None,       # ⭐ 추가: Agent 전용 Key
        timeout: float = 30.0,
        use_mcp_sdk: bool = False,           # ⭐ 추가: MCP SDK 사용 여부
    ):
```

- `use_mcp_sdk=True` 시 MCP SDK의 `streamablehttp_client` 사용
- `use_mcp_sdk=False` (기본) 시 REST API 직접 호출

### 2. MCPHubClient - Authorization 헤더 ✅

```python
def _get_headers(self, mcphub_user_id: str) -> Dict[str, str]:
    headers = {
        "X-MCPHub-User-Id": mcphub_user_id,
        "Content-Type": "application/json",
    }
    if self.api_key:
        headers["Authorization"] = f"Bearer {self.api_key}"  # ⭐ 추가
    return headers
```

### 3. MCPErrorCode 확장 ✅

```python
class MCPErrorCode(IntEnum):
    NO_SERVICE_TOKEN = -32001
    TOKEN_EXPIRED = -32002
    TOKEN_INVALID = -32003
    SERVER_NOT_FOUND = -32004
    TOOL_NOT_FOUND = -32005
    EXECUTION_ERROR = -32006
    NO_TOOLS_AVAILABLE = -32007  # ⭐ 추가
    SESSION_EXPIRED = -32008     # ⭐ 추가
```

### 4. AgentCardValidator - requirements 검증 ✅

```python
def _validate_requirements(self):
    """요구사항 필드 검증 (Agent Team 피드백)"""
    requirements = self.card.get("requirements", {})
    
    if "mcpHubToken" not in requirements:
        # warning 추가
        
    if requirements.get("mcpHubToken") and not requirements.get("mcpServers"):
        # error 추가
```

---

## 🎯 주요 API 사용 예시

### Before vs After

```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Before: 10줄
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def extract_headers(request):
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-Id")
    mcphub_user_id = request.headers.get("X-MCPHub-User-Id")
    logger.info(f"[{request_id}] user={user_id}, mcphub_user={mcphub_user_id}")
    return {"request_id": request_id, "user_id": user_id, "mcphub_user_id": mcphub_user_id}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# After: 2줄
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from k_jarvis_utils import KJarvisHeaders

headers = KJarvisHeaders.from_request(request)
logger.info(headers.log_context())
```

```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Before: 50줄 에러 핸들링
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MCP_ERROR_CODES = { -32001: "...", -32002: "...", ... }
def handle_mcp_error(error): ...

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# After: 3줄
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from k_jarvis_utils import MCPErrorHandler

handler = MCPErrorHandler(mcphub_url="http://localhost:5173")

@handler.wrap(service_name="Confluence")
async def my_skill(...): ...
```

---

## 📋 Phase 3 체크리스트

### Orchestrator Team
- [x] k-jarvis-utils 프로토타입 v0.1.0 완성 ✅
- [x] Agent Team 피드백 반영 ✅
- [ ] 단위 테스트 작성
- [ ] pip 로컬 설치 테스트
- [ ] 문서화 보완

### Agent Team
- [ ] k-jarvis-utils 로컬 테스트
- [ ] Confluence Agent에 적용 테스트
- [ ] 추가 피드백 (있으면)

### K-ARC Team
- [ ] k-arc-utils 프로토타입 개발 시작
- [ ] k-jarvis-utils와 에러 코드 일관성 확인

---

## 🔧 로컬 설치 방법 (테스트용)

```bash
# Agent-orchestrator 저장소에서
cd packages/k-jarvis-utils
pip install -e .

# 또는 전체 의존성 포함
pip install -e ".[all]"
```

### Agent에서 사용

```python
# 기존 requirements.txt에 추가 불필요 (로컬 editable 설치)
from k_jarvis_utils import (
    KJarvisHeaders,
    MCPHubClient,
    MCPError,
    MCPErrorHandler,
    A2AResponseBuilder,
    JsonRpcResponse,
    AgentCardValidator,
)
```

---

## 💡 다음 단계

1. **Agent Team**: `k-jarvis-utils`를 Confluence Agent에 적용 테스트
2. **K-ARC Team**: `k-arc-utils` 프로토타입 개발
3. **Orchestrator Team**: 테스트 코드 작성 및 문서화

**궁금한 점이 있으면 언제든 문서로 공유해주세요!** 🚀

---

**Orchestrator Team**

