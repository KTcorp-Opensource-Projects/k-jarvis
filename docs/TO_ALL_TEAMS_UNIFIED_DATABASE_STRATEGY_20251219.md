# 🗄️ 전체 팀 공지 - 통합 PostgreSQL 데이터베이스 전략

**작성일**: 2025-12-19  
**작성자**: MCPHub Team  
**대상**: Agent Team, Orchestrator Team, MCPHub Team  
**긴급도**: 높음

---

## ⚠️ 핵심 사항

**모든 K-Jarvis 서비스는 하나의 PostgreSQL 인스턴스를 공유합니다.**

각 팀은 별도의 **데이터베이스(DB)**를 사용하되, 동일한 PostgreSQL 서버에 연결합니다.

---

## 🏗️ 통합 DB 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Server                             │
│                    (단일 인스턴스)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ │
│  │   Database:      │ │   Database:      │ │   Database:      │ │
│  │   mcphub         │ │   k_auth         │ │   orchestrator   │ │
│  │                  │ │                  │ │                  │ │
│  │ • users          │ │ • users          │ │ • users          │ │
│  │ • mcp_servers    │ │ • oauth_clients  │ │ • conversations  │ │
│  │ • mcphub_keys    │ │ • refresh_tokens │ │ • messages       │ │
│  │ • subscriptions  │ │                  │ │ • agents         │ │
│  │ • ...            │ │                  │ │ • ...            │ │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
┌──────────┐         ┌──────────┐          ┌──────────┐
│ MCPHub   │         │ K-Auth   │          │Orchestrator│
│ Backend  │         │ Server   │          │ Backend   │
└──────────┘         └──────────┘          └──────────┘
```

---

## 📋 데이터베이스 및 사용자 설정

### Docker Compose 통합 설정

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16  # 벡터 확장 지원
    container_name: kjarvis-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d  # 초기화 스크립트
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### 초기화 스크립트 (`init-scripts/01-init-databases.sql`)

```sql
-- ============================================
-- K-Jarvis 통합 DB 초기화 스크립트
-- ============================================

-- 1. 확장 설치
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector

-- 2. 사용자 생성
CREATE USER mcphub WITH PASSWORD 'mcphub123';
CREATE USER kauth WITH PASSWORD 'kauth123';
CREATE USER orchestrator WITH PASSWORD 'orch123';

-- 3. 데이터베이스 생성
CREATE DATABASE mcphub OWNER mcphub;
CREATE DATABASE k_auth OWNER kauth;
CREATE DATABASE orchestrator OWNER orchestrator;

-- 4. 권한 부여
GRANT ALL PRIVILEGES ON DATABASE mcphub TO mcphub;
GRANT ALL PRIVILEGES ON DATABASE k_auth TO kauth;
GRANT ALL PRIVILEGES ON DATABASE orchestrator TO orchestrator;

-- 5. 각 DB에 확장 설치
\c mcphub
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

\c k_auth
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c orchestrator
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

## 🔗 팀별 연결 정보

### MCPHub Team

| 항목 | 값 |
|------|-----|
| **Database** | `mcphub` |
| **User** | `mcphub` |
| **Password** | `mcphub123` |
| **Host (Docker)** | `postgres` |
| **Host (로컬)** | `localhost` |
| **Port** | `5432` |
| **DATABASE_URL** | `postgresql://mcphub:mcphub123@postgres:5432/mcphub` |

### K-Auth Team (Orchestrator)

| 항목 | 값 |
|------|-----|
| **Database** | `k_auth` |
| **User** | `kauth` |
| **Password** | `kauth123` |
| **Host (Docker)** | `postgres` |
| **Host (로컬)** | `localhost` |
| **Port** | `5432` |
| **DATABASE_URL** | `postgresql://kauth:kauth123@postgres:5432/k_auth` |

### Orchestrator Team

| 항목 | 값 |
|------|-----|
| **Database** | `orchestrator` |
| **User** | `orchestrator` |
| **Password** | `orch123` |
| **Host (Docker)** | `postgres` |
| **Host (로컬)** | `localhost` |
| **Port** | `5432` |
| **DATABASE_URL** | `postgresql://orchestrator:orch123@postgres:5432/orchestrator` |

---

## 📊 MCPHub 스키마 구조 (참고용)

### 핵심 테이블

```
┌─────────────────────────────────────────────────────────────┐
│                       MCPHub Database                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐      ┌──────────────────────────────┐ │
│  │     users        │──────│    mcphub_keys               │ │
│  ├──────────────────┤      ├──────────────────────────────┤ │
│  │ id (uuid, PK)    │      │ id (uuid, PK)                │ │
│  │ username         │      │ keyValue (unique)            │ │
│  │ email            │      │ name                         │ │
│  │ kauthUserId      │◀────▶│ userId (FK)                  │ │
│  │ authProvider     │      │ serviceTokens (jsonb)        │ │
│  │ isAdmin          │      │ expiresAt                    │ │
│  │ isActive         │      │ isActive                     │ │
│  └──────────────────┘      └──────────────────────────────┘ │
│           │                                                  │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────┐   ┌────────────────────┐  │
│  │ user_server_subscriptions    │   │   mcp_servers      │  │
│  ├──────────────────────────────┤   ├────────────────────┤  │
│  │ id (uuid, PK)                │   │ id (int, PK)       │  │
│  │ user_id (FK → users)         │──▶│ name (unique)      │  │
│  │ server_id (FK → mcp_servers) │   │ displayName        │  │
│  │ is_active                    │   │ type (enum)        │  │
│  │ settings (jsonb)             │   │ url                │  │
│  │ installed_at                 │   │ headers (jsonb)    │  │
│  └──────────────────────────────┘   │ enabled            │  │
│                                     └────────────────────┘  │
│                                              │               │
│                                              ▼               │
│                                   ┌────────────────────────┐│
│                                   │ mcp_server_env_vars    ││
│                                   ├────────────────────────┤│
│                                   │ id (int, PK)           ││
│                                   │ serverId (FK)          ││
│                                   │ name                   ││
│                                   │ displayName            ││
│                                   │ description            ││
│                                   │ required               ││
│                                   └────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 전체 테이블 목록

| 테이블명 | 설명 | 주요 컬럼 |
|---------|------|----------|
| `users` | 사용자 정보 | id, username, kauthUserId, isAdmin |
| `mcp_servers` | MCP 서버 정보 | id, name, type, url, enabled |
| `mcphub_keys` | API Key | id, keyValue, userId, serviceTokens |
| `user_server_subscriptions` | 서버 구독 | userId, serverId, isActive |
| `mcp_server_env_vars` | 서버별 환경변수 정의 | serverId, name, required |
| `mcphub_key_requests` | 키 발급 요청 | userId, keyName, status |
| `mcp_server_requests` | 서버 등록 요청 | userId, serverName, status |
| `user_tokens` | 사용자 서비스 토큰 | userId, tokenName, tokenValue |
| `user_groups` | (Deprecated) 사용자 그룹 | - |
| `platform_keys` | 플랫폼 키 | - |
| `platform_usage` | 사용량 통계 | - |
| `vector_embeddings` | 벡터 임베딩 | - |

---

## 🔑 서비스 간 사용자 연동 (중요!)

### K-Auth ↔ MCPHub 사용자 동기화

MCPHub의 `users.kauthUserId` 컬럼을 통해 K-Auth 사용자와 연동됩니다.

```typescript
// MCPHub User Entity
@Entity('users')
export class User {
  @Column({ type: 'varchar', length: 100, unique: true, nullable: true })
  kauthUserId?: string;  // K-Auth 사용자 ID
  
  @Column({ type: 'varchar', length: 20, default: 'local' })
  authProvider?: string;  // 'local' | 'kauth'
}
```

### 연동 플로우

```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│   Client    │        │   K-Auth    │        │   MCPHub    │
└──────┬──────┘        └──────┬──────┘        └──────┬──────┘
       │                      │                      │
       │  1. OAuth 로그인     │                      │
       │─────────────────────▶│                      │
       │                      │                      │
       │  2. Access Token     │                      │
       │◀─────────────────────│                      │
       │                      │                      │
       │  3. MCPHub 접속 (Token + X-MCPHub-User-Id)  │
       │────────────────────────────────────────────▶│
       │                      │                      │
       │                      │  4. kauthUserId로   │
       │                      │     사용자 조회/생성 │
       │                      │                      │
       │  5. 서비스 이용      │                      │
       │◀────────────────────────────────────────────│
```

---

## ⚠️ 주의사항

### 1. 각 팀은 자신의 DB만 사용

```sql
-- ❌ 금지: 다른 팀 DB 직접 접근
SELECT * FROM k_auth.users;  -- K-Auth DB 직접 접근

-- ✅ 권장: API를 통한 연동
GET /api/kauth/users/{userId}
```

### 2. 테이블 마이그레이션은 각 팀이 관리

```
MCPHub: apps/backend/migrations/
K-Auth: k-auth/backend/migrations/
Orchestrator: Agent-orchestrator/backend/migrations/
```

### 3. Docker 환경에서 호스트명

```yaml
# Docker 내부에서는 컨테이너 이름 사용
DATABASE_URL=postgresql://mcphub:mcphub123@postgres:5432/mcphub

# 로컬 개발에서는 localhost 사용
DATABASE_URL=postgresql://mcphub:mcphub123@localhost:5432/mcphub
```

---

## 🚀 실행 방법

### 1. PostgreSQL 단독 실행 (모든 팀 공통)

```bash
# 프로젝트 루트에서
docker-compose -f docker-compose.postgres.yml up -d

# 또는 기존 docker-compose.integration.yml 사용
docker-compose -f docker-compose.integration.yml up -d postgres
```

### 2. 각 팀 서비스 연결

```bash
# MCPHub
cd mcphub && npm run dev

# Orchestrator
cd Agent-orchestrator && npm run dev

# K-Auth
cd k-auth && npm run dev
```

---

## 📝 체크리스트

### 각 팀 확인 사항

- [ ] DATABASE_URL 환경변수가 올바르게 설정되었는가?
- [ ] Docker 환경에서 호스트명이 `postgres`로 설정되었는가?
- [ ] 초기화 스크립트가 포함되었는가?
- [ ] 마이그레이션이 정상 실행되는가?

---

## 📞 문의

- **MCPHub Team**: Slack #mcphub-dev
- **Orchestrator Team**: Slack #k-jarvis-dev
- **긴급**: 정치훈 (jungchihoon)

---

**MCPHub Team | 2025-12-19**

