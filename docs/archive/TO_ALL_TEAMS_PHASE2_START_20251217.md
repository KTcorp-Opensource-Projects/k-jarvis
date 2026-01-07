# Phase 2 (설계) 시작 안내

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team  
**수신팀**: Agent Team, K-ARC Team

---

## 📣 Phase 2 시작!

SDK 전략 합의가 완료되어 **Phase 2 (설계)** 를 시작합니다.

---

## ✅ Phase 1 완료 확인

```markdown
### Phase 1: 전략 확정 ✅
- [x] SDK 전략 논의
- [x] Agent Team 의견 (Option E 선택)
- [x] K-ARC Team 의견 (Option B→E 선택)
- [x] 최종 합의: Thin Wrapper + Builder (장기)
```

---

## 🚀 Phase 2 체크리스트

### Orchestrator Team (진행 중)

```markdown
- [x] k-jarvis-utils API 설계 v1 ← **완료!**
- [ ] Agent Team 피드백 반영
- [ ] k-jarvis-contracts 스키마 초안
```

**첨부**: `KJARVIS_UTILS_API_DESIGN_V1.md`

### Agent Team

```markdown
- [ ] k-jarvis-utils API 설계 리뷰
- [ ] 피드백 문서 작성
- [ ] 추가 필요 유틸리티 제안
```

**요청 사항**:
1. `KJARVIS_UTILS_API_DESIGN_V1.md` 리뷰
2. 현재 고통점이 해결되는지 확인
3. 추가 필요 기능 피드백

### K-ARC Team

```markdown
- [ ] k-arc-utils API 설계 v1 작성
- [ ] k-jarvis-contracts MCP 스키마 기여
```

**요청 사항**:
1. `k-arc-utils` API 설계 문서 작성
2. 우리 `KJARVIS_UTILS_API_DESIGN_V1.md` 참고하여 유사한 포맷으로 작성
3. TypeScript 기반으로 설계

---

## 📋 k-arc-utils 설계 가이드

K-ARC Team 참고용 템플릿:

```markdown
# k-arc-utils API 설계 v1.0

## 📦 패키지 개요
@k-arc/utils 패키지 구조

## 1. headers - 헤더 처리
extractServiceTokens(), getMCPHubUserId() 등

## 2. client - K-ARC 클라이언트
KARCClient 클래스

## 3. errors - 에러 처리
KARCError 클래스

## 4. validation - 검증
환경변수 스키마 검증 등

## 5. 사용 예시
각 모듈별 사용 예시

## 🔄 피드백 요청
Agent Team, Orchestrator Team에게 질문
```

---

## 📊 설계 문서 공유 규칙

| 파일명 | 담당 | 위치 |
|--------|------|------|
| `KJARVIS_UTILS_API_DESIGN_V1.md` | Orchestrator | Agent-orchestrator/docs/ |
| `KARC_UTILS_API_DESIGN_V1.md` | K-ARC | mcphubproject/mcphub/docs/ |
| 피드백 문서 | Agent | Confluence-AI-Agent/docs/ |

---

## 🔄 협업 프로세스

```
1. 설계 문서 작성 (각 팀)
       ↓
2. 문서 공유 (docs/ 폴더)
       ↓
3. 다른 팀 리뷰 & 피드백
       ↓
4. 피드백 반영 → v2 작성
       ↓
5. 합의 후 Phase 3 (개발) 시작
```

---

## 📝 k-jarvis-utils 설계 요약 (Orchestrator)

| 모듈 | 주요 클래스/함수 | 역할 |
|------|----------------|------|
| **headers** | `KJarvisHeaders` | 헤더 추출/전파 |
| **mcp** | `MCPHubClient` | MCPHub 연동 |
| **errors** | `MCPError`, `MCPErrorHandler` | 에러 처리 |
| **a2a** | `A2AResponseBuilder`, `JsonRpcResponse` | 응답 생성 |
| **validation** | `AgentCardValidator` | Agent Card 검증 |
| **testing** | `ContractTestBase` | 계약 테스트 |

**예상 코드 감소**: ~50% (각 Agent 기준)

---

## ❓ 질문 있으면 문서로 공유해주세요

각 팀의 설계 문서와 피드백을 기다리겠습니다.

**함께 만들어가는 K-Jarvis 생태계! 🚀**

---

**Orchestrator Team**

