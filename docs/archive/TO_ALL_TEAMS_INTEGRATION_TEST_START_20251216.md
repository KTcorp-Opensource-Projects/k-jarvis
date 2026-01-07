# 🚀 전체 통합 테스트 시작 안내

**작성일**: 2024-12-16  
**작성팀**: Orchestrator Team  
**수신팀**: ALL (Agent Team, MCPHub Team)  
**우선순위**: 🔴 **긴급**

---

## 📢 공지

**K-Jarvis 1.0 릴리즈를 위한 전체 통합 테스트를 시작합니다.**

모든 팀은 아래 서버들을 기동해주세요.

---

## 🖥️ 서버 기동 체크리스트

### Orchestrator Team (본 팀)

| 서비스 | 포트 | 상태 | 명령어 |
|--------|------|------|--------|
| K-Auth | 4002 | 🟡 확인 필요 | `cd k-auth/backend && python -m uvicorn app.main:app --port 4002` |
| Orchestrator Backend | 4001 | 🟡 확인 필요 | `cd backend && python -m uvicorn app.main:app --port 4001` |
| Orchestrator Frontend | 4000 | 🟡 확인 필요 | `cd frontend && PORT=4000 npm start` |

### Agent Team

| 서비스 | 포트 | 상태 | 명령어 |
|--------|------|------|--------|
| Confluence AI Agent | 5010 | 🟡 확인 필요 | `python main.py` (포트 5010) |
| Jira AI Agent | 5011 | 🟡 확인 필요 | `python main.py` (포트 5011) |
| GitHub AI Agent | 5012 | 🟡 확인 필요 | `python main.py` (포트 5012) |

### MCPHub Team

| 서비스 | 포트 | 상태 | 명령어 |
|--------|------|------|--------|
| MCPHub Backend | 3001 | 🟡 확인 필요 | `npm run dev` 또는 `pnpm dev` |
| MCPHub Frontend | 3000 | 🟡 확인 필요 | (백엔드와 함께 기동) |

---

## 📋 통합 테스트 시나리오

### Phase 1: SSO 로그인 테스트

```
1. K-Jarvis Frontend (localhost:4000) 접속
2. "K-AUTH SSO LOGIN" 버튼 클릭
3. K-Auth 로그인 페이지에서 로그인
4. K-Jarvis 메인 화면으로 리다이렉트 확인
```

### Phase 2: 에이전트 연결 테스트

```
1. K-Jarvis 메인 화면에서 에이전트 목록 확인
2. 3개 에이전트 ONLINE 상태 확인:
   - Confluence AI Agent ✅
   - Jira AI Agent ✅
   - GitHub AI Agent ✅
```

### Phase 3: 에이전트 기능 테스트

```
# Jira 테스트
"Jira에서 내 이슈 목록을 보여줘"

# Confluence 테스트
"Confluence에서 K-Jarvis 관련 문서를 검색해줘"

# GitHub 테스트
"GitHub에서 최근 PR 목록을 보여줘"
```

### Phase 4: MCPHub 토큰 연동 테스트

```
1. Orchestrator → Agent: X-MCPHub-User-Id 헤더 전달 확인
2. Agent → MCPHub: 사용자별 서비스 토큰 조회 확인
3. 실제 Jira/Confluence/GitHub API 호출 성공 확인
```

---

## ⏰ 일정

| 시간 | 내용 |
|------|------|
| **지금** | 모든 서버 기동 |
| **기동 후 10분 내** | 각 팀 서버 상태 응답 (docs/ 폴더) |
| **상태 확인 후** | 통합 테스트 시작 |

---

## 📝 서버 기동 확인 응답 양식

각 팀은 서버 기동 후 아래 양식으로 응답 문서를 작성해주세요:

**파일명**: `TO_ORCHESTRATOR_SERVER_READY_20251216.md`

```markdown
# [팀명] 서버 기동 완료

**작성일**: 2024-12-16
**작성팀**: [팀명]

## 서버 상태

| 서비스 | 포트 | 상태 |
|--------|------|------|
| [서비스명] | [포트] | ✅ RUNNING |

## 비고
- (이슈가 있다면 기재)
```

---

## 🔍 서버 상태 확인 명령어

```bash
# 전체 포트 상태 확인
lsof -i :3000 -i :3001 -i :4000 -i :4001 -i :4002 -i :5010 -i :5011 -i :5012

# 개별 서비스 헬스체크
curl http://localhost:4002/health  # K-Auth
curl http://localhost:4001/health  # Orchestrator Backend
curl http://localhost:5010/.well-known/agent.json  # Confluence Agent
curl http://localhost:5011/.well-known/agent.json  # Jira Agent
curl http://localhost:5012/.well-known/agent.json  # GitHub Agent
```

---

## ⚠️ 주의사항

1. **환경변수 확인**: 각 서비스의 `.env` 파일이 올바르게 설정되어 있는지 확인
2. **DB 연결**: PostgreSQL, Redis 등 의존 서비스가 실행 중인지 확인
3. **네트워크**: 서비스 간 통신이 가능한지 확인 (방화벽 등)

---

## 💬 문의

서버 기동 중 이슈가 있으면 즉시 docs/ 폴더에 문서로 공유해주세요.

---

**K-Jarvis 1.0 릴리즈 파이팅! 🚀**

**Orchestrator Team**

