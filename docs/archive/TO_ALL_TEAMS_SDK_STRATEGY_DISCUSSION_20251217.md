# SDK 전략 재논의 요청 - 외부 프로토콜 버전 관리 문제

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team  
**수신팀**: Agent Team, K-ARC Team

---

## 🚨 중요 논의 사항

SDK 개발 합의 전, **반드시 논의해야 할 핵심 이슈**가 있습니다.

---

## ❓ 핵심 질문

### MCP와 A2A 프로토콜은 외부에서 관리됩니다

| 프로토콜 | 관리 주체 | 버전 업데이트 | 우리 의존도 |
|---------|----------|--------------|------------|
| **A2A Protocol** | Google | 불규칙 (신규 프로토콜) | Agent SDK |
| **MCP Protocol** | Anthropic | 활발히 업데이트 중 | MCP SDK |

**문제점**:
```
외부 프로토콜 업데이트
    ↓
우리 SDK 업데이트 필요
    ↓
모든 Agent/MCP 서버 업데이트 필요
    ↓
테스트, 배포 비용 발생
    ↓
계속 따라가야 하는 유지보수 부담
```

---

## 🤔 각 팀의 의견을 구합니다

### 질문 1: SDK가 정말 최선인가?

외부 프로토콜 버전 관리 부담을 고려할 때, 어떤 접근법이 좋을까요?

---

### Option A: Full SDK 개발 (원안)

```python
# 우리가 A2A/MCP를 완전히 래핑
from k_jarvis_agent_sdk import Agent

agent = Agent(name="My Agent")

@agent.skill(name="search")
async def search(query: str):
    return result
```

| 장점 | 단점 |
|------|------|
| ✅ 개발자 경험 최고 | ❌ **A2A/MCP 버전 추적 부담** |
| ✅ 완전한 추상화 | ❌ 프로토콜 변경 시 SDK 전체 수정 |
| ✅ 거버넌스 자동 적용 | ❌ 유지보수 팀 필요 |

---

### Option B: Thin Wrapper (가벼운 래퍼)

```python
# 공식 SDK 위에 우리 플랫폼 특화 기능만 추가
from python_a2a import A2AServer  # 공식 SDK 직접 사용
from k_jarvis_utils import KJarvisHeaders, MCPHubClient  # 우리 유틸만

class MyAgent(A2AServer):
    def __init__(self):
        super().__init__()
        self.headers = KJarvisHeaders()  # K-Jarvis 헤더 처리
        self.mcp = MCPHubClient()         # MCPHub 연동만
    
    def handle_message(self, message):
        user_id = self.headers.get_mcphub_user_id()
        # 비즈니스 로직
```

| 장점 | 단점 |
|------|------|
| ✅ 공식 SDK 버전 자동 추적 | ❌ 개발자가 A2A/MCP 이해 필요 |
| ✅ 유지보수 부담 적음 | ❌ 보일러플레이트 여전히 존재 |
| ✅ 유연성 높음 | ❌ 거버넌스 강제 어려움 |

---

### Option C: Template/Generator (템플릿 생성기)

```bash
# CLI로 프로젝트 생성만 제공
$ k-jarvis create my-agent --template basic

# 생성된 코드 (공식 SDK 직접 사용)
my-agent/
├── main.py          # python_a2a 직접 사용
├── config.yaml      # K-Jarvis 설정
├── requirements.txt # 공식 SDK 버전 지정
└── Dockerfile
```

| 장점 | 단점 |
|------|------|
| ✅ 유지보수 부담 최소 | ❌ 생성 후 업데이트 어려움 |
| ✅ 공식 SDK 100% 활용 | ❌ 거버넌스 적용 안됨 |
| ✅ 빠른 시작점 제공 | ❌ 코드 품질 편차 |

---

### Option D: Builder Only (노코드 플랫폼만)

```
사용자 → K-Jarvis Web UI → 설정만 입력 → 서버가 Agent 실행

┌─────────────────────────────────────────────────────────┐
│  K-Jarvis Agent Builder                                 │
│                                                          │
│  이름: [My Agent                    ]                   │
│  MCP 서버: [✓] Confluence  [✓] Jira  [ ] GitHub        │
│  프롬프트: [당신은 문서 관리 전문가입니다...]           │
│                                                          │
│              [테스트]        [배포]                      │
└─────────────────────────────────────────────────────────┘
```

| 장점 | 단점 |
|------|------|
| ✅ 프로토콜 몰라도 됨 | ❌ 커스터마이징 제한 |
| ✅ 버전 관리 우리가 통제 | ❌ 개발 비용 높음 |
| ✅ 비개발자도 사용 가능 | ❌ 복잡한 로직 불가 |

---

### Option E: 하이브리드 (권장?)

```
전문 개발자 → Thin Wrapper (Option B)
일반 사용자 → Builder (Option D)
```

| 장점 | 단점 |
|------|------|
| ✅ 모든 사용자 커버 | ❌ 두 가지 모두 개발 필요 |
| ✅ 유연성 + 편의성 | ❌ 복잡도 증가 |

---

## 📊 비교 요약

| Option | 개발 비용 | 유지보수 | DX | 거버넌스 | 버전 추적 부담 |
|--------|----------|---------|-----|---------|---------------|
| A. Full SDK | 높음 | **높음** | ⭐⭐⭐ | ⭐⭐⭐ | **🔴 높음** |
| B. Thin Wrapper | 중간 | 낮음 | ⭐⭐ | ⭐⭐ | 🟢 낮음 |
| C. Template | 낮음 | 최소 | ⭐ | ⭐ | 🟢 낮음 |
| D. Builder | 높음 | 중간 | ⭐⭐⭐ | ⭐⭐⭐ | 🟡 중간 |
| E. Hybrid (B+D) | 높음 | 중간 | ⭐⭐⭐ | ⭐⭐⭐ | 🟢 낮음 |

---

## 🔍 실제 사례 분석

### 1. Slack SDK

```python
# Slack은 Full SDK 제공
from slack_sdk import WebClient

client = WebClient(token="...")
client.chat_postMessage(channel="#general", text="Hello")
```

- **전략**: Full SDK
- **유지보수**: Slack 공식 팀이 담당
- **우리와 차이점**: 자체 프로토콜 → 버전 통제 가능

### 2. LangChain

```python
# LangChain은 다양한 LLM을 래핑
from langchain.llms import OpenAI, Anthropic

# 각 LLM Provider 버전 변경 시 LangChain이 대응
```

- **전략**: Full Wrapper SDK
- **문제점**: OpenAI API 변경 시 LangChain 업데이트 지연 발생
- **교훈**: 외부 의존성이 많으면 유지보수 부담 큼

### 3. Terraform Provider

```hcl
# Terraform은 각 클라우드를 Provider로 분리
provider "aws" {
  version = "~> 4.0"
}
```

- **전략**: Plugin/Provider 분리
- **장점**: AWS SDK 업데이트 = AWS Provider만 업데이트
- **적용 가능**: A2A Provider, MCP Provider로 분리?

---

## ❓ 각 팀에 질문

### Agent Team에게

1. **A2A 프로토콜 버전 변경 빈도**는 어느 정도인가요?
2. Full SDK 유지보수에 **참여할 의향**이 있나요?
3. Thin Wrapper로도 **충분히 편해질 수 있나요?**
4. **어떤 Option**이 현실적이라고 생각하나요?

### K-ARC Team에게

1. **MCP 프로토콜 버전 변경 빈도**는 어느 정도인가요?
2. MCP SDK를 완전히 래핑하는 것이 **가능한가요?**
3. K-ARC 자체가 **MCP 버전 업데이트를 흡수**할 수 있나요?
4. **어떤 Option**이 현실적이라고 생각하나요?

---

## 💡 Orchestrator Team 초기 의견

### Option E (Thin Wrapper + Builder) 경향

**이유**:
1. Full SDK는 유지보수 부담이 너무 큼
2. 하지만 템플릿만으로는 거버넌스 부족
3. Thin Wrapper로 핵심 기능만 제공하고
4. Builder로 비개발자/빠른 프로토타입 지원

**제안 구조**:
```
┌────────────────────────────────────────────────────────────────┐
│                      K-Jarvis Platform                         │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────┐  ┌─────────────────────────┐  │
│  │    k-jarvis-utils           │  │    Agent Builder        │  │
│  │    (Thin Wrapper)           │  │    (노코드 UI)          │  │
│  │                             │  │                         │  │
│  │  • KJarvisHeaders           │  │  • 드래그앤드롭         │  │
│  │  • MCPHubClient             │  │  • 템플릿 기반          │  │
│  │  • ErrorHandler             │  │  • 설정만으로 Agent     │  │
│  │  • AgentCard 검증기         │  │                         │  │
│  │                             │  │                         │  │
│  │  ** 공식 SDK 래핑 안함 **   │  │  ** 프로토콜 숨김 **    │  │
│  └──────────────┬──────────────┘  └──────────────┬──────────┘  │
│                 │                                │              │
│                 ▼                                ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              공식 SDK (버전 업데이트 자동 추적)           │  │
│  │                                                           │  │
│  │  python-a2a (A2A)        @modelcontextprotocol/sdk (MCP) │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 📋 응답 양식

각 팀은 아래 형식으로 의견을 공유해주세요:

```markdown
# [팀명] SDK 전략 의견

## 1. 선호 Option
- [ ] A. Full SDK
- [ ] B. Thin Wrapper
- [ ] C. Template/Generator
- [ ] D. Builder Only
- [ ] E. Hybrid (B+D)
- [ ] 기타: _______

## 2. 선택 이유
...

## 3. 외부 프로토콜 버전 관리 의견
- A2A/MCP 버전 변경 빈도 경험:
- 버전 추적 부담에 대한 의견:

## 4. 유지보수 참여 의향
- [ ] SDK 유지보수에 적극 참여 가능
- [ ] 제한적 참여 가능
- [ ] 참여 어려움

## 5. 추가 의견
...
```

---

## 📅 일정 관련 공지

### ❌ 날짜별 Phase 일정은 운영하지 않습니다

이전 문서에서 제안한 날짜별 일정(Phase 1: 12/18-20, Phase 2: 12/21-25 등)은 **폐기**합니다.

**이유**:
- 연말 휴가, 다른 업무 등 각 팀 상황이 다름
- 날짜에 쫓기면 품질 저하
- 유연한 진행이 더 현실적

---

### ✅ 체크리스트 기반 진행

**앞으로 모든 작업은 체크리스트로 관리합니다:**

```markdown
## K-Jarvis SDK 개발 체크리스트

### Phase 1: 전략 확정
- [ ] SDK 전략 합의 (Full SDK / Thin Wrapper / Builder 등)
- [ ] 각 팀 역할 분담 확정
- [ ] k-jarvis-contracts 스키마 초안

### Phase 2: 설계
- [ ] SDK API 인터페이스 설계 문서
- [ ] 스키마 리뷰 완료
- [ ] 프로토타입 범위 확정

### Phase 3: 개발
- [ ] k-jarvis-utils (또는 SDK) 프로토타입
- [ ] k-arc-mcp-sdk 프로토타입 (K-ARC)
- [ ] Agent Builder UI 프로토타입 (필요시)

### Phase 4: 테스트
- [ ] 기존 Agent에 적용 테스트 (Agent Team)
- [ ] 기존 MCP 서버에 적용 테스트 (K-ARC)
- [ ] 통합 테스트

### Phase 5: 마무리
- [ ] 문서화 완료
- [ ] 배포 (PyPI/npm)
- [ ] 기존 Agent/MCP 마이그레이션
```

**진행 방식**:
- 각 팀이 자기 속도에 맞게 체크리스트 완료
- 완료 시 문서로 공유
- 다음 단계는 의존성 있는 항목 완료 후 진행

---

## 📋 응답 요청

SDK 전략에 대한 각 팀 의견을 공유해주세요.

**응답 양식** (위 섹션 참조)으로 의견 부탁드립니다.

---

**Orchestrator Team** 🚀

