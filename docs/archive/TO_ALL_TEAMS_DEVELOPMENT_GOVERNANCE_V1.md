# 🎯 K-Jarvis 개발 거버넌스 v1.0
## LLM 기반 다중 팀 협업의 최적 전략

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team  
**수신팀**: ALL (Agent Team, MCPHub Team)  
**상태**: 🔴 **필수 적용**

---

## 📢 배경

K-Jarvis 프로젝트는 다음 목표를 위해 시작되었습니다:
- AI Agent 개발 부서들과 MCP Server 개발 부서의 증가에 따른 **A2A/MCP 스택 거버넌스**
- 다양한 Agent와 MCP Server의 **유연한 연동 및 관리**
- 일반 사용자들이 **하나의 생태계**에서 모든 AI 서비스 이용

### 현재 문제
```
LLM이 코어 수정 → 다른 팀 연쇄 수정 → 반복 테스트 → 개발 지연
```

### 해결책
```
Schema 정의 → 코드 자동 생성 → 변경 시 자동 동기화 → 테스트 1회
```

---

## 🏆 100점 전략: Schema-First Development

### 핵심 원칙

> **"스키마가 진실의 원천(Single Source of Truth)이다"**
> 
> 코드를 직접 수정하지 말고, 스키마를 수정하면 코드가 자동 생성된다.

---

## 📁 1. 중앙 스키마 저장소 구축

### 폴더 구조

```
k-jarvis-contracts/           # 새로운 독립 저장소
├── schemas/
│   ├── a2a-protocol.yaml     # A2A 프로토콜 스키마
│   ├── orchestrator-api.yaml # Orchestrator API
│   ├── agent-api.yaml        # Agent API
│   ├── mcphub-api.yaml       # MCPHub API
│   └── common/
│       ├── headers.yaml      # 공통 헤더 정의
│       ├── errors.yaml       # 공통 에러 코드
│       └── types.yaml        # 공통 타입 정의
├── generated/                # 자동 생성된 코드 (수정 금지)
│   ├── python/
│   ├── typescript/
│   └── java/
├── tests/
│   └── contract-tests/       # 계약 테스트
└── CHANGELOG.md              # 스키마 변경 이력
```

### 스키마 예시

```yaml
# schemas/common/headers.yaml
# ⚠️ 이 파일 변경 시 모든 팀 영향 - 합의 필수
version: "1.0.0"
status: LOCKED

headers:
  X-MCPHub-User-Id:
    type: string
    format: uuid
    required: true
    description: "K-Auth User ID for MCPHub token lookup"
    example: "40e8f8b8-6c96-4042-b8ab-0b2d8e59093e"
    
  X-Request-Id:
    type: string
    format: uuid
    required: false
    description: "Request tracing ID"
    
  Content-Type:
    type: string
    const: "application/json"
    required: true
```

```yaml
# schemas/a2a-protocol.yaml
version: "1.0.0"
status: LOCKED

request:
  type: object
  required: [jsonrpc, method, id]
  properties:
    jsonrpc:
      type: string
      const: "2.0"
    method:
      type: string
      enum: ["message/send", "tasks/send"]
    params:
      type: object
      properties:
        message:
          $ref: "#/definitions/Message"
    id:
      type: string
      format: uuid

response:
  type: object
  required: [jsonrpc, result, id]
  properties:
    jsonrpc:
      type: string
      const: "2.0"
    result:
      $ref: "#/definitions/TaskResult"
    id:
      type: string
```

---

## 🔄 2. 코드 자동 생성 시스템

### 원리

```
스키마 변경 → CI/CD → 코드 자동 생성 → 각 팀 저장소에 PR 생성
```

### 자동 생성 스크립트

```python
# scripts/generate_code.py
"""
스키마에서 코드 자동 생성
각 팀은 이 코드를 직접 수정하면 안됨!
"""
import yaml
from pathlib import Path
from jinja2 import Template

def generate_python_client(schema_path: str, output_path: str):
    """Python 클라이언트 코드 생성"""
    with open(schema_path) as f:
        schema = yaml.safe_load(f)
    
    template = Template('''
# ⚠️ AUTO-GENERATED CODE - DO NOT MODIFY
# Generated from: {{ schema_path }}
# Version: {{ version }}

from dataclasses import dataclass
from typing import Optional
import uuid

@dataclass
class A2ARequest:
    """A2A 프로토콜 요청 - 자동 생성됨"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: dict = None
    id: str = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())

@dataclass
class RequestHeaders:
    """필수 헤더 - 자동 생성됨"""
    x_mcphub_user_id: str  # Required
    x_request_id: Optional[str] = None
    content_type: str = "application/json"
    
    def to_dict(self) -> dict:
        headers = {
            "Content-Type": self.content_type,
            "X-MCPHub-User-Id": self.x_mcphub_user_id,
        }
        if self.x_request_id:
            headers["X-Request-Id"] = self.x_request_id
        return headers
''')
    
    code = template.render(
        schema_path=schema_path,
        version=schema.get('version', '1.0.0')
    )
    
    Path(output_path).write_text(code)
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    generate_python_client(
        "schemas/a2a-protocol.yaml",
        "generated/python/a2a_client.py"
    )
```

### 각 팀 적용 방법

```python
# orchestrator/app/orchestrator.py

# ❌ 잘못된 방법: 직접 구현
class A2ARequest:
    def __init__(self, method, params):
        self.jsonrpc = "2.0"  # 이걸 직접 수정하면 안됨!
        ...

# ✅ 올바른 방법: 자동 생성된 코드 import
from k_jarvis_contracts.a2a_client import A2ARequest, RequestHeaders

def call_agent(self, agent_url: str, message: str, kauth_user_id: str):
    # 자동 생성된 클래스 사용
    request = A2ARequest(
        method="message/send",
        params={"message": message}
    )
    headers = RequestHeaders(x_mcphub_user_id=kauth_user_id)
    
    response = await httpx.post(
        f"{agent_url}/a2a",
        json=request.__dict__,
        headers=headers.to_dict()
    )
```

---

## 🔒 3. LLM 개발 규칙 (각 팀 필수 적용)

### 각 팀 `.cursorrules`에 추가

```markdown
## 🚨 K-Jarvis 개발 거버넌스 규칙

### 절대 금지 (NEVER)
1. `k_jarvis_contracts/` 내 자동 생성된 코드 수정 금지
2. A2A 프로토콜 관련 클래스 직접 구현 금지
3. 팀 간 인터페이스(헤더, 요청/응답 형식) 임의 변경 금지

### 필수 사용 (ALWAYS)
1. `from k_jarvis_contracts import ...` 로 import
2. 인터페이스 변경 필요 시 → 스키마 변경 제안 문서 먼저 작성
3. 새 기능 추가 시 → 기존 인터페이스와 독립적으로 구현

### 변경이 필요한 경우 절차
1. docs/에 `TO_ALL_TEAMS_SCHEMA_CHANGE_제안내용.md` 작성
2. 모든 팀 동의 (48시간 내)
3. 스키마 저장소에서 스키마 수정
4. 코드 자동 재생성
5. 각 팀 테스트 후 적용

### 허용되는 변경
- 내부 비즈니스 로직 (인터페이스 영향 없음)
- 새로운 optional 필드 추가 (기존 필드 변경 없음)
- 성능 최적화 (입출력 동일)
```

---

## 📊 4. 변경 영향 자동 분석

### GitHub Action 설정

```yaml
# .github/workflows/schema-change-detector.yml
name: Schema Change Detector

on:
  pull_request:
    paths:
      - 'schemas/**'

jobs:
  analyze-impact:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Detect Schema Changes
        id: detect
        run: |
          CHANGED_FILES=$(git diff --name-only origin/main...HEAD -- schemas/)
          echo "changed_files=$CHANGED_FILES" >> $GITHUB_OUTPUT
          
      - name: Analyze Impact
        run: |
          python scripts/analyze_impact.py ${{ steps.detect.outputs.changed_files }}
          
      - name: Notify Teams
        run: |
          # Slack/Teams 알림
          echo "⚠️ 스키마 변경 감지!"
          echo "영향받는 팀: Orchestrator, Agent, MCPHub"
          echo "변경 파일: ${{ steps.detect.outputs.changed_files }}"
          
      - name: Create Team PRs
        run: |
          # 각 팀 저장소에 자동 PR 생성
          python scripts/create_team_prs.py
```

---

## 🧪 5. 계약 테스트 자동화

### Golden File Testing

```python
# tests/contract/test_golden_files.py
"""
Golden File Test: 실제 응답과 저장된 스냅샷 비교
스키마 위반 시 자동 감지
"""
import json
import pytest
from pathlib import Path

GOLDEN_DIR = Path("tests/golden_files")

class TestGoldenFiles:
    
    def test_a2a_request_format(self):
        """A2A 요청 형식이 스키마와 일치하는지 확인"""
        golden = json.loads((GOLDEN_DIR / "a2a_request.json").read_text())
        
        # 실제 생성된 요청
        from k_jarvis_contracts import A2ARequest
        actual = A2ARequest(method="message/send", params={})
        
        # 구조 비교
        assert actual.jsonrpc == golden["jsonrpc"]
        assert "method" in actual.__dict__
        assert "id" in actual.__dict__
    
    def test_header_format(self):
        """헤더 형식이 스키마와 일치하는지 확인"""
        golden = json.loads((GOLDEN_DIR / "headers.json").read_text())
        
        from k_jarvis_contracts import RequestHeaders
        headers = RequestHeaders(x_mcphub_user_id="test-uuid")
        actual = headers.to_dict()
        
        # 필수 헤더 존재 확인
        for required_header in golden["required"]:
            assert required_header in actual, f"Missing required header: {required_header}"
```

### Golden Files 예시

```json
// tests/golden_files/a2a_request.json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "content": "테스트 메시지"
    }
  },
  "id": "uuid-format"
}
```

```json
// tests/golden_files/headers.json
{
  "required": ["Content-Type", "X-MCPHub-User-Id"],
  "optional": ["X-Request-Id"]
}
```

---

## 📋 6. 즉시 실행 체크리스트

### Phase 1: 이번 주 (필수)

| # | 작업 | 담당 | 완료 |
|---|------|------|------|
| 1 | `.cursorrules`에 거버넌스 규칙 추가 | 모든 팀 | ☐ |
| 2 | 현재 인터페이스를 YAML 스키마로 문서화 | Orchestrator | ☐ |
| 3 | 팀별 Golden File 생성 | 모든 팀 | ☐ |

### Phase 2: 다음 주 (권장)

| # | 작업 | 담당 | 완료 |
|---|------|------|------|
| 4 | `k-jarvis-contracts` 저장소 생성 | Orchestrator | ☐ |
| 5 | 코드 자동 생성 스크립트 구현 | Orchestrator | ☐ |
| 6 | Contract Test 작성 | 모든 팀 | ☐ |

### Phase 3: 2주 후 (완성)

| # | 작업 | 담당 | 완료 |
|---|------|------|------|
| 7 | GitHub Action 설정 | Orchestrator | ☐ |
| 8 | 자동 생성 코드로 전환 | 모든 팀 | ☐ |
| 9 | 변경 영향 분석 자동화 | Orchestrator | ☐ |

---

## 🎯 기대 효과

### Before (현재)
```
코드 수정 → 테스트 실패 → 원인 분석 → 다른 팀 수정 → 재테스트 → 반복
평균 변경 사이클: 3-5회
```

### After (적용 후)
```
스키마 변경 제안 → 팀 동의 → 스키마 수정 → 코드 자동 생성 → 테스트 1회
평균 변경 사이클: 1회
```

| 항목 | Before | After |
|------|--------|-------|
| 변경 사이클 | 3-5회 | 1회 |
| 테스트 반복 | 많음 | 최소화 |
| 팀 간 충돌 | 빈번 | 거의 없음 |
| LLM 무단 수정 | 발생 | 방지됨 |

---

## 📝 응답 요청

각 팀은 이 거버넌스 적용에 동의하시면 응답 문서를 작성해주세요:

**파일명**: `TO_ORCHESTRATOR_GOVERNANCE_ACK_20251217.md`

```markdown
# [팀명] 개발 거버넌스 동의

**작성일**: 2024-12-17
**작성팀**: [팀명]

## 동의 여부
- [x] K-Jarvis 개발 거버넌스 v1.0에 동의합니다

## Phase 1 완료 예정일
- .cursorrules 업데이트: YYYY-MM-DD
- Golden File 생성: YYYY-MM-DD

## 추가 의견
- (있으면 작성)
```

---

## 💡 핵심 메시지

> **"코드를 수정하지 말고, 스키마를 수정하라"**
> 
> 스키마가 바뀌면 코드는 자동으로 따라온다.
> LLM은 자동 생성된 코드를 절대 수정하면 안 된다.

---

**K-Jarvis v2.0 - 안정적인 생태계를 향해** 🚀

**Orchestrator Team (K-Auth + Orchestrator 담당)**

