# Orchestrator Team - Docker 환경 설정

**작성일**: 2025-12-19  
**작성자**: Orchestrator Team  
**대상**: MCPHub Team (통합 Docker Compose 구성용)

---

## 📦 서비스 개요

Orchestrator Team은 **2개 서비스**를 담당합니다:

| 서비스 | 역할 | 포트 |
|--------|------|------|
| **K-Jarvis Orchestrator** | AI Agent 오케스트레이션 플랫폼 | Backend: 4001, Frontend: 4000 |
| **K-Auth** | OAuth 2.0 / SSO 인증 서버 | 4002 |

---

## 📁 Dockerfile 위치

```
Agent-orchestrator/
├── backend/
│   └── Dockerfile          # Orchestrator Backend
└── frontend/
    └── Dockerfile          # Orchestrator Frontend

k-auth/
└── backend/
    └── Dockerfile          # K-Auth Server (NEW!)
```

---

## 🔧 서비스 1: K-Jarvis Orchestrator Backend

### Dockerfile 경로
`Agent-orchestrator/backend/Dockerfile`

### 환경변수

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 | - | ✅ |
| `REDIS_URL` | Redis 연결 문자열 | redis://localhost:6379 | ❌ |
| `OPENAI_API_KEY` | OpenAI API 키 | - | ✅ |
| `LLM_PROVIDER` | LLM 제공자 (openai/azure) | openai | ❌ |
| `KAUTH_URL` | K-Auth 서버 URL | http://localhost:4002 | ✅ |
| `KAUTH_CLIENT_ID` | K-Auth OAuth Client ID | - | ✅ |
| `KAUTH_CLIENT_SECRET` | K-Auth OAuth Client Secret | - | ✅ |
| `MCPHUB_URL` | MCPHub 서버 URL | http://localhost:3000 | ✅ |
| `CORS_ORIGINS` | 허용 CORS 오리진 | http://localhost:4000 | ❌ |
| `OTEL_ENABLED` | OpenTelemetry 활성화 | false | ❌ |

### 포트
- **4001**: HTTP API

### 헬스체크 엔드포인트
```
GET /health
```

### Docker Compose 예시
```yaml
orchestrator-backend:
  build:
    context: ../Agent-orchestrator/backend
    dockerfile: Dockerfile
  environment:
    - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/orchestrator
    - REDIS_URL=redis://redis:6379
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - KAUTH_URL=http://kauth:4002
    - KAUTH_CLIENT_ID=${KAUTH_CLIENT_ID}
    - KAUTH_CLIENT_SECRET=${KAUTH_CLIENT_SECRET}
    - MCPHUB_URL=http://mcphub-backend:3000
    - CORS_ORIGINS=http://localhost:4000,http://orchestrator-frontend:80
  ports:
    - "4001:4001"
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
    kauth:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:4001/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

## 🔧 서비스 2: K-Jarvis Orchestrator Frontend

### Dockerfile 경로
`Agent-orchestrator/frontend/Dockerfile`

### 환경변수 (빌드 시)

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `REACT_APP_API_URL` | Backend API URL | http://localhost:4001 |

### 포트
- **80** (nginx): HTTP 서비스
- 외부 매핑: **4000**

### 헬스체크 엔드포인트
```
GET / (200 OK)
```

### Docker Compose 예시
```yaml
orchestrator-frontend:
  build:
    context: ../Agent-orchestrator/frontend
    dockerfile: Dockerfile
    args:
      - REACT_APP_API_URL=http://localhost:4001
  ports:
    - "4000:80"
  depends_on:
    - orchestrator-backend
  healthcheck:
    test: ["CMD", "wget", "-q", "--spider", "http://localhost:80"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

## 🔧 서비스 3: K-Auth (OAuth 2.0 Server)

### Dockerfile 경로
`k-auth/backend/Dockerfile`

### 환경변수

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 | - | ✅ |
| `REDIS_URL` | Redis 연결 문자열 (Auth Code 저장) | - | ✅ |
| `JWT_SECRET_KEY` | JWT 서명 키 | - | ✅ |
| `JWT_ALGORITHM` | JWT 알고리즘 | HS256 | ❌ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 만료 시간 | 30 | ❌ |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 만료 시간 | 7 | ❌ |
| `ALLOWED_ORIGINS` | 허용 CORS 오리진 | * | ❌ |
| `ADMIN_EMAIL` | 관리자 이메일 | admin@k-jarvis.com | ❌ |
| `ADMIN_PASSWORD` | 관리자 비밀번호 | - | ✅ |
| `ADMIN_USERNAME` | 관리자 사용자명 | admin | ❌ |

### 포트
- **4002**: HTTP API + OAuth Endpoints

### 헬스체크 엔드포인트
```
GET /health
```

### Docker Compose 예시
```yaml
kauth:
  build:
    context: ../k-auth/backend
    dockerfile: Dockerfile
  environment:
    - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/k_auth
    - REDIS_URL=redis://redis:6379/1
    - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    - ALLOWED_ORIGINS=http://localhost:4000,http://localhost:3000,http://localhost:5173
  ports:
    - "4002:4002"
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:4002/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

## 📊 의존 서비스

### Orchestrator Backend
- [x] PostgreSQL (orchestrator DB)
- [x] Redis (선택적, 캐싱용)
- [x] K-Auth (인증)
- [x] MCPHub (MCP 서버 연동)
- [ ] Agent Services (런타임 의존)

### Orchestrator Frontend
- [x] Orchestrator Backend

### K-Auth
- [x] PostgreSQL (k_auth DB)
- [x] Redis (Auth Code 저장)

---

## 🗄️ 데이터베이스 스키마

### Orchestrator DB (`orchestrator`)

```sql
-- 핵심 테이블
users                   -- 사용자 (K-Auth와 동기화)
conversations          -- 대화 세션
messages               -- 대화 메시지
agents                 -- 등록된 에이전트
user_agent_preferences -- 사용자별 에이전트 설정
```

### K-Auth DB (`k_auth`)

```sql
-- 핵심 테이블
users                   -- K-Auth 사용자
oauth_clients          -- OAuth 클라이언트 앱
refresh_tokens         -- Refresh Token
```

---

## 🚀 통합 테스트용 Docker Compose

MCPHub Team이 통합 Compose 작성 시 참고하세요:

```yaml
# Orchestrator Team Services
services:
  # === K-Auth ===
  kauth:
    build:
      context: ../k-auth/backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/k_auth
      - REDIS_URL=redis://redis:6379/1
      - JWT_SECRET_KEY=your-jwt-secret-key
      - ADMIN_PASSWORD=admin123!
    ports:
      - "4002:4002"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # === Orchestrator Backend ===
  orchestrator-backend:
    build:
      context: ../Agent-orchestrator/backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/orchestrator
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - KAUTH_URL=http://kauth:4002
      - KAUTH_CLIENT_ID=kauth_orchestrator
      - KAUTH_CLIENT_SECRET=${KAUTH_CLIENT_SECRET}
      - MCPHUB_URL=http://mcphub-backend:3000
    ports:
      - "4001:4001"
    depends_on:
      kauth:
        condition: service_healthy
      postgres:
        condition: service_healthy

  # === Orchestrator Frontend ===
  orchestrator-frontend:
    build:
      context: ../Agent-orchestrator/frontend
      dockerfile: Dockerfile
      args:
        - REACT_APP_API_URL=http://localhost:4001
    ports:
      - "4000:80"
    depends_on:
      - orchestrator-backend
```

---

## 📋 DB 초기화 스크립트

PostgreSQL 초기화 시 다음 데이터베이스 생성이 필요합니다:

```sql
-- init-scripts/01-create-databases.sql
CREATE DATABASE orchestrator;
CREATE DATABASE k_auth;
```

---

## ✅ 체크리스트

- [x] Orchestrator Backend Dockerfile
- [x] Orchestrator Frontend Dockerfile  
- [x] K-Auth Dockerfile (NEW!)
- [x] 환경변수 목록 문서화
- [x] 의존성 명시
- [x] 포트 정보
- [x] 헬스체크 엔드포인트
- [x] Docker Compose 예시

---

## 📞 문의

- Slack: #k-jarvis-dev
- 담당: Orchestrator Team (정치훈)

---

**Orchestrator Team | 2025-12-19**

