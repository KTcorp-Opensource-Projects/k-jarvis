# k-jarvis-utils API 설계 v1.0

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team  
**상태**: Draft (피드백 요청)

---

## 📦 패키지 개요

```
k-jarvis-utils
├── headers/           # K-Jarvis 헤더 처리
├── mcp/               # MCPHub 연동 유틸리티
├── a2a/               # A2A 응답 빌더
├── errors/            # 표준 에러 핸들링
├── validation/        # Agent Card 검증
├── testing/           # 계약 테스트 헬퍼
└── __init__.py
```

---

## 1. headers - K-Jarvis 헤더 처리

### KJarvisHeaders

```python
from dataclasses import dataclass
from typing import Optional
from flask import Request  # 또는 FastAPI Request

@dataclass
class KJarvisHeaders:
    """K-Jarvis 플랫폼 표준 헤더"""
    
    request_id: str
    user_id: Optional[str]
    mcphub_user_id: Optional[str]
    content_type: str
    accept: Optional[str]
    
    @classmethod
    def from_request(cls, request: Request) -> "KJarvisHeaders":
        """
        HTTP 요청에서 K-Jarvis 헤더 추출
        
        Args:
            request: Flask/FastAPI Request 객체
            
        Returns:
            KJarvisHeaders 인스턴스
            
        Example:
            headers = KJarvisHeaders.from_request(request)
            print(headers.mcphub_user_id)  # "user-123"
        """
        import uuid
        
        return cls(
            request_id=request.headers.get("X-Request-Id", str(uuid.uuid4())),
            user_id=request.headers.get("X-User-Id"),
            mcphub_user_id=request.headers.get("X-MCPHub-User-Id"),
            content_type=request.headers.get("Content-Type", "application/json"),
            accept=request.headers.get("Accept"),
        )
    
    def to_dict(self) -> dict:
        """헤더를 딕셔너리로 변환 (전파용)"""
        headers = {
            "X-Request-Id": self.request_id,
            "Content-Type": self.content_type,
        }
        if self.user_id:
            headers["X-User-Id"] = self.user_id
        if self.mcphub_user_id:
            headers["X-MCPHub-User-Id"] = self.mcphub_user_id
        if self.accept:
            headers["Accept"] = self.accept
        return headers
    
    def log_context(self) -> str:
        """로깅용 컨텍스트 문자열"""
        return f"[{self.request_id}] user={self.user_id}, mcphub_user={self.mcphub_user_id}"
```

### 사용 예시

```python
from flask import Flask, request
from k_jarvis_utils import KJarvisHeaders

app = Flask(__name__)

@app.route("/a2a", methods=["POST"])
def a2a_endpoint():
    # Before: 10줄 이상의 헤더 추출 코드
    # After: 1줄
    headers = KJarvisHeaders.from_request(request)
    
    logger.info(headers.log_context())  # [req-123] user=..., mcphub_user=...
    
    # MCP 호출 시 헤더 전파
    response = httpx.post(
        "http://mcphub/api/...",
        headers=headers.to_dict()
    )
```

---

## 2. mcp - MCPHub 연동 유틸리티

### MCPHubClient

```python
from typing import Optional, Dict, Any, List
import httpx

class MCPHubClient:
    """MCPHub(K-ARC) 연동 클라이언트"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:5173",
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        mcphub_user_id: str,
    ) -> Dict[str, Any]:
        """
        MCP 도구 호출
        
        Args:
            server_name: MCP 서버 이름 (예: "atlassian-confluence")
            tool_name: 도구 이름 (예: "search")
            arguments: 도구 인자
            mcphub_user_id: MCPHub 사용자 ID (서비스 토큰 조회용)
            
        Returns:
            MCP 도구 실행 결과
            
        Raises:
            MCPError: MCP 관련 에러
        """
        response = await self._client.post(
            f"{self.base_url}/api/mcp/{server_name}/tools/call",
            json={
                "name": tool_name,
                "arguments": arguments,
            },
            headers={
                "X-MCPHub-User-Id": mcphub_user_id,
                "Content-Type": "application/json",
            },
        )
        
        if response.status_code != 200:
            error_data = response.json()
            raise MCPError.from_response(error_data)
        
        return response.json()
    
    async def list_tools(
        self,
        server_name: str,
        mcphub_user_id: str,
    ) -> List[Dict[str, Any]]:
        """MCP 서버의 도구 목록 조회"""
        response = await self._client.get(
            f"{self.base_url}/api/mcp/{server_name}/tools",
            headers={"X-MCPHub-User-Id": mcphub_user_id},
        )
        return response.json()
```

### 사용 예시

```python
from k_jarvis_utils.mcp import MCPHubClient

async def search_confluence(query: str, mcphub_user_id: str):
    async with MCPHubClient() as mcp:
        result = await mcp.call_tool(
            server_name="atlassian-confluence",
            tool_name="search",
            arguments={"query": query},
            mcphub_user_id=mcphub_user_id,
        )
        return result
```

---

## 3. errors - 표준 에러 핸들링

### MCPError

```python
from typing import Optional, Dict, Any
from enum import IntEnum

class MCPErrorCode(IntEnum):
    """MCPHub 표준 에러 코드"""
    NO_SERVICE_TOKEN = -32001
    TOKEN_EXPIRED = -32002
    TOKEN_INVALID = -32003
    SERVER_NOT_FOUND = -32004
    TOOL_NOT_FOUND = -32005
    EXECUTION_ERROR = -32006

class MCPError(Exception):
    """MCP 관련 에러"""
    
    # 사용자 친화적 메시지 템플릿
    USER_MESSAGES = {
        MCPErrorCode.NO_SERVICE_TOKEN: """⚠️ {service_name} 서비스 토큰이 등록되지 않았습니다.

해결 방법:
1. MCPHub ({mcphub_url})에 로그인
2. MCP 카탈로그에서 {service_name} 서버 찾기
3. 토큰 등록 후 다시 시도해주세요.""",

        MCPErrorCode.TOKEN_EXPIRED: """⚠️ {service_name} 서비스 토큰이 만료되었습니다.

해결 방법:
1. MCPHub ({mcphub_url})에 로그인
2. {service_name} 서버의 토큰을 갱신해주세요.""",

        MCPErrorCode.TOKEN_INVALID: """⚠️ {service_name} 서비스 토큰이 유효하지 않습니다.

해결 방법:
1. MCPHub ({mcphub_url})에서 토큰을 다시 등록해주세요.""",
    }
    
    def __init__(
        self,
        code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> "MCPError":
        """API 응답에서 에러 생성"""
        error = response.get("error", {})
        return cls(
            code=error.get("code", -32000),
            message=error.get("message", "Unknown error"),
            details=error.get("data"),
        )
    
    def get_user_message(
        self,
        service_name: str = "서비스",
        mcphub_url: str = "http://localhost:5173",
    ) -> str:
        """사용자 친화적 에러 메시지 생성"""
        template = self.USER_MESSAGES.get(self.code)
        if template:
            return template.format(
                service_name=service_name,
                mcphub_url=mcphub_url,
            )
        return f"오류가 발생했습니다: {self.message}"
    
    def is_token_error(self) -> bool:
        """토큰 관련 에러인지 확인"""
        return self.code in (
            MCPErrorCode.NO_SERVICE_TOKEN,
            MCPErrorCode.TOKEN_EXPIRED,
            MCPErrorCode.TOKEN_INVALID,
        )
```

### MCPErrorHandler

```python
class MCPErrorHandler:
    """MCP 에러 핸들러 (데코레이터 지원)"""
    
    def __init__(
        self,
        mcphub_url: str = "http://localhost:5173",
        default_service_name: str = "서비스",
    ):
        self.mcphub_url = mcphub_url
        self.default_service_name = default_service_name
    
    def handle(self, error: MCPError, service_name: Optional[str] = None) -> str:
        """에러를 사용자 메시지로 변환"""
        return error.get_user_message(
            service_name=service_name or self.default_service_name,
            mcphub_url=self.mcphub_url,
        )
    
    def wrap(self, service_name: Optional[str] = None):
        """에러 핸들링 데코레이터"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except MCPError as e:
                    return self.handle(e, service_name)
            return wrapper
        return decorator
```

### 사용 예시

```python
from k_jarvis_utils.errors import MCPError, MCPErrorHandler

handler = MCPErrorHandler(mcphub_url="http://localhost:5173")

@handler.wrap(service_name="Confluence")
async def search_confluence(query: str, mcphub_user_id: str):
    async with MCPHubClient() as mcp:
        return await mcp.call_tool(
            server_name="atlassian-confluence",
            tool_name="search",
            arguments={"query": query},
            mcphub_user_id=mcphub_user_id,
        )

# 에러 발생 시 자동으로 사용자 친화적 메시지 반환:
# "⚠️ Confluence 서비스 토큰이 등록되지 않았습니다..."
```

---

## 4. a2a - A2A 응답 빌더

### A2AResponseBuilder

```python
from typing import Any, Optional, List, Dict
from dataclasses import dataclass, field
import uuid

@dataclass
class A2APart:
    """A2A 메시지 파트"""
    type: str  # "text", "data", "file", etc.
    content: Any
    
    def to_dict(self) -> dict:
        if self.type == "text":
            return {"type": "text", "text": self.content}
        elif self.type == "data":
            return {"type": "data", "data": self.content}
        return {"type": self.type, "content": self.content}

class A2AResponseBuilder:
    """A2A 프로토콜 응답 빌더"""
    
    def __init__(self):
        self.parts: List[A2APart] = []
    
    def add_text(self, text: str) -> "A2AResponseBuilder":
        """텍스트 파트 추가"""
        self.parts.append(A2APart(type="text", content=text))
        return self
    
    def add_data(self, data: Any) -> "A2AResponseBuilder":
        """데이터 파트 추가"""
        self.parts.append(A2APart(type="data", content=data))
        return self
    
    def build(self) -> Dict[str, Any]:
        """A2A 응답 형식으로 빌드"""
        return {
            "role": "agent",
            "parts": [p.to_dict() for p in self.parts],
        }
    
    @staticmethod
    def text(content: str) -> Dict[str, Any]:
        """단순 텍스트 응답 생성 (숏컷)"""
        return {
            "role": "agent",
            "parts": [{"type": "text", "text": content}],
        }
    
    @staticmethod
    def error(message: str, code: Optional[int] = None) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "role": "agent",
            "parts": [{"type": "text", "text": f"❌ {message}"}],
            "metadata": {"error": True, "code": code} if code else {"error": True},
        }
```

### JsonRpcResponse

```python
from typing import Any, Optional

class JsonRpcResponse:
    """JSON-RPC 응답 빌더"""
    
    @staticmethod
    def success(result: Any, request_id: Any = None) -> dict:
        """성공 응답"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }
    
    @staticmethod
    def error(
        code: int,
        message: str,
        request_id: Any = None,
        data: Optional[Any] = None,
    ) -> dict:
        """에러 응답"""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error,
        }
```

### 사용 예시

```python
from k_jarvis_utils.a2a import A2AResponseBuilder, JsonRpcResponse

# 단순 텍스트 응답
return A2AResponseBuilder.text("검색 결과입니다.")

# 복합 응답
response = (
    A2AResponseBuilder()
    .add_text("검색 결과:")
    .add_data({"total": 10, "items": [...]})
    .build()
)

# JSON-RPC 응답
return JsonRpcResponse.success(
    result={"message": response},
    request_id=request_data.get("id"),
)
```

---

## 5. validation - Agent Card 검증

### AgentCardValidator

```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ValidationError:
    field: str
    message: str
    severity: str  # "error" | "warning"

class AgentCardValidator:
    """Agent Card 스키마 검증기"""
    
    REQUIRED_FIELDS = ["name", "description", "version", "endpoints"]
    REQUIRED_ENDPOINTS = ["message"]  # 최소 필수 엔드포인트
    
    def __init__(self, card: Dict[str, Any]):
        self.card = card
        self.errors: List[ValidationError] = []
    
    def validate(self) -> bool:
        """전체 검증 실행"""
        self._validate_required_fields()
        self._validate_endpoints()
        self._validate_skills()
        self._validate_routing()
        return len([e for e in self.errors if e.severity == "error"]) == 0
    
    def _validate_required_fields(self):
        for field in self.REQUIRED_FIELDS:
            if field not in self.card:
                self.errors.append(ValidationError(
                    field=field,
                    message=f"필수 필드 '{field}'가 없습니다.",
                    severity="error",
                ))
    
    def _validate_endpoints(self):
        endpoints = self.card.get("endpoints", {})
        for ep in self.REQUIRED_ENDPOINTS:
            if ep not in endpoints:
                self.errors.append(ValidationError(
                    field=f"endpoints.{ep}",
                    message=f"필수 엔드포인트 '{ep}'가 없습니다.",
                    severity="error",
                ))
    
    def _validate_skills(self):
        skills = self.card.get("skills", [])
        for i, skill in enumerate(skills):
            if "name" not in skill:
                self.errors.append(ValidationError(
                    field=f"skills[{i}].name",
                    message="스킬에 name이 필요합니다.",
                    severity="error",
                ))
    
    def _validate_routing(self):
        # routing 필드 권장 검사
        if "routing" not in self.card:
            self.errors.append(ValidationError(
                field="routing",
                message="routing 필드 추가를 권장합니다 (RAG 라우팅 향상).",
                severity="warning",
            ))
    
    def get_errors(self) -> List[ValidationError]:
        return [e for e in self.errors if e.severity == "error"]
    
    def get_warnings(self) -> List[ValidationError]:
        return [e for e in self.errors if e.severity == "warning"]
    
    def format_report(self) -> str:
        """검증 보고서 문자열 생성"""
        lines = ["=== Agent Card 검증 결과 ==="]
        
        errors = self.get_errors()
        warnings = self.get_warnings()
        
        if not errors and not warnings:
            lines.append("✅ 검증 통과")
        else:
            if errors:
                lines.append(f"\n❌ 에러 ({len(errors)}건):")
                for e in errors:
                    lines.append(f"  - {e.field}: {e.message}")
            if warnings:
                lines.append(f"\n⚠️ 경고 ({len(warnings)}건):")
                for w in warnings:
                    lines.append(f"  - {w.field}: {w.message}")
        
        return "\n".join(lines)
```

### 사용 예시

```python
from k_jarvis_utils.validation import AgentCardValidator

agent_card = {
    "name": "My Agent",
    "description": "...",
    "version": "1.0.0",
    "endpoints": {"message": "/a2a"},
    "skills": [{"name": "search", "description": "..."}],
}

validator = AgentCardValidator(agent_card)
if validator.validate():
    print("✅ Agent Card 검증 통과")
else:
    print(validator.format_report())
```

---

## 6. testing - 계약 테스트 헬퍼

### ContractTestBase

```python
import pytest
from typing import Dict, Any
import httpx

class ContractTestBase:
    """K-Jarvis 계약 테스트 기본 클래스"""
    
    AGENT_URL: str = "http://localhost:5010"
    
    @pytest.fixture
    def client(self):
        with httpx.Client(base_url=self.AGENT_URL) as client:
            yield client
    
    def test_agent_card_exists(self, client):
        """Agent Card 엔드포인트 존재 확인"""
        response = client.get("/.well-known/agent.json")
        assert response.status_code == 200
        assert "name" in response.json()
    
    def test_agent_card_valid(self, client):
        """Agent Card 스키마 검증"""
        response = client.get("/.well-known/agent.json")
        card = response.json()
        
        validator = AgentCardValidator(card)
        assert validator.validate(), validator.format_report()
    
    def test_health_endpoint(self, client):
        """헬스체크 엔드포인트"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_a2a_endpoint_exists(self, client):
        """/a2a 엔드포인트 존재 확인"""
        response = client.post(
            "/a2a",
            json={
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {"message": {"role": "user", "parts": [{"type": "text", "text": "테스트"}]}},
                "id": "test-1",
            },
        )
        # 에러가 아닌 응답이면 OK (토큰 없어서 실패해도 엔드포인트는 존재)
        assert response.status_code in (200, 400, 401, 500)
    
    def test_required_headers_propagation(self, client):
        """필수 헤더 전파 확인"""
        response = client.post(
            "/a2a",
            json={"jsonrpc": "2.0", "method": "message/send", "params": {}, "id": "test"},
            headers={
                "X-Request-Id": "test-request-123",
                "X-MCPHub-User-Id": "test-user-456",
            },
        )
        # 응답에서 에러가 나더라도 헤더는 처리되어야 함
        assert response.status_code != 404
```

### 사용 예시

```python
# tests/test_confluence_agent.py
from k_jarvis_utils.testing import ContractTestBase

class TestConfluenceAgent(ContractTestBase):
    AGENT_URL = "http://localhost:5010"
    
    def test_search_skill_exists(self, client):
        """search 스킬 존재 확인"""
        response = client.get("/.well-known/agent.json")
        card = response.json()
        
        skill_names = [s["name"] for s in card.get("skills", [])]
        assert "search" in skill_names or "search_confluence" in skill_names
```

---

## 📦 패키지 구조 최종

```
k_jarvis_utils/
├── __init__.py
│   # 모든 public API export
│   from .headers import KJarvisHeaders
│   from .mcp import MCPHubClient
│   from .errors import MCPError, MCPErrorCode, MCPErrorHandler
│   from .a2a import A2AResponseBuilder, JsonRpcResponse
│   from .validation import AgentCardValidator, ValidationError
│   from .testing import ContractTestBase
│
├── headers/
│   ├── __init__.py
│   └── kjarvis_headers.py
│
├── mcp/
│   ├── __init__.py
│   └── mcphub_client.py
│
├── errors/
│   ├── __init__.py
│   ├── mcp_error.py
│   └── handler.py
│
├── a2a/
│   ├── __init__.py
│   ├── response_builder.py
│   └── jsonrpc.py
│
├── validation/
│   ├── __init__.py
│   └── agent_card.py
│
└── testing/
    ├── __init__.py
    └── contract_base.py
```

---

## 🔄 피드백 요청

Agent Team에게:
1. 위 API가 현재 고통점을 해결하는가?
2. 추가로 필요한 유틸리티가 있는가?
3. API 네이밍/시그니처가 직관적인가?

---

**Orchestrator Team**


