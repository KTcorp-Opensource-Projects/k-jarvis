# 🔍 K-Jarvis 플랫폼 최종 점검 체크리스트

**작성일**: 2024-12-12  
**작성팀**: Orchestrator Team  
**대상**: 모든 팀 (Orchestrator, Agent, MCPHub)

---

## 📋 개요

E2E 테스트 완료 후, 플랫폼 품질 보장을 위해 아래 5가지 항목에 대한 최종 점검이 필요합니다.
**각 팀은 담당 항목을 검토하고, 이 문서의 해당 섹션에 결과를 기재해주세요.**

---

## 1️⃣ DB 구조 및 JIT Provisioning 검토

### 질문
- K-Auth, MCPHub, Orchestrator가 **같은 DB를 공유해야 하는가?**
- K-Auth 계정으로 최초 로그인 시, 각 서비스에 **새로운 유저로 자동 등록되는 구조인가?** (JIT Provisioning)
- 서비스 간 사용자 연결 키는 무엇인가? (`kauth_user_id`?)

### 담당팀별 기재란

#### 🔷 K-Auth Team (Orchestrator 담당)
**현재 구조:**
- [x] K-Auth는 독립 DB 사용 (PostgreSQL: `k_auth`)
- [x] K-Auth에서 발급하는 `sub` (UUID)가 사용자 고유 식별자

**응답:**
```
K-Auth는 독립 DB 사용 (PostgreSQL: k_auth, Port: 5432)
- users 테이블: id mod(UUID), username, email, hashed_password 등
- oauth_clients 테이블: 클라이언트 앱 등록 (MCPHub, Orchestrator)
- 발급 토큰: OAuth 2.0 Access Token, Refresh Token
- sub claim: K-Auth 내 사용자 UUID (각 서비스 연결 키로 사용)

결론: 3개 서비스가 같은 DB를 공유할 필요 없음!
각 서비스는 kauth_user_id (sub)로 사용자를 연결하면 됨.
```

#### 🔷 Orchestrator Team
**현재 구조:**
- [x] Orchestrator는 독립 DB 사용 (PostgreSQL: `agent_orchestrator`)
- [x] K-Auth SSO 로그인 시 `find_or_create_user()` 로직으로 JIT Provisioning 구현
- [x] `kauth_user_id` 컬럼으로 K-Auth 사용자와 연결

**응답:**
```
Orchestrator는 K-Auth와 별도 DB 사용.
K-Auth 최초 로그인 시 Orchestrator DB에 새 사용자 자동 생성 (JIT Provisioning).
사용자 연결 키: kauth_user_id (K-Auth의 sub 값)
```

#### 🔷 MCPHub Team
**현재 구조:**
- [x] MCPHub는 독립 DB 사용 (PostgreSQL: `mcphub`)
- [x] K-Auth SSO 로그인 시 사용자 자동 생성 로직 존재 (JIT Provisioning)
- [x] `kauthUserId` 컬럼으로 K-Auth 연결

**응답:**
```
✅ MCPHub는 K-Auth와 별도 DB 사용 (PostgreSQL: mcphub)
✅ K-Auth 최초 로그인 시 MCPHub DB에 새 사용자 자동 생성 (JIT Provisioning)
✅ 사용자 연결 키: kauthUserId (K-Auth의 sub 값)
✅ 기존 사용자(이메일/username 일치)는 K-Auth 연결 후 재사용

구현 위치: apps/backend/src/routes/kauth-routes.ts
```

---

## 2️⃣ 멀티 에이전트 체이닝 검토

### 질문
- 현재 Orchestrator가 **여러 에이전트를 순차적/병렬로 호출**하는 기능이 구현되어 있는가?
- 예: "Jira에서 이슈 가져와서 Confluence에 정리해줘"

### 담당팀별 기재란

#### 🔷 Orchestrator Team
**현재 구현 상태:**
- [x] 멀티 에이전트 체이닝 구현됨
- [ ] 구현 안됨 / 계획 중
- [x] LLM 기반 워크플로우 분석 및 실행

**응답:**
```
✅ 멀티 에이전트 체이닝 구현 완료!

코드 위치: backend/app/workflow.py (1776 라인)

구현된 기능:
- Phase 1: LLM 기반 동적 워크플로우 분석, N-step 워크플로우 지원
- Phase 2: Supervisor LLM, 에러 복구 (retry/fallback/skip), 구조화된 컨텍스트 전달
- Phase 3: Handoff Pattern (에이전트 간 동적 위임)

핵심 클래스:
- LLMWorkflowAnalyzer: 사용자 요청 분석 → 멀티스텝 필요 여부 판단
- WorkflowExecutor: 워크플로우 순차 실행 (Supervisor 감독)
- HybridWorkflowAnalyzer: 하이브리드 분석기

예시 시나리오:
"Jira에서 이슈 가져와서 Confluence에 정리해줘"
→ Step 1: Jira Agent (이슈 조회)
→ Step 2: Confluence Agent (문서 생성, 이전 결과 사용)

제한사항:
- max_iterations: 기본 10스텝
- 동기적 순차 실행 (병렬 실행 미지원)
```

#### 🔷 Agent Team
**체이닝 지원 여부:**
- [x] Agent가 다른 Agent 호출 가능? → ❌ 없음 (Agent는 자신의 도메인 도구만 사용)
- [x] A2A Protocol에 체이닝 관련 스펙 있음? → Orchestrator가 담당

**응답:**
```
❌ Agent가 다른 Agent를 호출하는 기능 없음
✅ Orchestrator가 "멀티 에이전트 오케스트레이션/체이닝"을 담당하는 구조가 적합
✅ A2A 요청에서 전달된 "이전 결과/컨텍스트"는 입력 메시지에 포함되는 형태로 처리 가능
```

---

## 3️⃣ 코드 품질 검토 (유지보수 관점)

### 검토 항목
각 팀은 자신의 코드베이스에서 아래 항목을 점검해주세요:

| 항목 | 설명 |
|------|------|
| 중복 코드 | 같은 로직이 여러 파일에 존재 |
| 하드코딩 | URL, 토큰, 설정값이 코드에 직접 기재 |
| 데드 코드 | 사용되지 않는 함수/클래스/import |
| 코드 구성 | 파일/폴더 구조가 논리적인지 |
| 로깅 일관성 | logger 사용, 에러 핸들링 |
| 타입 힌트 | Python type hints, TypeScript types |

### 담당팀별 기재란

#### 🔷 Orchestrator Team
```
점검 완료 여부: [x] 일부 완료

발견된 이슈:
- [해결] Option B 레거시 코드 (X-MCP-Hub-Token 직접 전달) 일부 잔존 → 제거 완료
- [해결] _get_user_mcp_token() 미사용 함수 → deprecated 처리
- [검토중] mcp_token_service.py, token_cache.py - Option C에서 불필요, 삭제 검토
- [양호] 환경변수 사용 (하드코딩 없음)
- [양호] loguru logger 일관 사용

개선 계획:
- mcp_token_service.py, token_cache.py 파일 삭제 예정
- 코드 주석 정리 (한국어/영어 혼용 → 한국어 통일)
```

#### 🔷 Agent Team
```
점검 완료 여부: [x]

발견된 이슈 (해결됨):
- Option C 헤더 전달 버그(초기화 순서) → lazy initialization으로 수정
- 문서 중복/난립 → COLLABORATION_HISTORY.md로 통합

잔여 개선 권장:
- X-MCPHub-User-Id 로그 마스킹 권장
- Dev artifacts (agent.log 등) 운영 배포 시 제외
```

#### 🔷 MCPHub Team
```
점검 완료 여부: [x]

발견된 이슈:
- 하드코딩 (localhost): 15개 → 환경변수 fallback 형태 (문제 없음)
- console.log: 97개 → production에서 제거됨
- TODO/FIXME: 6개 → 향후 개선 항목

개선 계획:
- 단기: CORS 설정 환경변수화
- 중기: TODO 항목 해결
- 장기: 코드 리팩토링, 테스트 커버리지 확대
```

---

## 4️⃣ 개발 문서 존재 여부

### 검토 항목

#### 🔷 Orchestrator Team - Agent Card 등록 가이드
- [ ] 새로운 Agent를 Orchestrator에 등록하는 방법 문서화
- [ ] `agent.json` 필수 필드 설명
- [ ] A2A Protocol 준수 사항

**문서 위치:**
```
❌ 미작성 - 작성 예정

작성 예정 내용:
1. Agent 등록 방법 (Admin UI 또는 API)
2. agent.json 필수 필드:
   - name, description, url
   - capabilities (streaming, pushNotifications 등)
   - routing (keywords, domains, description)
3. A2A Protocol 준수 사항:
   - /.well-known/agent.json 엔드포인트
   - /tasks/send POST 엔드포인트
   - 응답 형식 (A2A Message)
4. Option C 연동:
   - X-MCPHub-User-Id 헤더 수신 및 MCPHub 전달
```

#### 🔷 Agent Team - Agent 개발 가이드
- [x] 새로운 Agent 개발 시 필요한 구조
- [x] MCPHub 연동 방법
- [x] X-MCPHub-User-Id 헤더 처리 방법

**문서 위치:**
```
✅ 문서 존재:
- Confluence Agent: Agent-Frabric/Confluence-AI-Agent/docs/
  - ARCHITECTURE.md, SETUP_GUIDE.md, COLLABORATION_HISTORY.md
- Jira Agent: Agent-Frabric/Jira-AI-Agent/docs/
  - A2A_PROTOCOL_COMPLIANCE.md, AGENT_TEST_CHECKLIST.md
```

#### 🔷 MCPHub Team - MCP Server 등록 가이드
- [ ] 새로운 MCP Server를 MCPHub에 등록하는 방법
- [ ] 필수 환경변수 정의 방법
- [ ] 카탈로그 등록 절차

**문서 위치:**
```
⚠️ 일부 미작성:

현재 존재하는 문서:
- docs/ARCHITECTURE.md - 아키텍처 개요
- docs/SETUP_GUIDE.md - 셋업 가이드
- docs/MCPHUB_INTEGRATION_GUIDE.md - 통합 가이드

미작성 (작성 예정):
- docs/MCP_SERVER_REGISTRATION_GUIDE.md
```

---

## 5️⃣ 보안 검토 및 전체 E2E 아키텍처 문서

### 5-1. 보안 검토 항목

| 항목 | 담당팀 | 상태 | 비고 |
|------|--------|------|------|
| JWT 토큰 보안 | K-Auth | | 만료시간, 서명 알고리즘 |
| X-MCPHub-User-Id 헤더 | All | | 위변조 방지책? |
| 서비스 토큰 저장 | MCPHub | | 암호화 여부? |
| API 인증 | All | | 모든 API에 인증 적용? |
| CORS 설정 | All | | 허용 도메인 검토 |
| SQL Injection | All | | ORM 사용 여부 |

### 5-2. 보안 관련 질문

**X-MCPHub-User-Id 헤더 관련:**
- 이 헤더가 위변조될 경우의 대응책은?
- Agent가 악의적으로 다른 사용자의 ID를 사용할 수 없는가?

**각 팀 의견:**
```
Orchestrator Team:
현재 구조에서 X-MCPHub-User-Id 헤더는 Orchestrator가 JWT에서 추출한 kauth_user_id를 
Agent에게 전달하는 용도로 사용됩니다.

보안 고려사항:
1. Orchestrator → Agent: 헤더 위변조 가능성 존재
   - 대안: Agent가 MCPHub API Key 기반 인증, Orchestrator 신뢰 체인 형성
   - 현재: Agent는 고정 MCP_HUB_TOKEN 사용, MCPHub가 allowedServers로 제한

2. 외부 사용자가 직접 Agent 호출 시:
   - Agent URL이 외부 노출되면 X-MCPHub-User-Id 위변조 가능
   - 대안: Agent를 내부 네트워크에만 노출, Orchestrator만 접근 가능하게 설정

3. 권장 개선:
   - Orchestrator → Agent 구간에 내부 서명 토큰 추가 검토
   - MCPHub allowedServers 화이트리스트 강화

Agent Team:
- Agent 엔드포인트는 외부에 노출하지 않고 Orchestrator만 접근 가능하도록 제한 권장
- Orchestrator→Agent 호출에 K-Auth JWT 전달 or 내부 HMAC 서명 헤더 추가 검토
- X-MCPHub-User-Id 로그 부분 마스킹 권장

MCPHub Team:
✅ 위변조 방지 구현 완료!
- 구현 위치: apps/backend/src/middlewares/mcpAuth.middleware.ts
- 보안 검증: 관리자(isAdmin=true) 또는 자신의 K-Auth ID인 경우만 허용
- 위변조 시도 시: 경고 로그 + 자신의 토큰으로 fallback
```

### 5-3. 전체 E2E 아키텍처 문서 작성

아래 섹션을 **각 팀이 함께 작성**해주세요.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        K-Jarvis E2E Architecture                        │
└─────────────────────────────────────────────────────────────────────────┘

[사용자]
    │
    ▼
┌─────────────┐     SSO Login      ┌─────────────┐
│   K-Auth    │◄──────────────────►│   MCPHub    │
│  (OAuth)    │                    │  (MCP관리)   │
│  Port:4002  │                    │  Port:5173  │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │ SSO Login                        │ Token Storage
       ▼                                  │
┌─────────────┐                           │
│Orchestrator │                           │
│  (AI Hub)   │◄──────────────────────────┘
│  Port:4000  │     X-MCPHub-User-Id
└──────┬──────┘
       │
       │ A2A Protocol + X-MCPHub-User-Id
       ▼
┌─────────────┐
│   Agents    │───────────────────►┌─────────────┐
│ (Jira/Git/  │  X-MCPHub-User-Id  │   MCPHub    │
│ Confluence) │                    │   (API)     │
└─────────────┘                    │  Port:3000  │
                                   └──────┬──────┘
                                          │
                                          │ Token Lookup
                                          ▼
                                   ┌─────────────┐
                                   │  External   │
                                   │   APIs      │
                                   │ (Jira/Git)  │
                                   └─────────────┘
```

**각 팀 담당 영역 상세 설명:**

#### K-Auth (Orchestrator Team 담당)
```
역할: 중앙 OAuth 2.0 Identity Provider (SSO)
DB: PostgreSQL (k_auth), 독립 운영
Port: 4002

API 엔드포인트:
- GET  /oauth/authorize     - OAuth 인증 시작
- POST /oauth/token         - 토큰 발급/갱신
- GET  /oauth/userinfo      - 사용자 정보 조회
- GET  /login               - 로그인 페이지
- GET  /register            - 회원가입 페이지

발급 토큰:
- Access Token: JWT (HS256, 24시간 만료)
- Refresh Token: Opaque (7일 만료)
- Claims: sub(UUID), username, email, is_admin

OAuth Clients 등록:
- MCPHub: redirect_uri=http://localhost:5173/auth/callback
- Orchestrator: redirect_uri=http://localhost:4001/auth/kauth/callback
```

#### Orchestrator (Orchestrator Team 담당)
```
역할: AI 에이전트 라우팅 및 대화 관리 허브
DB: PostgreSQL (agent_orchestrator), 독립 운영
Port: Frontend 4000, Backend 4001

API 엔드포인트:
- POST /api/chat              - 메시지 전송 (Agent 라우팅)
- POST /api/chat/stream       - 스트리밍 응답
- GET  /api/agents            - 에이전트 목록
- GET  /api/conversations     - 대화 이력
- GET  /auth/kauth            - K-Auth SSO 시작
- GET  /auth/kauth/callback   - K-Auth 콜백

JWT 구조 (Orchestrator 자체 발급):
{
  "sub": "username",
  "user_id": "uuid",
  "is_admin": false,
  "kauth_user_id": "k-auth-sub-uuid",  // Option C 핵심!
  "exp": 1234567890
}

Agent 호출 방식:
- POST {agent_url}/tasks/send
- Headers: 
  - Content-Type: application/json
  - X-MCPHub-User-Id: {kauth_user_id}  // Option C
- Body: A2A Message 형식
```

#### Agents (Agent Team 담당)
```
역할: 도메인별 AI Agent (Confluence/Jira/GitHub)
DB: 없음 (Stateless)
Port: Confluence 5010, Jira 5011, GitHub 5012

지원 프로토콜:
- A2A Protocol (/.well-known/agent.json, /tasks/send)
- MCP Protocol (MCPHub 경유)

MCPHub 연동 방식:
- Agent 전용 MCPHub Key 사용 (MCP_HUB_TOKEN 환경변수)
- X-MCPHub-User-Id 헤더를 MCPHub에 전달

헤더 처리:
- 수신: X-MCPHub-User-Id (Orchestrator에서)
- 전달: Authorization + X-MCPHub-User-Id (MCPHub로)
```

#### MCPHub (MCPHub Team 담당)
```
역할:
- MCP 서버 통합 관리 플랫폼
- 사용자별 서비스 토큰 저장/조회
- MCP 프로토콜 프록시 (tools/list, tools/call)

DB: PostgreSQL (mcphub)
Port: Backend 3000, Frontend 5173
주요 테이블: users, mcphub_keys, user_server_subscriptions, mcp_servers

Token 저장 방식:
- user_server_subscriptions.settings.envVariables (JSONB)
- 서버별로 분리 저장
- 예: {"GITHUB_TOKEN": "ghp_xxx", "ATLASSIAN_JIRA_TOKEN": "xxx"}

X-MCPHub-User-Id 처리 로직:
1. 헤더에서 K-Auth user_id 추출
2. 보안 검증 (관리자 또는 본인만 허용) ✅
3. user_server_subscriptions에서 서비스 토큰 조회
4. MCP 서버에 토큰 적용하여 API 호출
```

---

## 📅 마감일

**각 팀 응답 마감: 2024-12-13 (금) 18:00**

완료 후 이 문서를 업데이트하거나, 별도 응답 문서를 작성해주세요.

---

## ✅ 진행 상태

| 팀 | 1번 DB | 2번 체이닝 | 3번 코드 | 4번 문서 | 5번 보안 |
|----|:------:|:--------:|:------:|:------:|:------:|
| Orchestrator | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| Agent | ✅ | ✅ | ✅ | ✅ | ✅ |
| MCPHub | ✅ | - | ✅ | ⚠️ | ✅ |

**범례**: ✅ 완료 | ⚠️ 일부 미작성 (문서) | - 해당 없음

---

**문의사항은 문서 공유 시스템(http://localhost:8888)을 통해 공유해주세요.**

