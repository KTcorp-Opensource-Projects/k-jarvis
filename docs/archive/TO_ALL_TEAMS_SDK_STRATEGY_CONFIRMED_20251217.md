# K-Jarvis SDK 전략 최종 합의

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team  
**수신팀**: Agent Team, K-ARC Team

---

## ✅ 합의 완료

3팀의 의견을 종합한 결과, **SDK 전략이 확정**되었습니다.

---

## 🎯 최종 결정

### Option E: Thin Wrapper + Builder (장기)

| 결정 사항 | 내용 |
|----------|------|
| **전략** | **Thin Wrapper** (공식 SDK 래핑 안함) |
| **Full SDK** | ❌ **개발하지 않음** (버전 추적 부담) |
| **Builder** | 장기 계획 (수요 검증 후) |
| **일정 방식** | 날짜 X → **체크리스트 기반** |

---

## 📦 확정된 패키지 구조

### 1. k-jarvis-utils (Python)

**담당**: Orchestrator Team + Agent Team

```python
from k_jarvis_utils import (
    # 헤더 처리
    KJarvisHeaders,
    
    # MCP 연동
    MCPHubClient,
    MCPErrorHandler,
    
    # A2A 유틸리티
    A2AResponseBuilder,
    JsonRpcError,
    
    # Agent Card
    AgentCardValidator,
    
    # 테스트
    ContractTestBase,
)
```

**범위**:
- ✅ K-Jarvis 플랫폼 특화 기능
- ✅ 헤더 처리 (X-MCPHub-User-Id 등)
- ✅ 에러 핸들링 표준화
- ❌ A2A 프로토콜 래핑 (공식 SDK 사용)

### 2. k-arc-utils (TypeScript)

**담당**: K-ARC Team

```typescript
import {
  // 헤더 처리
  extractServiceTokens,
  getMCPHubUserId,
  createUserContext,
  
  // K-ARC 클라이언트
  KARCClient,
  
  // 에러 처리
  KARCError,
  
  // 검증
  validateEnvSchema,
} from '@k-arc/utils';
```

**범위**:
- ✅ K-ARC 플랫폼 연동
- ✅ 서비스 토큰 처리
- ✅ 환경변수 스키마 검증
- ❌ MCP 프로토콜 래핑 (공식 SDK 사용)

### 3. 공식 SDK (버전 추적 위임)

| 프로토콜 | 공식 SDK | 버전 관리 |
|---------|---------|----------|
| **A2A** | python-a2a | Google 담당 |
| **MCP** | @modelcontextprotocol/sdk | Anthropic 담당 |

**우리는 래핑하지 않고 직접 사용**

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        개발자 코드                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────────┐     ┌──────────────────────┐         │
│   │    k-jarvis-utils    │     │     k-arc-utils      │         │
│   │       (Python)       │     │    (TypeScript)      │         │
│   │                      │     │                      │         │
│   │  K-Jarvis 특화 기능  │     │   K-ARC 특화 기능    │         │
│   │  • 헤더 처리         │     │   • 서비스 토큰      │         │
│   │  • 에러 핸들링       │     │   • 사용자 컨텍스트  │         │
│   │  • 계약 테스트       │     │   • 환경변수 검증    │         │
│   │                      │     │                      │         │
│   │  유지보수: 우리 팀   │     │   유지보수: 우리 팀  │         │
│   └──────────┬───────────┘     └──────────┬───────────┘         │
│              │                            │                      │
│              ▼                            ▼                      │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │              공식 SDK (버전 추적 위임)                    │  │
│   │                                                           │  │
│   │   python-a2a (Google)    @modelcontextprotocol/sdk       │  │
│   │                          (Anthropic)                      │  │
│   │                                                           │  │
│   │   유지보수: 공식 팀      유지보수: 공식 팀               │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 👥 역할 분담 (확정)

| 패키지 | 주담당 | 협업 |
|--------|-------|------|
| **k-jarvis-utils** | Orchestrator | Agent Team |
| **k-arc-utils** | K-ARC | - |
| **k-jarvis-contracts** | Orchestrator | Agent, K-ARC |
| **Builder (장기)** | Orchestrator | K-ARC |

### Agent Team 담당 범위

```markdown
✅ k-jarvis-utils 협업
  - KJarvisHeaders 구현
  - MCPErrorHandler 구현  
  - 사용 문서화
  - 베타 테스트 (기존 Agent에 적용)

❌ 담당하지 않음
  - A2A 프로토콜 래핑
  - Builder UI 개발
```

### K-ARC Team 담당 범위

```markdown
✅ k-arc-utils 주도
  - TypeScript 버전 개발
  - MCP 스키마 기여
  - K-ARC 포털에 MCP 서버 간편 등록 (Builder 역할)

❌ 담당하지 않음
  - MCP 프로토콜 래핑
  - Agent SDK
```

---

## ✅ 확정된 체크리스트

### Phase 1: 전략 확정 ✅ 완료
- [x] SDK 전략 논의 시작 (Orchestrator)
- [x] Agent Team 의견 제출
- [x] K-ARC Team 의견 제출
- [x] **최종 합의 문서 (이 문서)**

### Phase 2: 설계
- [ ] k-jarvis-utils API 설계 (Orchestrator + Agent)
- [ ] k-arc-utils API 설계 (K-ARC)
- [ ] k-jarvis-contracts 스키마 초안 (Orchestrator)

### Phase 3: 개발
- [ ] k-jarvis-utils 프로토타입 (Orchestrator + Agent)
- [ ] k-arc-utils 프로토타입 (K-ARC)

### Phase 4: 테스트
- [ ] Confluence Agent에 k-jarvis-utils 적용 (Agent)
- [ ] Jira Agent에 적용 (Agent)
- [ ] GitHub Agent에 적용 (Agent)
- [ ] MCP 서버에 k-arc-utils 적용 (K-ARC)

### Phase 5: 배포 및 문서화
- [ ] k-jarvis-utils PyPI 배포
- [ ] k-arc-utils npm 배포 (@k-arc/utils)
- [ ] 사용 가이드 문서화
- [ ] Confluence 개발자 문서 업데이트

---

## 📊 기대 효과

### 코드 감소 (예상)

| 영역 | 현재 | Thin Wrapper 후 | 감소율 |
|------|------|----------------|--------|
| Agent 보일러플레이트 | ~500줄 | ~250줄 | **50%** |
| MCP 서버 연동 코드 | ~200줄 | ~100줄 | **50%** |

### 유지보수 부담

| 항목 | Full SDK | Thin Wrapper |
|------|---------|--------------|
| 외부 프로토콜 추적 | 🔴 높음 | 🟢 **없음** |
| 코드 유지보수 | 🔴 높음 | 🟢 **낮음** |
| 버전 호환성 | 🔴 복잡 | 🟢 **단순** |

---

## 💬 마무리

### Full SDK를 안 만드는 이유 (재확인)

> **A2A, MCP는 활발히 개발 중인 외부 프로토콜입니다.**
> 
> Full SDK로 래핑하면:
> - 버전 변경 시 우리 SDK 전체 수정 필요
> - 모든 Agent/MCP 서버 재테스트 필요
> - 유지보수 팀 상시 필요
> 
> **Thin Wrapper는:**
> - 공식 SDK가 버전 추적 담당
> - 우리는 플랫폼 특화 기능만 담당
> - 유지보수 부담 최소화

### 다음 단계

각 팀은 **Phase 2 (설계)** 체크리스트를 시작해주세요:

- **Orchestrator**: k-jarvis-utils API 설계 시작
- **Agent Team**: k-jarvis-utils 협업 대기
- **K-ARC Team**: k-arc-utils API 설계 시작

---

## 📎 참조 문서

- Agent Team 의견: `TO_ORCHESTRATOR_SDK_STRATEGY_RESPONSE_20251217.md`
- K-ARC Team 의견: `TO_ORCHESTRATOR_SDK_STRATEGY_RESPONSE_20251217.md`
- 전략 논의: `TO_ALL_TEAMS_SDK_STRATEGY_DISCUSSION_20251217.md`

---

**SDK 전략 합의 완료! 🚀**

**Orchestrator Team**

