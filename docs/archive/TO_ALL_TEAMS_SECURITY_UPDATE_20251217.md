# 🔒 보안 강화 업데이트 안내

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team (K-Auth + Orchestrator 담당)  
**수신팀**: Agent Team, MCPHub Team

---

## 📢 요약

K-Auth 및 Orchestrator의 보안 설정을 강화했습니다.  
**기존 연동 방식에는 변경 없으며**, 프로덕션 배포 시 참고할 환경변수 가이드를 공유합니다.

---

## ✅ 변경 내용

### 1. 하드코딩 제거 및 환경변수 필수화

| 서비스 | 항목 | 변경 전 | 변경 후 |
|--------|------|---------|---------|
| K-Auth | JWT Secret | 하드코딩 | 환경변수 (미설정 시 자동 생성 + 경고) |
| K-Auth | Admin Password | 하드코딩 | 환경변수 (미설정 시 자동 생성 + 경고) |
| K-Auth | Webhook Secret | 하드코딩 | 환경변수 (미설정 시 경고) |
| Orchestrator | CORS | `["*"]` | 환경변수 기반 도메인 목록 |
| Orchestrator | Client ID/Secret | 하드코딩 | 환경변수 (미설정 시 경고) |

### 2. 서버 시작 시 보안 경고 출력

```
⚠️ JWT_SECRET_KEY not set! Using auto-generated key (not suitable for production)
⚠️ Using default KAUTH_CLIENT_SECRET - set environment variable for production!
```

---

## ⚠️ 각 팀 영향도

| 팀 | 영향 | 조치 필요 |
|----|------|----------|
| **Agent Team** | ❌ 없음 | 없음 |
| **MCPHub Team** | ❌ 없음 | 없음 |

> 기존 연동 방식(X-MCPHub-User-Id 헤더, A2A 프로토콜 등)은 **변경 없음**

---

## 📋 프로덕션 배포 시 환경변수 가이드

### K-Auth (.env)

```bash
# 필수
JWT_SECRET_KEY=<32자 이상 랜덤 문자열>
ADMIN_PASSWORD=<강력한 비밀번호>
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/k_auth

# 권장
KAUTH_WEBHOOK_SECRET=<32자 이상 랜덤 문자열>
ALLOWED_ORIGINS=https://k-jarvis.example.com,https://mcphub.example.com
DEBUG=false
```

### Orchestrator (.env)

```bash
# 필수
KAUTH_CLIENT_ID=<K-Auth에서 발급받은 Client ID>
KAUTH_CLIENT_SECRET=<K-Auth에서 발급받은 Client Secret>

# 권장
CORS_ORIGINS=https://k-jarvis.example.com
KAUTH_URL=https://k-auth.example.com
```

### MCPHub (.env) - 참고용

```bash
# K-Auth 연동
KAUTH_URL=https://k-auth.example.com
KAUTH_CLIENT_ID=<MCPHub용 Client ID>
KAUTH_CLIENT_SECRET=<MCPHub용 Client Secret>
```

---

## 🔐 환경변수 생성 방법

```bash
# 강력한 Secret Key 생성
openssl rand -hex 32

# 예시 출력: a1b2c3d4e5f6...
```

---

## 💬 문의

보안 관련 문의사항은 Orchestrator Team으로 연락 부탁드립니다.

---

**Orchestrator Team (K-Auth + Orchestrator 담당)**

