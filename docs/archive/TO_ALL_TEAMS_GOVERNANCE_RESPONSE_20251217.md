# 개발 거버넌스 응답 및 후속 계획

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team (K-Auth + K-Jarvis 담당)  
**수신팀**: Agent Team, MCPHub Team

---

## 📢 요약

두 팀의 거버넌스 동의 및 피드백에 감사드립니다.  
질문사항에 대한 답변과 후속 계획을 안내드립니다.

---

## ✅ 동의 현황

| 팀 | 거버넌스 동의 | .cursorrules | FROZEN ZONE | Golden File |
|----|-------------|--------------|-------------|-------------|
| **Agent Team** | ✅ | ⏳ 12/17 | ✅ 정의 완료 | ⏳ 12/18 |
| **MCPHub Team** | ✅ | ✅ 완료 | ✅ 완료 | ⏳ 12/18-19 |
| **Orchestrator Team** | ✅ | ✅ 완료 | ✅ 완료 | ⏳ 12/18 |

**🎉 전체 팀 거버넌스 동의 완료!**

---

## 💬 MCPHub Team 질문 답변

### Q1. k-jarvis-contracts 저장소 생성 시점

**A: 이번 주 내 (12/20까지) 생성 예정**

```
저장소 구조:
k-jarvis-contracts/
├── schemas/
│   ├── a2a-protocol.yaml      # A2A 프로토콜
│   ├── agent-card.yaml        # Agent Card
│   ├── mcphub-api.yaml        # MCPHub API ← 포함
│   └── common/
│       ├── headers.yaml       # 공통 헤더
│       └── types.yaml         # 공통 타입
├── generated/
│   ├── python/               # Python 클라이언트
│   └── typescript/           # TypeScript 클라이언트 ← 제공
└── scripts/
    ├── generate_python.py
    └── generate_typescript.ts # ← Orchestrator Team 제공
```

### Q2. TypeScript 코드 자동 생성 스크립트

**A: Orchestrator Team에서 제공 예정**

- Python 생성 스크립트: ✅ 제공
- TypeScript 생성 스크립트: ✅ 제공 예정 (12/20까지)
- 사용 방법 문서: ✅ 함께 제공

### Q3. MCPHub API 스키마 포함 여부

**A: 예, 중앙 저장소에 포함**

```yaml
# schemas/mcphub-api.yaml (초안)
version: "1.0.0"
status: "DRAFT"

endpoints:
  # 내부 API (Orchestrator/Agent → MCPHub)
  internal:
    - path: "/api/internal/tokens"
      method: "GET"
      description: "X-MCPHub-User-Id 기반 서비스 토큰 조회"
      
  # MCP 프로토콜
  mcp:
    - path: "/mcp"
      method: "POST"
      description: "MCP JSON-RPC 엔드포인트"
```

MCPHub Team에서 상세 스키마 작성 후 PR 요청 부탁드립니다.

---

## 💬 Agent Team 제안 응답

### Contract Test 공동 라이브러리

**A: 좋은 제안입니다. 채택합니다.**

```python
# k_jarvis_contracts/tests/base_contract_test.py
class BaseContractTest:
    """모든 팀이 상속받아 사용하는 기본 계약 테스트"""
    
    def assert_a2a_request_valid(self, request):
        """A2A 요청 유효성 검증"""
        assert request.get("jsonrpc") == "2.0"
        assert request.get("method") in ["message/send", "tasks/send"]
        assert "id" in request
        
    def assert_headers_valid(self, headers):
        """헤더 유효성 검증"""
        assert "Content-Type" in headers
        # X-MCPHub-User-Id는 인증된 요청에서만 필수
        
    def assert_agent_card_valid(self, card):
        """Agent Card 유효성 검증"""
        assert "name" in card
        assert "endpoints" in card
        assert "skills" in card
```

### K-Jarvis 확장 필드 스키마화

**A: 반영하겠습니다.**

```yaml
# schemas/agent-card.yaml
version: "1.0.0"
status: "DRAFT"

# 표준 A2A Agent Card
base:
  name: { type: string, required: true }
  description: { type: string }
  endpoints: { type: object, required: true }
  skills: { type: array }
  
# K-Jarvis 확장 필드
kjarvis_extensions:
  routing:
    domain: { type: string, description: "도메인 (documentation, project_management 등)" }
    category: { type: string, description: "카테고리 (confluence, jira, github 등)" }
    keywords: { type: array, items: string, description: "라우팅 키워드" }
    capabilities: { type: array, items: string }
  requirements:
    mcpHubToken: { type: boolean, default: false }
    mcpServers: { type: array, items: string }
```

---

## 📅 후속 일정

| 날짜 | 작업 | 담당 |
|------|------|------|
| **12/17 (오늘)** | .cursorrules 업데이트 완료 | Agent Team |
| **12/18** | Golden File 생성 | 모든 팀 |
| **12/19** | Contract Test 기본 클래스 작성 | Orchestrator |
| **12/20** | k-jarvis-contracts 저장소 생성 | Orchestrator |
| **12/20** | TypeScript 생성 스크립트 제공 | Orchestrator |
| **12/21 이후** | 자동 생성 코드로 전환 | 모든 팀 |

---

## 📋 각 팀 Action Items

### Agent Team
- [ ] `.cursorrules` 거버넌스 규칙 추가 (12/17)
- [ ] `tests/golden_files/` 생성 (12/18)
- [ ] Agent Card 스키마 검토 및 피드백 (12/19)

### MCPHub Team
- [ ] `tests/golden_files/` 생성 (12/18-19)
- [ ] MCPHub API 스키마 초안 작성 (12/19)
- [ ] K-ARC 리브랜딩 준비 (별도 문서 참조)

### Orchestrator Team
- [ ] k-jarvis-contracts 저장소 생성 (12/20)
- [ ] Python/TypeScript 생성 스크립트 작성 (12/20)
- [ ] BaseContractTest 클래스 작성 (12/19)
- [ ] K-ARC 디자인 에셋 제공 (12/19)

---

**거버넌스 Phase 1 완료를 향해 함께 나아갑시다!** 🚀

**Orchestrator Team**

