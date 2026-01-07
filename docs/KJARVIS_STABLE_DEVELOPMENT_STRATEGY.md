# K-Jarvis 안정적 개발 전략
## LLM 기반 다중 팀 협업에서 변경 영향 최소화 방안

**작성일**: 2024-12-17  
**버전**: 1.0  
**대상**: Orchestrator Team, Agent Team, MCPHub Team

---

## 🎯 문제 정의

### 현재 상황
```
[Orchestrator Team] ──수정──> Core/Middleware 변경
        │
        ├──영향──> [Agent Team] 코드 수정 필요
        └──영향──> [MCPHub Team] 코드 수정 필요
```

### 문제점
1. 코어 로직 수정 시 다른 팀 코드도 연쇄적으로 수정 필요
2. 각 팀이 LLM을 사용하므로 변경 범위 예측 어려움
3. 테스트 반복으로 개발 속도 저하
4. 버전 간 호환성 관리 어려움

---

## 🛡️ 전략 1: API Contract (계약) 기반 개발

### 핵심 원칙
> **"인터페이스는 계약이다. 계약을 변경하려면 모든 당사자의 동의가 필요하다."**

### 구현 방법

#### 1.1 계약 문서 작성 (각 팀 필수)

```yaml
# contracts/orchestrator-to-agent.yaml
contract_name: "Orchestrator → Agent 통신"
version: "1.0.0"
status: "LOCKED"  # LOCKED = 변경 금지

endpoints:
  - path: "/a2a"
    method: "POST"
    headers:
      - name: "X-MCPHub-User-Id"
        type: "string"
        required: true
        description: "K-Auth User ID for MCPHub token lookup"
      - name: "X-Request-Id"
        type: "string"
        required: false
    request_body:
      type: "A2ARequest"
      schema: "$ref: #/schemas/A2ARequest"
    response:
      type: "A2AResponse"
      schema: "$ref: #/schemas/A2AResponse"

schemas:
  A2ARequest:
    type: object
    properties:
      jsonrpc: { type: string, const: "2.0" }
      method: { type: string }
      params: { type: object }
      id: { type: string }
    required: [jsonrpc, method, id]

breaking_changes:
  - "헤더 추가/삭제"
  - "필수 필드 변경"
  - "응답 구조 변경"
  - "엔드포인트 경로 변경"
```

#### 1.2 계약 변경 프로세스

```
1. 변경 제안 문서 작성 (TO_ALL_TEAMS_CONTRACT_CHANGE_*.md)
        ↓
2. 모든 팀 검토 및 동의 (48시간 내)
        ↓
3. 영향도 분석 문서 작성
        ↓
4. 동시 수정 일정 합의
        ↓
5. 계약 버전 업데이트 (v1.0.0 → v1.1.0)
```

---

## 🔒 전략 2: 변경 금지 영역 (Frozen Zone) 지정

### LLM 개발 시 필수 규칙

각 팀의 `.cursorrules` 또는 프롬프트에 다음 내용 포함:

```markdown
## 🚫 변경 금지 영역 (FROZEN ZONE)

다음 영역은 팀 간 합의 없이 절대 수정하지 마세요:

### Orchestrator Team
- `backend/app/orchestrator.py` 의 `_call_agent()` 메서드
- `backend/app/api.py` 의 A2A 관련 엔드포인트
- X-MCPHub-User-Id 헤더 처리 로직

### Agent Team  
- `/a2a` 엔드포인트 응답 형식
- MCPHub 연동 로직 (X-MCPHub-User-Id 처리)
- A2A 프로토콜 구현부

### MCPHub Team
- `/mcp` 엔드포인트
- 서비스 토큰 조회 API
- X-MCPHub-User-Id 기반 토큰 조회 로직

### 변경이 필요한 경우
1. 먼저 docs/ 폴더에 변경 제안 문서 작성
2. 다른 팀의 동의를 얻은 후 수정
3. 절대 단독으로 수정하지 않음
```

---

## 📦 전략 3: 인터페이스 분리 아키텍처

### 현재 구조의 문제

```
Orchestrator ──직접호출──> Agent
     │
     └── 내부 로직 변경 시 Agent도 영향
```

### 개선된 구조

```
Orchestrator ──[Contract Layer]──> Agent
                    │
                    ├── 헤더 변환
                    ├── 요청 검증
                    └── 버전 호환성 처리
```

### 구현 예시

```python
# orchestrator/app/contracts/agent_contract.py
"""
Agent 통신 계약 레이어
이 파일은 FROZEN ZONE입니다. 변경 시 전체 팀 동의 필요.
"""

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Contract Version
CONTRACT_VERSION = "1.0.0"

@dataclass
class AgentRequest:
    """Agent 요청 계약 - 변경 금지"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: dict = None
    id: str = ""

@dataclass  
class AgentHeaders:
    """Agent 헤더 계약 - 변경 금지"""
    x_mcphub_user_id: Optional[str] = None
    x_request_id: Optional[str] = None
    content_type: str = "application/json"
    
    def to_dict(self) -> dict:
        headers = {"Content-Type": self.content_type}
        if self.x_mcphub_user_id:
            headers["X-MCPHub-User-Id"] = self.x_mcphub_user_id
        if self.x_request_id:
            headers["X-Request-Id"] = self.x_request_id
        return headers

def validate_request(request: AgentRequest) -> bool:
    """요청 검증 - 계약 준수 확인"""
    if request.jsonrpc != "2.0":
        logger.error(f"Contract violation: jsonrpc must be '2.0'")
        return False
    if not request.method:
        logger.error(f"Contract violation: method is required")
        return False
    return True
```

---

## 🧪 전략 4: 자동화된 계약 테스트 (Contract Testing)

### 구현 방법

각 팀이 `tests/contract/` 폴더에 계약 테스트 작성:

```python
# orchestrator/tests/contract/test_agent_contract.py
"""
Agent 계약 테스트
이 테스트가 실패하면 계약 위반입니다.
"""
import pytest
from app.contracts.agent_contract import AgentRequest, AgentHeaders, CONTRACT_VERSION

class TestAgentContract:
    """Agent 통신 계약 테스트"""
    
    def test_contract_version(self):
        """계약 버전 확인"""
        assert CONTRACT_VERSION == "1.0.0"
    
    def test_request_format(self):
        """요청 형식 계약 준수"""
        request = AgentRequest(
            method="message/send",
            params={"message": "test"},
            id="123"
        )
        assert request.jsonrpc == "2.0"
        assert request.method == "message/send"
    
    def test_required_headers(self):
        """필수 헤더 계약 준수"""
        headers = AgentHeaders(
            x_mcphub_user_id="user-123"
        )
        header_dict = headers.to_dict()
        
        # X-MCPHub-User-Id는 필수
        assert "X-MCPHub-User-Id" in header_dict
        assert header_dict["Content-Type"] == "application/json"
    
    def test_header_name_exact_match(self):
        """헤더 이름 정확히 일치 확인"""
        headers = AgentHeaders(x_mcphub_user_id="test")
        header_dict = headers.to_dict()
        
        # 대소문자 정확히 일치해야 함
        assert "X-MCPHub-User-Id" in header_dict
        assert "x-mcphub-user-id" not in header_dict  # 소문자 안됨
```

### CI/CD 연동

```yaml
# .github/workflows/contract-test.yml
name: Contract Tests

on:
  push:
    paths:
      - 'app/contracts/**'
      - 'app/orchestrator.py'
      - 'app/api.py'

jobs:
  contract-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Contract Tests
        run: |
          pytest tests/contract/ -v --tb=short
          
      - name: Notify on Failure
        if: failure()
        run: |
          echo "⚠️ CONTRACT VIOLATION DETECTED!"
          echo "계약 테스트 실패. 다른 팀에 영향을 줄 수 있는 변경입니다."
```

---

## 📋 전략 5: 변경 영향 체크리스트

### LLM에게 제공할 변경 전 체크리스트

```markdown
## 🔍 코드 변경 전 체크리스트

변경하려는 코드가 다음에 해당하는지 확인하세요:

### 1. 다른 팀 영향 여부
- [ ] API 엔드포인트 변경? → 🔴 전체 팀 동의 필요
- [ ] 헤더 추가/삭제/변경? → 🔴 전체 팀 동의 필요
- [ ] 요청/응답 구조 변경? → 🔴 전체 팀 동의 필요
- [ ] 환경변수 추가/변경? → 🟡 문서 업데이트 필요

### 2. FROZEN ZONE 여부
- [ ] orchestrator.py의 _call_agent() → 🔴 변경 금지
- [ ] api.py의 /a2a 엔드포인트 → 🔴 변경 금지
- [ ] X-MCPHub-User-Id 처리 로직 → 🔴 변경 금지

### 3. 허용된 변경
- [ ] 내부 로직만 변경 (입출력 동일) → ✅ 허용
- [ ] 새로운 optional 파라미터 추가 → 🟡 문서화 후 허용
- [ ] 버그 수정 (동작 변경 없음) → ✅ 허용
- [ ] 성능 최적화 (동작 변경 없음) → ✅ 허용

### 4. 변경 시 필수 작업
- [ ] tests/contract/ 테스트 실행 및 통과
- [ ] 영향받는 팀에 사전 공지
- [ ] docs/ 에 변경 내용 문서화
```

---

## 🔄 전략 6: 버전 관리 전략

### Semantic Versioning 적용

```
v1.0.0
 │ │ │
 │ │ └── PATCH: 버그 수정 (하위 호환)
 │ └──── MINOR: 기능 추가 (하위 호환)
 └────── MAJOR: Breaking Change (하위 호환 X)
```

### API 버전 관리

```python
# 버전별 엔드포인트 분리
@app.post("/v1/a2a")  # 기존 버전 유지
async def a2a_v1(request: A2ARequestV1):
    ...

@app.post("/v2/a2a")  # 새 버전은 별도 엔드포인트
async def a2a_v2(request: A2ARequestV2):
    ...
```

---

## 📊 전략 요약

| 전략 | 목적 | 효과 |
|------|------|------|
| **1. API Contract** | 인터페이스 고정 | 연쇄 수정 방지 |
| **2. Frozen Zone** | 변경 금지 영역 지정 | LLM 무단 수정 방지 |
| **3. 인터페이스 분리** | 계약 레이어 추가 | 내부 변경 격리 |
| **4. Contract Testing** | 자동화된 계약 검증 | 위반 조기 발견 |
| **5. 변경 체크리스트** | 변경 전 검토 | 영향도 사전 파악 |
| **6. 버전 관리** | 하위 호환성 유지 | 점진적 마이그레이션 |

---

## 🚀 즉시 적용 권장 사항

### Phase 1: 즉시 (오늘)
1. 각 팀 `.cursorrules`에 FROZEN ZONE 규칙 추가
2. `contracts/` 폴더 생성 및 현재 인터페이스 문서화

### Phase 2: 이번 주 내
3. Contract Testing 파일 생성
4. 변경 체크리스트 LLM 프롬프트에 포함

### Phase 3: 다음 주
5. CI/CD에 Contract Test 연동
6. API 버전 관리 체계 도입

---

## 💡 핵심 메시지

> **"코어를 수정하기 전에 문서를 먼저 작성하라"**
> 
> LLM 개발 환경에서 가장 중요한 것은 **변경 의도를 먼저 공유**하는 것입니다.
> 코드 수정보다 문서 작성이 먼저입니다.

---

**K-Jarvis Project - 안정적인 v2.0을 향해** 🚀


