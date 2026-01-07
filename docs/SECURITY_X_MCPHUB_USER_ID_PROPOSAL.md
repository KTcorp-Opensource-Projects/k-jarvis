# X-MCPHub-User-Id 보안 강화 방안

**작성일**: 2026-01-05  
**작성팀**: Orchestrator Team  
**상태**: 📋 검토 중

---

## 📋 현재 상황

### 현재 구현

```
[Orchestrator] → [Agent] → [MCPHub]
      ↓              ↓           ↓
   JWT 보유    X-MCPHub-User-Id   User ID로 토큰 조회
              (단순 문자열)
```

### 보안 우려

| 위험 | 설명 | 심각도 |
|------|------|--------|
| 헤더 위변조 | 악의적 에이전트가 다른 사용자 ID 전달 가능 | 🔴 높음 |
| 중간자 공격 | HTTP 통신 시 헤더 탈취 가능 | 🟡 중간 |
| 에이전트 Key 탈취 | Key 탈취 시 다른 사용자 사칭 가능 | 🔴 높음 |

---

## 🔍 보안 방안 비교

### 방안 A: K-Auth JWT 토큰 전달 (권장)

**설명**: Orchestrator가 K-Auth JWT 토큰을 에이전트에 전달, MCPHub가 직접 검증

```
[Orchestrator] → [Agent] → [MCPHub]
      ↓              ↓           ↓
   JWT 보유    Authorization:    JWT 검증
              Bearer {jwt}       → User ID 추출
```

**구현**:
```python
# Orchestrator → Agent
headers = {
    "X-MCPHub-User-Id": kauth_user_id,
    "X-KAuth-Token": kauth_jwt_token  # 추가
}

# MCPHub
def verify_user_context(request):
    jwt_token = request.headers.get("X-KAuth-Token")
    if jwt_token:
        # K-Auth 공개키로 JWT 검증
        payload = verify_jwt(jwt_token, KAUTH_PUBLIC_KEY)
        return payload["sub"]  # kauth_user_id
    else:
        # 기존 방식 (폴백)
        return request.headers.get("X-MCPHub-User-Id")
```

| 장점 | 단점 |
|------|------|
| ✅ JWT 서명 검증으로 위변조 방지 | ⚠️ MCPHub가 K-Auth 공개키 필요 |
| ✅ 추가 개발 최소화 | ⚠️ JWT 만료 시 갱신 필요 |
| ✅ 표준 방식 | |

**복잡도**: 🟡 중간  
**보안 수준**: ✅ 높음

---

### 방안 B: HMAC 서명 추가

**설명**: X-MCPHub-User-Id에 HMAC 서명 추가

```
[Orchestrator] → [Agent] → [MCPHub]
      ↓              ↓           ↓
   서명 생성    X-MCPHub-User-Id   서명 검증
              X-MCPHub-Signature
```

**구현**:
```python
import hmac
import hashlib

SHARED_SECRET = "orchestrator-mcphub-secret"

# Orchestrator
def sign_user_id(user_id: str) -> str:
    signature = hmac.new(
        SHARED_SECRET.encode(),
        user_id.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

headers = {
    "X-MCPHub-User-Id": kauth_user_id,
    "X-MCPHub-Signature": sign_user_id(kauth_user_id)
}

# MCPHub
def verify_signature(user_id: str, signature: str) -> bool:
    expected = sign_user_id(user_id)
    return hmac.compare_digest(expected, signature)
```

| 장점 | 단점 |
|------|------|
| ✅ 구현 간단 | ⚠️ 공유 비밀키 관리 필요 |
| ✅ 경량 | ⚠️ 비밀키 노출 시 전체 시스템 위험 |

**복잡도**: 🟢 낮음  
**보안 수준**: 🟡 중간

---

### 방안 C: mTLS (Mutual TLS)

**설명**: 서비스 간 상호 인증서 기반 통신

```
[Orchestrator] ←→ [Agent] ←→ [MCPHub]
       TLS 인증서로 상호 인증
```

| 장점 | 단점 |
|------|------|
| ✅ 최고 수준 보안 | ⚠️ 인증서 관리 복잡 |
| ✅ 중간자 공격 완벽 차단 | ⚠️ 개발/운영 비용 높음 |
| ✅ 서비스 인증 | ⚠️ 로컬 개발 어려움 |

**복잡도**: 🔴 높음  
**보안 수준**: ✅ 매우 높음

---

## 📊 방안 비교 요약

| 방안 | 복잡도 | 보안 수준 | 개발 기간 | 권장 환경 |
|------|--------|----------|----------|----------|
| **A: JWT 전달** | 🟡 중간 | ✅ 높음 | 3일 | 스테이징/프로덕션 |
| B: HMAC 서명 | 🟢 낮음 | 🟡 중간 | 1일 | 개발 환경 |
| C: mTLS | 🔴 높음 | ✅ 매우 높음 | 2주 | 고보안 프로덕션 |

---

## ✅ Orchestrator 팀 권장 방안

### 단기 (프로덕션 v1.0): 방안 A (JWT 전달)

**이유**:
1. K-Auth JWT가 이미 존재
2. MCPHub가 K-Auth 공개키로 검증 가능
3. 추가 개발 최소화 (3일 이내)
4. 표준 방식으로 확장성 좋음

### 장기 (프로덕션 v2.0): 방안 C (mTLS)

**이유**:
1. 최고 수준 보안 달성
2. 서비스 간 상호 인증
3. Zero Trust 아키텍처 지원

---

## 📋 구현 계획 (방안 A)

### Orchestrator 팀 작업

| # | 작업 | 예상 일정 |
|---|------|----------|
| 1 | K-Auth JWT 토큰을 에이전트에 전달하도록 수정 | 1일 |
| 2 | 헤더 이름 결정 (X-KAuth-Token) | 즉시 |
| 3 | 테스트 및 검증 | 1일 |

### MCPHub 팀 작업

| # | 작업 | 예상 일정 |
|---|------|----------|
| 1 | K-Auth 공개키 조회 또는 설정 | 0.5일 |
| 2 | JWT 검증 로직 구현 | 1일 |
| 3 | 기존 X-MCPHub-User-Id 폴백 유지 | 0.5일 |
| 4 | 테스트 및 검증 | 1일 |

### Agent 팀 작업

| # | 작업 | 예상 일정 |
|---|------|----------|
| 1 | X-KAuth-Token 헤더 포워딩 | 0.5일 |
| 2 | 테스트 및 검증 | 0.5일 |

---

## 📞 결정 요청

**MCPHub 팀에게**:
1. 방안 A (JWT 전달)에 동의하시나요?
2. K-Auth 공개키 조회 방식 (환경변수 vs API 호출)?
3. 예상 구현 일정?

**Agent 팀에게**:
1. X-KAuth-Token 헤더 포워딩 가능한가요?
2. 예상 구현 일정?

---

**피드백 마감**: 2026-01-07


