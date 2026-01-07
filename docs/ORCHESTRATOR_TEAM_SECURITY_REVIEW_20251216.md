# Orchestrator Team 보안/아키텍처 검토 결과

**작성일**: 2024-12-16  
**작성팀**: Orchestrator Team  
**검토 범위**: K-Auth, Orchestrator Backend/Frontend, 서비스 간 통신

---

## 🔴 1. 발견된 보안 이슈

### 심각도: HIGH (🔴)

| # | 항목 | 위치 | 설명 | 조치 방안 | 상태 |
|---|------|------|------|----------|------|
| 1 | **CORS 와일드카드** | `orchestrator/backend/app/main.py:88` | `allow_origins=["*"]` 설정 | 프로덕션에서 특정 도메인만 허용 | ⚠️ 수정 필요 |
| 2 | **JWT Secret 기본값** | `k-auth/backend/app/config.py:22` | `"k-auth-secret-key-change-in-production"` | 환경변수로 강력한 키 설정 필수 | ⚠️ 수정 필요 |
| 3 | **Admin 비밀번호 하드코딩** | `k-auth/backend/app/config.py:35` | `admin_password: str = "admin123"` | 환경변수로 변경 필수 | ⚠️ 수정 필요 |
| 4 | **Client Secret 하드코딩** | `orchestrator/backend/app/auth/kauth.py:23` | 기본값으로 Client Secret 노출 | 환경변수 설정 필수 | ⚠️ 수정 필요 |
| 5 | **Rate Limiting 미적용** | K-Auth 전체 | 로그인/토큰 발급 엔드포인트에 Rate Limit 없음 | Brute Force 공격 방어 필요 | ⚠️ 구현 필요 |

### 심각도: MEDIUM (🟡)

| # | 항목 | 위치 | 설명 | 조치 방안 | 상태 |
|---|------|------|------|----------|------|
| 6 | **Debug 모드 기본값** | `k-auth/backend/app/config.py:16` | `debug: bool = True` | 프로덕션에서 False 설정 | ⚠️ 확인 필요 |
| 7 | **DB 비밀번호 기본값** | `k-auth/backend/app/config.py:19` | `postgres:postgres` | 프로덕션에서 강력한 비밀번호 설정 | ⚠️ 확인 필요 |
| 8 | **Webhook Secret 하드코딩** | `k-auth/backend/app/webhook/service.py:20` | `"k-auth-webhook-secret-key"` | 환경변수로 변경 | ⚠️ 수정 필요 |

### 심각도: LOW (🟢)

| # | 항목 | 위치 | 설명 | 조치 방안 | 상태 |
|---|------|------|------|----------|------|
| 9 | **Fallback 메모리 저장소** | `orchestrator/backend/app/auth/kauth.py:42` | Redis 미연결 시 인메모리 사용 | 프로덕션에서 Redis 필수 | ℹ️ 참고 |

---

## 🟢 2. 정상 확인된 항목

### 인증/인가
- [x] JWT 토큰 검증 로직 정상 (HS256 알고리즘 사용)
- [x] 토큰 만료 처리 적절 (Access: 30분, Refresh: 7일)
- [x] 권한 체크 엔드포인트별 적용됨
- [x] 관리자/일반사용자 권한 분리됨 (`is_admin` 필드)

### 민감 정보 보호
- [x] 환경변수 기반 설정 지원 (`os.getenv` 사용)
- [x] 비밀번호 해싱 적용 (bcrypt via passlib)
- [x] Client Secret 해싱 저장 (`pwd_context.hash()`)

### 통신 보안
- [x] K-Auth 콜백 시 state 파라미터 검증 (CSRF 방지)
- [x] Authorization Code Flow 정상 구현
- [x] Refresh Token 폐기 기능 구현

### 입력 검증
- [x] Pydantic 모델 기반 입력 검증
- [x] SQLAlchemy 파라미터 바인딩 사용 (SQL Injection 방지)
- [x] 비밀번호 길이 제한 (min=6, max=100)

---

## 🔍 3. X-MCPHub-User-Id 헤더 보안 분석

### 현재 구현

```
[User] → [K-Auth] → [Orchestrator] → [Agent] → [MCPHub]
                         │               │          │
                    JWT 발급         헤더 추가    토큰 조회
                (kauth_user_id)   (X-MCPHub-User-Id)
```

### 보안 검토

| 검토 항목 | 결과 | 비고 |
|----------|------|------|
| 헤더 위조 가능성 | 🟡 내부망에서만 허용 | Agent → MCPHub는 내부 통신 |
| 인증 후 전달 여부 | ✅ | JWT에서 kauth_user_id 추출 후 전달 |
| MCPHub 신뢰 가능 여부 | 🟡 조건부 | 내부망 + 서비스 간 인증 추가 권장 |

### 권장 개선 사항

```python
# 현재: 헤더만 전달
headers["X-MCPHub-User-Id"] = kauth_user_id

# 권장: 서명된 토큰 사용 (서비스 간 인증)
service_token = sign_service_request(kauth_user_id, timestamp)
headers["X-MCPHub-Service-Auth"] = service_token
```

---

## 📋 4. 아키텍처 검토 결과

### 4.1 코드 구조

| 항목 | 상태 | 비고 |
|------|------|------|
| 일관성 | ✅ | 모듈별 분리 적절 |
| 중복 코드 | 🟡 | DB 연결 로직 일부 중복 |
| 데드 코드 | ✅ | 발견 안됨 |
| 하드코딩 | 🔴 | 상기 보안 이슈 참조 |

### 4.2 의존성 관리

| 항목 | 상태 | 비고 |
|------|------|------|
| 순환 의존성 | ✅ | 발견 안됨 |
| 불필요한 의존성 | ✅ | 적절함 |
| 버전 고정 | 🟡 | requirements.txt에 일부 버전 미지정 |

### 4.3 에러 처리

| 항목 | 상태 | 비고 |
|------|------|------|
| 예외 처리 | ✅ | try-except 적절 사용 |
| 에러 로깅 | ✅ | loguru 사용 |
| 장애 전파 방지 | ✅ | Agent 실패 시 폴백 처리 |

---

## 🛠️ 5. 즉시 조치 필요 항목

### Priority 1: 프로덕션 배포 전 필수

```bash
# 1. K-Auth 환경변수 설정
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
export ADMIN_PASSWORD="$(openssl rand -base64 16)"
export DATABASE_URL="postgresql+asyncpg://user:STRONG_PASSWORD@host:5432/k_auth"

# 2. Orchestrator 환경변수 설정  
export KAUTH_CLIENT_SECRET="실제_클라이언트_시크릿"

# 3. CORS 설정 수정 (backend/app/main.py)
# allow_origins=["*"] → allow_origins=["https://your-domain.com"]
```

### Priority 2: 조속히 개선

1. **Rate Limiting 구현** - K-Auth 로그인 엔드포인트
2. **서비스 간 인증 강화** - X-MCPHub-User-Id 서명 검증
3. **Audit 로깅** - 민감 작업 로그 기록

---

## 📊 6. 보안 점수 요약

| 영역 | 점수 | 비고 |
|------|------|------|
| 인증/인가 | 8/10 | Rate Limiting 미적용 |
| 데이터 보호 | 7/10 | 하드코딩 이슈 |
| 통신 보안 | 8/10 | 서비스 간 인증 강화 필요 |
| 코드 품질 | 9/10 | 양호 |
| **종합** | **8/10** | 프로덕션 배포 전 조치 필요 |

---

## ✅ 7. 결론

K-Jarvis 1.0은 **개발/테스트 환경에서는 안전**하나, **프로덕션 배포 전 다음 항목 필수 조치**:

1. 🔴 모든 하드코딩된 Secret/Password를 환경변수로 이동
2. 🔴 CORS 와일드카드 제거
3. 🟡 Rate Limiting 구현
4. 🟡 Debug 모드 비활성화

---

**Orchestrator Team - 보안 검토 완료**


