# 🔗 전체 팀 공지 - 통합 Docker 네트워크 설정 가이드

**작성일**: 2025-12-19  
**작성자**: Orchestrator Team  
**대상**: Agent Team, K-ARC Team, Orchestrator Team  
**긴급도**: 🔴 높음 (즉시 적용 필요)

---

## ⚠️ 현재 문제점

### 네트워크 분리 상태

현재 각 팀의 서비스들이 **별도의 Docker 네트워크**에서 실행되고 있어 **서로 통신이 불가능**합니다.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        현재 문제 상황                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────┐    ┌──────────────────────────┐          │
│  │ agent-orchestrator_default│    │ mcphub_kjarvis-network  │          │
│  │                          │    │                          │          │
│  │  • kjarvis-kauth         │ ❌ │  • kjarvis-postgres      │          │
│  │  • kjarvis-orchestrator  │←──→│  • kjarvis-redis         │          │
│  │    -backend              │통신 │  • kjarvis-mcphub-backend│          │
│  │  • kjarvis-orchestrator  │불가 │  • kjarvis-mcphub-frontend│         │
│  │    -frontend             │    │                          │          │
│  └──────────────────────────┘    └──────────────────────────┘          │
│                                                                         │
│  서로 다른 네트워크 → 컨테이너명으로 접근 불가!                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 현재 실행 상태

| 컨테이너 | 네트워크 | 포트 |
|----------|----------|------|
| kjarvis-postgres | `mcphub_kjarvis-network` | 5433:5432 |
| kjarvis-redis | `mcphub_kjarvis-network` | 6380:6379 |
| kjarvis-mcphub-backend | `mcphub_kjarvis-network` | 3000 |
| kjarvis-mcphub-frontend | `mcphub_kjarvis-network` | 5173 |
| kjarvis-kauth | `agent-orchestrator_default` | 4002 |
| kjarvis-orchestrator-backend | `agent-orchestrator_default` | 4001 |
| kjarvis-orchestrator-frontend | `agent-orchestrator_default` | 4000 |

---

## ✅ 해결 방안: 통합 Docker 네트워크

### 목표 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     kjarvis-network (통합 네트워크)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Infrastructure                              │   │
│  │  ┌─────────────────┐       ┌─────────────────┐                  │   │
│  │  │ kjarvis-postgres│       │  kjarvis-redis  │                  │   │
│  │  │     :5432       │       │     :6379       │                  │   │
│  │  └────────┬────────┘       └────────┬────────┘                  │   │
│  └───────────┼─────────────────────────┼───────────────────────────┘   │
│              │                         │                               │
│   ┌──────────┼─────────────────────────┼──────────────────────┐        │
│   │          ▼                         ▼                      │        │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │        │
│   │  │  K-Auth     │  │ Orchestrator│  │ MCPHub Backend  │   │        │
│   │  │   :4002     │  │   :4001     │  │     :3000       │   │        │
│   │  └─────────────┘  └──────┬──────┘  └────────┬────────┘   │        │
│   │                          │                  │             │        │
│   │                          ▼                  ▼             │        │
│   │                   ┌─────────────┐  ┌─────────────────┐   │        │
│   │                   │ Orch Frontend│ │MCPHub Frontend  │   │        │
│   │                   │   :4000     │  │    :5173        │   │        │
│   │                   └─────────────┘  └─────────────────┘   │        │
│   └───────────────────────────────────────────────────────────┘        │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                        AI Agents                                │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │   │
│   │  │Confluence│ │  Jira    │ │  GitHub  │ │  Sample  │           │   │
│   │  │  :5010   │ │  :5011   │ │  :5012   │ │  :5020   │           │   │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 설정 방법

### Step 1: 외부 공용 네트워크 생성

```bash
# 공용 네트워크 생성 (한 번만 실행)
docker network create kjarvis-network
```

### Step 2: 각 팀 Docker Compose 수정

#### 네트워크 설정 추가 (모든 팀 공통)

```yaml
# docker-compose.yml 맨 아래에 추가
networks:
  kjarvis-network:
    external: true
```

#### 서비스에 네트워크 연결

```yaml
services:
  your-service:
    # ... 기존 설정 ...
    networks:
      - kjarvis-network
```

---

## 📋 팀별 설정 가이드

### K-ARC Team (MCPHub) - 통합 관리 주체

```yaml
# docker-compose.integration.yml

version: '3.8'

services:
  # === Infrastructure (공용) ===
  postgres:
    image: pgvector/pgvector:pg16
    container_name: kjarvis-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
    ports:
      - "5432:5432"  # 표준 포트 사용
    networks:
      - kjarvis-network
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: kjarvis-redis
    ports:
      - "6379:6379"  # 표준 포트 사용
    networks:
      - kjarvis-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # === MCPHub Services ===
  mcphub-backend:
    container_name: kjarvis-mcphub-backend
    # ... 기존 설정 ...
    networks:
      - kjarvis-network
    environment:
      - DATABASE_URL=postgresql://postgres:postgres123@kjarvis-postgres:5432/mcphub
      - REDIS_URL=redis://kjarvis-redis:6379

  mcphub-frontend:
    container_name: kjarvis-mcphub-frontend
    # ... 기존 설정 ...
    networks:
      - kjarvis-network

networks:
  kjarvis-network:
    external: true

volumes:
  postgres_data:
```

### Orchestrator Team

```yaml
# docker-compose.yml

version: '3.8'

services:
  kauth:
    container_name: kjarvis-kauth
    build:
      context: ../k-auth/backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres123@kjarvis-postgres:5432/k_auth
      - REDIS_URL=redis://kjarvis-redis:6379/1
    ports:
      - "4002:4002"
    networks:
      - kjarvis-network
    depends_on:
      - postgres  # 또는 external dependency 체크

  orchestrator-backend:
    container_name: kjarvis-orchestrator-backend
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres123@kjarvis-postgres:5432/orchestrator
      - REDIS_URL=redis://kjarvis-redis:6379/0
      - KAUTH_URL=http://kjarvis-kauth:4002
      - MCPHUB_URL=http://kjarvis-mcphub-backend:3000
    ports:
      - "4001:4001"
    networks:
      - kjarvis-network

  orchestrator-frontend:
    container_name: kjarvis-orchestrator-frontend
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "4000:80"
    networks:
      - kjarvis-network

networks:
  kjarvis-network:
    external: true
```

### Agent Team

```yaml
# docker-compose.yml

version: '3.8'

services:
  confluence-agent:
    container_name: kjarvis-confluence-agent
    # ... 기존 설정 ...
    environment:
      - MCPHUB_URL=http://kjarvis-mcphub-backend:3000
    networks:
      - kjarvis-network

  jira-agent:
    container_name: kjarvis-jira-agent
    # ... 기존 설정 ...
    networks:
      - kjarvis-network

  github-agent:
    container_name: kjarvis-github-agent
    # ... 기존 설정 ...
    networks:
      - kjarvis-network

  sample-agent:
    container_name: kjarvis-sample-agent
    # ... 기존 설정 ...
    networks:
      - kjarvis-network

networks:
  kjarvis-network:
    external: true
```

---

## 🔗 서비스 간 통신 설정

### 컨테이너 내부 호스트명 (Docker 네트워크 내)

| 서비스 | 호스트명 | 포트 |
|--------|----------|------|
| PostgreSQL | `kjarvis-postgres` | 5432 |
| Redis | `kjarvis-redis` | 6379 |
| K-Auth | `kjarvis-kauth` | 4002 |
| Orchestrator Backend | `kjarvis-orchestrator-backend` | 4001 |
| MCPHub Backend | `kjarvis-mcphub-backend` | 3000 |
| Confluence Agent | `kjarvis-confluence-agent` | 5010 |
| Jira Agent | `kjarvis-jira-agent` | 5011 |
| GitHub Agent | `kjarvis-github-agent` | 5012 |
| Sample Agent | `kjarvis-sample-agent` | 5020 |

### 환경변수 설정 예시

```bash
# Orchestrator Backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@kjarvis-postgres:5432/orchestrator
REDIS_URL=redis://kjarvis-redis:6379/0
KAUTH_URL=http://kjarvis-kauth:4002
MCPHUB_URL=http://kjarvis-mcphub-backend:3000

# K-Auth
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@kjarvis-postgres:5432/k_auth
REDIS_URL=redis://kjarvis-redis:6379/1

# MCPHub Backend
DATABASE_URL=postgresql://postgres:postgres123@kjarvis-postgres:5432/mcphub
REDIS_URL=redis://kjarvis-redis:6379/2

# Agents
MCPHUB_URL=http://kjarvis-mcphub-backend:3000
```

---

## 🚀 실행 순서

### 전체 환경 시작 순서

```bash
# 1. 공용 네트워크 생성 (최초 1회)
docker network create kjarvis-network

# 2. Infrastructure 시작 (MCPHub 팀 관리)
cd mcphubproject/mcphub
docker-compose -f docker-compose.integration.yml up -d postgres redis

# 3. DB 초기화 대기 (약 10초)
sleep 10

# 4. 각 팀 서비스 시작
# MCPHub
docker-compose -f docker-compose.integration.yml up -d mcphub-backend mcphub-frontend

# Orchestrator
cd Agent-orchestrator
docker-compose up -d

# Agent
cd Confluence-AI-Agent
docker-compose up -d
```

### 연결 확인

```bash
# 네트워크 내 컨테이너 확인
docker network inspect kjarvis-network

# 서비스 간 통신 테스트
docker exec kjarvis-orchestrator-backend curl http://kjarvis-mcphub-backend:3000/api/health
docker exec kjarvis-orchestrator-backend curl http://kjarvis-kauth:4002/health
```

---

## ⚠️ 주의사항

### 1. 포트 표준화

**모든 팀은 표준 포트를 사용합니다** (로컬 충돌 방지를 위한 변경 포트 사용 X)

| 서비스 | 표준 포트 |
|--------|----------|
| PostgreSQL | 5432 |
| Redis | 6379 |

로컬 서비스와 충돌 시 → 로컬 서비스 중지 후 Docker 사용

### 2. 컨테이너 이름 규칙

모든 컨테이너는 `kjarvis-` 접두사 사용:
- `kjarvis-postgres`
- `kjarvis-redis`
- `kjarvis-kauth`
- `kjarvis-orchestrator-backend`
- `kjarvis-mcphub-backend`
- 등

### 3. 시작 순서 준수

```
1. PostgreSQL → 2. Redis → 3. K-Auth → 4. MCPHub → 5. Orchestrator → 6. Agents
```

---

## 📊 체크리스트

### K-ARC Team (MCPHub)
- [ ] 공용 네트워크 `kjarvis-network` 생성
- [ ] PostgreSQL/Redis를 표준 포트(5432/6379)로 변경
- [ ] docker-compose.integration.yml에 external network 설정
- [ ] DB 초기화 스크립트 (mcphub, k_auth, orchestrator DB 생성)

### Orchestrator Team
- [ ] docker-compose.yml에 external network 설정
- [ ] 환경변수를 Docker 내부 호스트명으로 변경
- [ ] Infrastructure 의존성 확인

### Agent Team
- [ ] docker-compose.yml에 external network 설정
- [ ] MCPHUB_URL을 Docker 내부 호스트명으로 변경
- [ ] 각 Agent 컨테이너명 `kjarvis-` 접두사 적용

---

## 📞 문의

- **네트워크/인프라**: K-ARC Team (#mcphub-dev)
- **통합 정책**: Orchestrator Team (#k-jarvis-dev)

---

**모든 서비스가 하나의 네트워크에서 통신해야 K-Jarvis 플랫폼이 정상 동작합니다!**

---

## 🔧 K-ARC Team 필수 작업 요청

### 1. DB 초기화 스크립트 수정 필요

현재 `scripts/init-local-db.sql`에는 `mcphub` DB만 생성됩니다.
**k_auth**, **orchestrator** 데이터베이스를 추가해야 합니다.

#### 수정 요청: init-local-db.sql 시작 부분에 추가

```sql
-- ============================================
-- 0. 전체 K-Jarvis 데이터베이스 생성
-- ============================================

-- K-Auth 데이터베이스 생성
SELECT 'CREATE DATABASE k_auth'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'k_auth')\gexec

-- Orchestrator 데이터베이스 생성
SELECT 'CREATE DATABASE orchestrator'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'orchestrator')\gexec

-- 각 DB에 확장 설치
\c k_auth
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c orchestrator
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

\c mcphub
-- 기존 mcphub 스크립트 계속...
```

### 2. Docker Compose 수정 필요

#### 현재 문제점:
- 포트: `5433:5432`, `6380:6379` → 표준 포트 불일치
- 네트워크: `external: true` 아님

#### 권장 수정:

```yaml
# docker-compose.integration.yml

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: kjarvis-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
      POSTGRES_DB: postgres  # 기본 DB
    ports:
      - "5432:5432"  # 표준 포트 사용
    # ... 나머지 동일

  redis:
    image: redis:7-alpine
    container_name: kjarvis-redis
    ports:
      - "6379:6379"  # 표준 포트 사용
    # ... 나머지 동일

networks:
  kjarvis-network:
    external: true  # 외부 네트워크로 변경
```

### 3. 로컬 서비스 충돌 해결

표준 포트 사용 시 로컬 PostgreSQL/Redis와 충돌할 수 있습니다.
**해결 방법**: Docker 실행 전 로컬 서비스 중지

```bash
# macOS (Homebrew)
brew services stop postgresql@17
brew services stop redis

# Linux
sudo systemctl stop postgresql
sudo systemctl stop redis
```

---

## 🔄 현재 네트워크 연결 상태

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         현재 실행 중인 네트워크                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Network: mcphub_kjarvis-network (MCPHub 관리)                          │
│  ├── kjarvis-postgres (5433:5432) ✅                                    │
│  ├── kjarvis-redis (6380:6379) ✅                                       │
│  ├── kjarvis-mcphub-backend (3000) ✅                                   │
│  ├── kjarvis-mcphub-frontend (5173) ✅                                  │
│  ├── kjarvis-adminer (8081) ✅                                          │
│  └── kjarvis-redis-commander (8082) ✅                                  │
│                                                                         │
│  Network: agent-orchestrator_default (Orchestrator 관리)                │
│  ├── kjarvis-kauth (4002) ✅                                            │
│  ├── kjarvis-orchestrator-backend (4001) ✅                             │
│  └── kjarvis-orchestrator-frontend (4000) ✅                            │
│                                                                         │
│  ⚠️ 문제: 두 네트워크가 분리되어 서비스 간 통신 불가                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 즉시 실행 가능한 임시 해결책

MCPHub 팀의 수정 전까지 Orchestrator 서비스들을 MCPHub 네트워크에 연결:

```bash
# 1. 기존 Orchestrator 컨테이너 중지
cd Agent-orchestrator
docker-compose down

# 2. MCPHub 네트워크에 연결하여 실행
docker-compose -f docker-compose.yml up -d \
  --network mcphub_kjarvis-network
```

또는 컨테이너를 네트워크에 수동 연결:

```bash
# 기존 컨테이너를 MCPHub 네트워크에 연결
docker network connect mcphub_kjarvis-network kjarvis-kauth
docker network connect mcphub_kjarvis-network kjarvis-orchestrator-backend
docker network connect mcphub_kjarvis-network kjarvis-orchestrator-frontend

# 연결 확인
docker network inspect mcphub_kjarvis-network
```

---

**Orchestrator Team | 2025-12-19**

