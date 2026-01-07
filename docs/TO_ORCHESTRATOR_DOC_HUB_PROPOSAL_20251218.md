# 📚 K-Jarvis 문서 허브 구조 제안

**발신**: K-ARC Team  
**수신**: Orchestrator Team, Agent Team  
**작성일**: 2025-12-18  
**유형**: 문서 구조 개선 제안

---

## 1. 배경

현재 "01. 2026년도 먹거리 발굴" 하위에 K-Jarvis 관련 문서들이 많이 있지만, 팀별로 정리된 허브 문서가 없어서 찾기가 어렵습니다.

### 현재 문제점

```
📁 01. 2026년도 먹거리 발굴
├── K-Jarvis 플랫폼 아키텍처
├── K-Jarvis 사용자별 인증 체인 아키텍처
├── K-Jarvis 1.0 - 전체 아키텍처 및 개발 가이드
├── K-Jarvis 1.0 - 사용자 가이드
├── K-Jarvis 1.0 - 관리자 가이드
├── K-Jarvis 1.0 - Agent 개발 가이드
├── K-Jarvis 1.0 - 전체 아키텍처 다이어그램
├── K-Jarvis v1.0 - Agent Team 후속조치...
└── 02. AI Agent 모음

→ 어떤 문서가 어느 팀 담당인지 불명확
→ 새로 합류하는 개발자가 시작점을 찾기 어려움
```

---

## 2. 제안: 팀별 문서 허브 구조

### K-ARC Team (완료 ✅)

K-ARC Team은 이미 허브 페이지를 생성했습니다:

**📄 K-ARC (MCPHub) 문서 허브**
- URL: https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/569022753
- 내용:
  - K-ARC MCP 서버 개발 가이드 (k-arc-utils)
  - MCPHub Transport 및 세션 관리 기술 가이드
  - MCPHub API Reference
  - MCPHub API 명세서 (Swagger)
  - SDK 링크 (k-arc-utils Python/TypeScript)
  - 로컬 개발 환경 정보

---

### Orchestrator Team (제안)

**📄 K-Jarvis Orchestrator 문서 허브** (신규 생성 제안)

포함 내용:
- K-Jarvis 플랫폼 아키텍처
- K-Jarvis 1.0 - 전체 아키텍처 및 개발 가이드
- K-Auth 기술 가이드
- K-Auth OAuth 2.0 연동 가이드
- A2A Protocol Specification
- k-jarvis-utils SDK 가이드
- 사용자/관리자 가이드

---

### Agent Team (제안)

**📄 K-Jarvis Agent 문서 허브** (신규 생성 제안)

포함 내용:
- Agent Fabric 에이전트 개발 가이드 v1.0
- AI Agent A2A 프로토콜 구현 가이드
- AI Agent 빠른 시작 가이드
- AI Agent FAQ
- K-Jarvis 1.0 - Agent 개발 가이드
- 개발한 Agent 목록 (Jira, Confluence, GitHub 등)

---

## 3. 최종 목표 구조

```
📁 01. 2026년도 먹거리 발굴
│
├── 📂 K-Jarvis Orchestrator 문서 허브 (Orchestrator Team)
│   ├── 🔗 K-Jarvis 플랫폼 아키텍처
│   ├── 🔗 K-Auth 기술 가이드
│   ├── 🔗 A2A Protocol Specification
│   └── 🔗 k-jarvis-utils SDK
│
├── 📂 K-Jarvis Agent 문서 허브 (Agent Team)
│   ├── 🔗 Agent Fabric 개발 가이드
│   ├── 🔗 AI Agent 빠른 시작 가이드
│   └── 🔗 개발한 Agent 목록
│
├── 📂 K-ARC (MCPHub) 문서 허브 (K-ARC Team) ✅ 완료
│   ├── 🔗 K-ARC MCP 서버 개발 가이드
│   ├── 🔗 MCPHub API Reference
│   └── 🔗 SDK (k-arc-utils)
│
└── 📄 (공통) K-Jarvis 1.0 - 사용자 가이드
```

---

## 4. 기대 효과

| 항목 | 효과 |
|------|------|
| **문서 검색 용이** | 팀별 허브에서 시작하여 필요한 문서 빠르게 찾기 |
| **온보딩 개선** | 새 개발자가 자신의 역할에 맞는 허브부터 시작 |
| **유지보수 명확** | 각 팀이 자신의 허브 문서 관리 책임 |
| **중복 방지** | 허브에서 링크로 연결하여 문서 중복 생성 방지 |

---

## 5. 요청 사항

### Orchestrator Team
- [ ] "K-Jarvis Orchestrator 문서 허브" 페이지 생성
- [ ] 관련 문서들 링크로 정리
- [ ] K-Auth, A2A Protocol 문서 포함

### Agent Team
- [ ] "K-Jarvis Agent 문서 허브" 페이지 생성
- [ ] 개발한 Agent 목록 정리
- [ ] Agent 개발 관련 문서 링크 정리

---

## 6. K-ARC 허브 페이지 참고

K-ARC Team이 만든 허브 페이지 구조를 참고하세요:

**URL**: https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/569022753

포함 내용:
1. K-Jarvis 생태계 팀별 허브 링크 (상호 연결)
2. 핵심 문서 목록 (링크 + 설명 + 상태)
3. 관련 문서 (K-Auth, SDK)
4. 로컬 개발 환경 정보
5. 빠른 시작 가이드
6. 연락처

---

**K-ARC Team | 2025-12-18**

