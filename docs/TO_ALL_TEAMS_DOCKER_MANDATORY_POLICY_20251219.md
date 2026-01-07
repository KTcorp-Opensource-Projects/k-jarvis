# 🚨 전체 팀 필수 공지 - Docker 기반 개발/테스트 정책

**작성일**: 2025-12-19  
**작성자**: Orchestrator Team (K-Jarvis 프로젝트 총괄)  
**대상**: Agent Team, K-ARC Team, Orchestrator Team (전 팀)  
**긴급도**: 🔴 최상 (즉시 적용)

---

## ⚠️ 핵심 결정 사항

### Docker 기반 개발/테스트 **필수화**

**2025-12-19부터 K-Jarvis 생태계의 모든 서비스는 반드시 Docker 기반으로 실행합니다.**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   🚫 더 이상 허용되지 않는 방식:                                         │
│      - brew services start postgresql                                   │
│      - brew services start redis                                        │
│      - 로컬 Python/Node 직접 실행 (테스트 용도)                          │
│                                                                         │
│   ✅ 필수 방식:                                                          │
│      - docker-compose up -d                                             │
│      - 모든 서비스는 Docker 컨테이너로 실행                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 적용 범위

### 대상 서비스

| 서비스 | 담당 팀 | Docker 이미지 |
|--------|---------|---------------|
| **K-Jarvis Orchestrator** (Backend/Frontend) | Orchestrator Team | agent-orchestrator-* |
| **K-Auth** (OAuth 2.0 Server) | Orchestrator Team | k-auth |
| **AI Agents** (Confluence, Jira, GitHub, Sample) | Agent Team | confluence-agent, etc. |
| **K-ARC (MCPHub)** (Backend/Frontend) | K-ARC Team | mcphub-* |
| **PostgreSQL** | 공용 | pgvector/pgvector:pg16 |
| **Redis** | 공용 | redis:7-alpine |

### 적용 상황

| 상황 | Docker 필수 |
|------|-------------|
| 로컬 개발 | ✅ 필수 |
| 단위 테스트 | ✅ 필수 |
| 통합 테스트 | ✅ 필수 |
| E2E 테스트 | ✅ 필수 |
| 팀 간 연동 테스트 | ✅ 필수 |
| 데모/시연 | ✅ 필수 |

---

## 🎯 정책 도입 이유

### 1. 환경 불일치 해결

```
❌ 이전: "내 환경에서는 되는데요..."
   - PostgreSQL 버전 불일치 (14 vs 15 vs 17)
   - Node.js/Python 버전 불일치
   - 환경변수 설정 누락
   
✅ 이후: 동일한 Docker 이미지 = 동일한 환경
```

### 2. 통합 테스트 용이성

```
❌ 이전: "Agent 팀, 서버 좀 기동해주세요"
   - 수동 조율 필요
   - 포트 충돌
   - 서비스 의존성 관리 어려움
   
✅ 이후: docker-compose up -d 한 번으로 전체 환경 구동
```

### 3. 배포 환경과 일관성

```
❌ 이전: 로컬 ≠ 스테이징 ≠ 프로덕션
   - "로컬에서는 됐는데 배포하니까 안 돼요"
   
✅ 이후: 로컬 Docker ≈ Azure Container Apps
   - 동일한 이미지, 동일한 동작
```

---

## 🛠️ 각 팀 필수 조치

### 1. Dockerfile 필수 구비

모든 팀은 자신의 서비스에 대해 **Dockerfile**을 필수로 제공해야 합니다.

```
프로젝트/
├── Dockerfile           # 필수!
├── .dockerignore        # 권장
└── docker-compose.yml   # 팀별 독립 테스트용 (선택)
```

### 2. 환경변수 문서화

Docker 환경에서 필요한 환경변수를 문서화하세요.

```markdown
## 환경변수

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| DATABASE_URL | PostgreSQL 연결 | - | ✅ |
| REDIS_URL | Redis 연결 | - | ✅ |
```

### 3. 헬스체크 엔드포인트 필수

모든 서비스는 `/health` 엔드포인트를 제공해야 합니다.

```bash
curl http://localhost:PORT/health
# 응답: {"status": "healthy", ...}
```

---

## 📂 통합 Docker Compose (MCPHub 주관)

MCPHub Team이 전체 서비스 통합 Docker Compose를 관리합니다.

### 위치

```
mcphubproject/mcphub/docker-compose.integration.yml
```

### 포함 서비스

```yaml
services:
  # Infrastructure
  postgres:     # pgvector/pgvector:pg16
  redis:        # redis:7-alpine
  
  # K-ARC (MCPHub)
  mcphub-backend:
  mcphub-frontend:
  
  # Orchestrator Team
  kauth:
  orchestrator-backend:
  orchestrator-frontend:
  
  # Agent Team
  confluence-agent:
  jira-agent:
  github-agent:
  sample-agent:
```

---

## 🚀 사용 방법

### 전체 환경 시작

```bash
# MCPHub 프로젝트에서
cd mcphubproject/mcphub
docker-compose -f docker-compose.integration.yml up -d
```

### 서비스 상태 확인

```bash
docker-compose ps
```

### 로그 모니터링

```bash
docker-compose logs -f [서비스명]
```

### 환경 종료

```bash
docker-compose down
```

### 데이터 초기화 (필요시)

```bash
docker-compose down -v  # 볼륨까지 삭제
docker-compose up -d    # 새로 시작
```

---

## ⚠️ 주의사항

### 1. 로컬 서비스 충돌 방지

Docker 환경 사용 전 로컬 서비스를 중지하세요:

```bash
# 반드시 중지
brew services stop postgresql@17
brew services stop postgresql@15
brew services stop postgresql@14
brew services stop redis
```

### 2. 포트 확인

| 서비스 | 포트 |
|--------|------|
| PostgreSQL | 5432 |
| Redis | 6379 |
| K-Auth | 4002 |
| Orchestrator Backend | 4001 |
| Orchestrator Frontend | 4000 |
| MCPHub Backend | 3000 |
| MCPHub Frontend | 5173 |
| Agents | 5010-5020 |

### 3. Docker 내부 호스트명

```yaml
# Docker 내부에서는 컨테이너 이름 사용
DATABASE_URL=postgresql://user:pass@postgres:5432/dbname
REDIS_URL=redis://redis:6379

# 로컬 브라우저에서는 localhost 사용
http://localhost:4000  # Frontend 접속
```

---

## 📊 정책 준수 체크리스트

각 팀은 다음 체크리스트를 완료해야 합니다:

### Orchestrator Team ✅

- [x] K-Auth Dockerfile 작성
- [x] Orchestrator Backend Dockerfile 작성
- [x] Orchestrator Frontend Dockerfile 작성
- [x] 환경변수 문서화
- [x] 헬스체크 엔드포인트 확인

### Agent Team

- [ ] Confluence Agent Dockerfile 작성
- [ ] Jira Agent Dockerfile 작성
- [ ] GitHub Agent Dockerfile 작성
- [ ] Sample Agent Dockerfile 작성
- [ ] 환경변수 문서화
- [ ] 헬스체크 엔드포인트 확인

### K-ARC Team

- [ ] MCPHub Backend Dockerfile 작성
- [ ] MCPHub Frontend Dockerfile 작성
- [ ] 환경변수 문서화
- [ ] 헬스체크 엔드포인트 확인
- [ ] 통합 Docker Compose 완성

---

## 📅 적용 일정

| 일정 | 내용 |
|------|------|
| **2025-12-19 (오늘)** | 정책 공지, 각 팀 Dockerfile 준비 시작 |
| **2025-12-20** | 각 팀 Dockerfile 제출 완료 |
| **2025-12-21** | 통합 Docker Compose 완성 |
| **2025-12-22** | 전체 통합 테스트 시작 |

---

## 📞 문의

- **통합 환경 관련**: K-ARC Team (#mcphub-dev)
- **정책 관련**: Orchestrator Team (#k-jarvis-dev)
- **긴급 문의**: 정치훈

---

## 🔔 중요

**이 정책은 즉시 적용됩니다.**

앞으로 모든 개발, 테스트, 데모는 Docker 환경에서 진행해야 합니다.
로컬 환경에서 직접 서비스를 실행하는 방식은 더 이상 지원되지 않습니다.

---

**Orchestrator Team | 2025-12-19**

