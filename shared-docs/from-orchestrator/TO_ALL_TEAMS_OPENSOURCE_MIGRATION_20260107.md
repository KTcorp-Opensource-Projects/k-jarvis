# K-Jarvis 오픈소스 이행 공지

**작성일**: 2026-01-07  
**작성팀**: Orchestrator Team  
**수신**: Agent Team, MCPHub Team  
**긴급도**: 🔴 높음

---

## 📋 요약

K-Jarvis 에코시스템을 오픈소스로 배포하기 위해 다음과 같이 구조를 변경합니다.

---

## 🔄 주요 변경 사항

### 1. Agent 등록 기능 복원

**변경 내용:**
- Agent 등록 기능을 다시 **Orchestrator에 포함**
- Agent Card Service는 별도로 유지하되, **같은 Repository에서 관리**

**이유:**
- 오픈소스 사용자가 하나의 repo만 clone해서 전체 기능 사용 가능
- 관리 편의성 및 일관성

### 2. Repository 구조

```
k-jarvis (GitHub Public Repo)
├── backend/                    # Orchestrator Backend
│   ├── app/
│   │   ├── orchestrator.py
│   │   ├── registry.py         # Agent 등록/관리 (복원)
│   │   └── ...
│   └── ...
├── frontend/                   # Orchestrator Frontend
├── agent-catalog/              # Agent Card Service (통합)
│   ├── app/
│   └── docker-compose.yml
├── packages/                   # SDK
│   └── k-jarvis-utils/
├── docker-compose.yml          # 전체 통합 실행
├── README.md
├── LICENSE                     # Apache 2.0
└── CONTRIBUTING.md
```

### 3. MCPHub Team 요청 사항

⚠️ **MCPHub 팀은 Agent Card 등록 관련 소스를 제거해 주세요**

**제거 대상:**
- Agent Card 등록/조회 API
- Agent Card 관련 DB 테이블/로직
- Agent Card 프론트엔드 컴포넌트

**이유:**
- Agent Card는 Orchestrator repo에서 통합 관리
- 중복 제거로 코드 간소화
- 오픈소스 배포 시 혼란 방지

---

## 📦 오픈소스 배포 구성

### Public Repository

| 서비스 | Repository 이름 | 담당 팀 |
|--------|-----------------|---------|
| K-Jarvis (Orchestrator + Agent Card + SDK) | `k-jarvis` | Orchestrator |
| K-Auth | `k-auth` | Orchestrator |
| K-ARC (MCPHub) | `k-arc` | MCPHub |
| Sample Agents | `k-jarvis-agents` | Agent |
| Sample MCP Servers | `k-jarvis-mcp-servers` | MCPHub |

### SDK 포함

**k-jarvis repo에 포함될 SDK:**
- `packages/k-jarvis-utils` - Python SDK for Agent Development

**k-arc repo에 포함될 SDK:**
- `packages/k-arc-utils` - TypeScript SDK for MCP Server Development

---

## ✅ 각 팀 체크리스트

### Orchestrator Team (우리)

- [x] 현재 상태 커밋
- [x] 오픈소스 브랜치 생성 (`opensource/v1.0.0`)
- [ ] Agent Card Service를 같은 repo로 통합
- [ ] Agent 등록 기능 복원 확인
- [ ] SDK 통합
- [ ] 전체 Docker Compose 통합

### MCPHub Team

- [ ] Agent Card 관련 소스 제거
  - [ ] Agent Card API 제거
  - [ ] Agent Card DB 스키마 제거
  - [ ] Agent Card Frontend 제거
- [ ] K-ARC 브랜딩 적용
- [ ] README.md 작성
- [ ] .env.example 정리 (credential 제거)

### Agent Team

- [ ] Sample Agent 코드 정리
- [ ] README.md 작성
- [ ] .env.example 정리 (credential 제거)
- [ ] Agent 개발 가이드 작성

---

## 📅 일정

| 단계 | 기간 | 내용 |
|------|------|------|
| **1단계** | 이번 주 | 각 팀 코드 정리 |
| **2단계** | 다음 주 | 통합 테스트 |
| **3단계** | 2주 후 | Public GitHub 배포 |

---

## 🔒 보안 주의사항

### 반드시 제거해야 할 항목

```
❌ API Keys (OpenAI, Azure, Anthropic, Google)
❌ Database 비밀번호
❌ JWT Secret Keys
❌ OAuth Client Secrets
❌ 내부 서버 URL/IP
❌ 회사 내부 정보
```

### Git History 정리

기존 커밋에 민감 정보가 있다면 BFG 또는 git-filter-repo로 제거 필요

---

## 📞 문의

질문이나 논의 사항이 있으면 문서로 공유해 주세요.

**다음 단계:**
1. 각 팀 체크리스트 확인 후 작업 시작
2. 완료 시 문서로 공유
3. 통합 테스트 진행

---

**오픈소스 배포를 위해 협조 부탁드립니다! 🚀**

