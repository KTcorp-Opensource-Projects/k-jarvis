# 🚨 전체 팀 공지 - Docker 기반 통합 개발 환경 전환

**작성일**: 2025-12-19  
**작성자**: MCPHub Team  
**대상**: Agent Team, Orchestrator Team, MCPHub Team  
**긴급도**: 높음

---

## ⚠️ 중요: 플랫폼 환경 차이

### 로컬 vs 배포 환경

| 환경 | 플랫폼 | 설명 |
|------|--------|------|
| **로컬 개발** | `linux/arm64` | Apple Silicon Mac (M1/M2/M3) |
| **Azure 배포** | `linux/amd64` | Azure Container Apps |

### Docker 이미지 빌드 시 주의사항

```bash
# ❌ 잘못된 방법 - 플랫폼 미지정
docker build -t myapp .

# ✅ 로컬 테스트용 (ARM64)
docker build --platform linux/arm64 -t myapp:local .

# ✅ Azure 배포용 (AMD64)
docker build --platform linux/amd64 -t myapp:prod .

# ✅ 멀티 플랫폼 빌드 (권장)
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest .
```

### Dockerfile 권장 사항

```dockerfile
# 멀티 플랫폼 지원을 위해 공식 이미지 사용
FROM node:20-alpine  # ✅ 멀티 플랫폼 지원
# FROM node:20       # ✅ 멀티 플랫폼 지원
# FROM ubuntu:22.04  # ✅ 멀티 플랫폼 지원
```

### MCPHub 현재 설정

MCPHub는 다음과 같이 플랫폼별 Dockerfile을 분리하여 관리합니다:

```
apps/backend/
├── Dockerfile.local      # 로컬 개발용 (ARM64 호환)
├── Dockerfile.sbox       # 샌드박스용 (AMD64)
└── Dockerfile.production # 프로덕션용 (AMD64)
```

---

## 📌 배경

현재 각 팀이 **로컬 환경에서 독립적으로 개발/테스트**를 진행하고 있어 다음과 같은 문제가 발생하고 있습니다:

### 현재 문제점

1. **통합 테스트 어려움**
   - 다른 팀 서비스 테스트 시 "서버 기동해주세요" 요청 필요
   - 포트 충돌, 프로세스 관리 복잡
   - 환경 불일치로 인한 버그 재현 어려움

2. **협업 비효율**
   - 각 팀 로컬 환경이 달라 동일한 테스트 결과 보장 불가
   - DB 스키마 불일치 가능성
   - 서비스 간 연동 테스트 시 수동 조율 필요

3. **배포 환경과 괴리**
   - 로컬 환경 ≠ 실제 배포 환경 (Azure Container Apps)
   - Scale-out 테스트 불가

---

## ✅ 결정 사항

**2025-12-19부터 모든 팀은 Docker 기반 개발 환경으로 전환합니다.**

### 전환 범위

| 서비스 | Docker 이미지 | 포트 |
|--------|--------------|------|
| PostgreSQL | postgres:15 | 5432 |
| Redis | redis:7-alpine | 6379 |
| MCPHub Backend | mcphub-backend | 3000 |
| MCPHub Frontend | mcphub-frontend | 5173 |
| Agent Service | (Agent팀 제공) | TBD |
| Orchestrator Service | (Orchestrator팀 제공) | TBD |
| K-Auth Service | (해당 시) | TBD |

---

## 📋 각 팀 액션 아이템

### 🔵 Agent Team

1. **Dockerfile 제공**
   - Agent 서비스용 Dockerfile 작성
   - 필요한 환경변수 목록 문서화

2. **Docker Compose 설정 추가**
   - `docker-compose.agent.yml` 또는 통합 compose에 추가

3. **의존성 명시**
   - MCPHub, Redis 등 의존 서비스 명시

### 🟢 Orchestrator Team

1. **Dockerfile 제공**
   - Orchestrator 서비스용 Dockerfile 작성
   - 필요한 환경변수 목록 문서화

2. **Docker Compose 설정 추가**
   - `docker-compose.orchestrator.yml` 또는 통합 compose에 추가

3. **의존성 명시**
   - Agent, MCPHub 등 의존 서비스 명시

### 🟡 MCPHub Team (내부)

1. ✅ Docker Compose 통합 환경 구성
2. ✅ PostgreSQL, Redis 포함
3. ⏳ 각 팀 서비스 통합
4. ⏳ 스키마 마이그레이션 검증

---

## 🛠️ 통합 Docker Compose 구조 (예정)

```yaml
# docker-compose.integration.yml

version: '3.8'

services:
  # === Infrastructure ===
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: mcphub
      POSTGRES_PASSWORD: mcphub123
      POSTGRES_DB: mcphub
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d  # 스키마 초기화
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mcphub"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # === MCPHub ===
  mcphub-backend:
    build:
      context: ./apps/backend
      dockerfile: Dockerfile.local
    environment:
      - DATABASE_URL=postgresql://mcphub:mcphub123@postgres:5432/mcphub
      - REDIS_URL=redis://redis:6379
      - NODE_ENV=development
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  mcphub-frontend:
    build:
      context: ./apps/frontend
      dockerfile: Dockerfile.local
    environment:
      - VITE_API_BASE_URL=http://mcphub-backend:3000
    ports:
      - "5173:5173"
    depends_on:
      - mcphub-backend

  # === Agent Service (Agent팀 제공 필요) ===
  # agent-service:
  #   build:
  #     context: ../Confluence-AI-Agent
  #     dockerfile: Dockerfile
  #   environment:
  #     - MCPHUB_URL=http://mcphub-backend:3000
  #   ports:
  #     - "8080:8080"
  #   depends_on:
  #     - mcphub-backend

  # === Orchestrator Service (Orchestrator팀 제공 필요) ===
  # orchestrator-service:
  #   build:
  #     context: ../Agent-orchestrator
  #     dockerfile: Dockerfile
  #   environment:
  #     - AGENT_URL=http://agent-service:8080
  #     - MCPHUB_URL=http://mcphub-backend:3000
  #   ports:
  #     - "9000:9000"
  #   depends_on:
  #     - agent-service

volumes:
  postgres_data:
```

---

## 📊 스키마 검증 필요 항목

각 팀은 다음 테이블/스키마가 정상적으로 생성되는지 확인해주세요:

### MCPHub DB 스키마

```sql
-- 핵심 테이블
users                    -- 사용자
mcphub_keys              -- API 키
mcp_servers              -- MCP 서버 정보
mcp_server_env_vars      -- 서버 환경변수
user_server_subscriptions -- 사용자 구독
activity_logs            -- 활동 로그
```

### 확인 방법

```bash
# Docker 환경에서 스키마 확인
docker exec -it mcphub-postgres psql -U mcphub -d mcphub -c "\dt"
```

---

## 🚀 실행 방법 (예정)

```bash
# 1. 전체 환경 시작
docker-compose -f docker-compose.integration.yml up -d

# 2. 로그 모니터링
docker-compose -f docker-compose.integration.yml logs -f

# 3. 헬스 체크
curl http://localhost:3000/api/servers  # MCPHub
curl http://localhost:8080/health       # Agent (예정)
curl http://localhost:9000/health       # Orchestrator (예정)

# 4. 환경 종료
docker-compose -f docker-compose.integration.yml down
```

---

## 📅 타임라인

| 일정 | 내용 |
|------|------|
| 2025-12-19 (오늘) | 공지 및 각 팀 Dockerfile 준비 시작 |
| 2025-12-20 | 각 팀 Dockerfile 제출 |
| 2025-12-21 | 통합 Docker Compose 완성 |
| 2025-12-22 | 통합 테스트 시작 |

---

## 📝 각 팀 제출 양식

다음 내용을 포함한 문서를 `docs/` 폴더에 작성해주세요:

```markdown
# {팀명} Docker 환경 설정

## Dockerfile 위치
- `path/to/Dockerfile`

## 환경변수
| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| XXX | ... | ... |

## 의존 서비스
- [ ] PostgreSQL
- [ ] Redis
- [ ] MCPHub
- [ ] 기타

## 포트
- 메인 서비스: XXXX
- 기타: ...

## 헬스체크 엔드포인트
- GET /health
```

---

## ❓ FAQ

**Q: 기존 로컬 개발은 불가능한가요?**
A: 개인 개발은 로컬에서 가능하나, **팀 간 통합 테스트는 반드시 Docker 환경**에서 진행합니다.

**Q: Docker Desktop 설치가 필수인가요?**
A: 네, 모든 팀원은 Docker Desktop (또는 Rancher Desktop) 설치가 필요합니다.

**Q: DB 데이터는 어떻게 관리하나요?**
A: Docker Volume으로 관리하며, 테스트 데이터 초기화 스크립트를 제공합니다.

---

## 📞 문의

- Slack: #k-jarvis-integration
- MCPHub: #mcphub-dev

---

**협조 부탁드립니다. 🙏**

MCPHub Team

