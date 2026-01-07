# K-Auth OAuth 2.1 업그레이드 분석 보고서

> **작성일**: 2025-12-29  
> **작성팀**: K-Jarvis Orchestrator Team (K-Auth 담당)  
> **상태**: 🔴 **중요 - 업그레이드 필요**

---

## 📌 Executive Summary

현재 K-Auth는 **OAuth 2.0 (RFC 6749)** 기반으로 구현되어 있습니다.  
그러나 **OAuth 2.1**이 2024년부터 새로운 표준으로 자리잡고 있으며,  
보안 강화를 위해 **K-Auth를 OAuth 2.1로 업그레이드해야 합니다.**

### 핵심 문제점

| 항목 | OAuth 2.1 요구사항 | K-Auth 현재 상태 | 상태 |
|------|-------------------|------------------|------|
| **PKCE** | 모든 클라이언트 필수 | ❌ 미구현 | 🔴 |
| **Implicit Grant** | 제거됨 | ✅ 미사용 | 🟢 |
| **ROPC Grant** | 제거됨 | ✅ 미사용 | 🟢 |
| **Redirect URI 검증** | 정확한 문자열 매칭 | ✅ 구현됨 | 🟢 |
| **Refresh Token Rotation** | 권장 | ✅ 구현됨 | 🟢 |

**결론**: **PKCE 미구현이 가장 큰 보안 취약점**입니다.

---

## 1. OAuth 2.0 vs OAuth 2.1 주요 차이점

### 1.1 OAuth 2.1 주요 변경사항

[Logto 블로그](https://blog.logto.io/ko/oauth-2-1)에 따르면:

| 변경사항 | OAuth 2.0 | OAuth 2.1 |
|----------|-----------|-----------|
| **PKCE** | 공용 클라이언트만 권장 | **모든 클라이언트 필수** |
| **Implicit Grant** | 지원 | **제거** |
| **ROPC Grant** | 지원 (비권장) | **제거** |
| **Redirect URI** | 부분 매칭 허용 | **정확한 매칭 필수** |
| **Refresh Token** | 선택적 | **Rotation 권장** |

### 1.2 PKCE (Proof Key for Code Exchange)란?

PKCE는 **Authorization Code 탈취 공격**을 방지하는 보안 확장입니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PKCE Flow                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 클라이언트: code_verifier 생성 (랜덤 문자열)                │
│  2. 클라이언트: code_challenge = SHA256(code_verifier)          │
│  3. 인증 요청: /authorize?code_challenge=xxx&code_challenge_method=S256 │
│  4. 인증 서버: code_challenge 저장                              │
│  5. 토큰 요청: /token?code_verifier=xxx                         │
│  6. 인증 서버: SHA256(code_verifier) == 저장된 code_challenge 검증 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**PKCE가 필요한 이유:**
- 공용 클라이언트 (SPA, Mobile App)는 client_secret을 안전하게 저장할 수 없음
- Authorization Code가 탈취되어도 code_verifier 없이는 토큰 교환 불가
- **OAuth 2.1에서는 기밀 클라이언트에도 PKCE 필수**

---

## 2. 현재 K-Auth 코드 분석

### 2.1 현재 구현 상태

```python
# k-auth/backend/app/oauth/service.py

async def generate_authorization_code(
    self,
    client_id: str,
    user_id: uuid.UUID,
    redirect_uri: str,
    scopes: List[str]
    # ❌ code_challenge 파라미터 없음
) -> str:
    """Authorization Code 생성 (Redis 사용)"""
    code = secrets.token_urlsafe(32)
    
    code_data = {
        "client_id": client_id,
        "user_id": str(user_id),
        "redirect_uri": redirect_uri,
        "scopes": scopes,
        # ❌ code_challenge 저장 없음
    }
    # ...
```

### 2.2 PKCE 미구현으로 인한 보안 위험

```
공격 시나리오:
1. 사용자가 OAuth 로그인 시작
2. 공격자가 redirect_uri를 가로채서 Authorization Code 탈취
3. 공격자가 탈취한 Code로 토큰 요청
4. ❌ PKCE 없음 → 공격자가 Access Token 획득!

PKCE 적용 시:
1. 사용자가 OAuth 로그인 시작 (code_challenge 포함)
2. 공격자가 Authorization Code 탈취
3. 공격자가 토큰 요청 시도
4. ✅ code_verifier 없음 → 토큰 발급 거부!
```

---

## 3. OAuth 2.1 지원 Python 라이브러리 분석

### 3.1 주요 라이브러리 비교

| 라이브러리 | OAuth 2.1 지원 | PKCE | FastAPI 호환 | 추천도 |
|------------|---------------|------|--------------|--------|
| **Authlib** | ✅ 완전 지원 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Aioauth** | ✅ 부분 지원 | ✅ | ✅ | ⭐⭐⭐⭐ |
| **python-jose** | ❌ JWT만 | ❌ | ✅ | ⭐⭐ |

### 3.2 Authlib - 권장 라이브러리

**Authlib**는 Python에서 가장 완성도 높은 OAuth 라이브러리입니다.

```python
# Authlib PKCE 예제 (클라이언트 측)
from authlib.integrations.requests_client import OAuth2Session
from authlib.common.security import generate_token

# 1. code_verifier 생성
code_verifier = generate_token(48)

# 2. PKCE 활성화된 세션 생성
session = OAuth2Session(
    client_id='your_client_id',
    redirect_uri='https://yourapp.com/callback',
    scope='openid profile email',
    code_challenge_method='S256'  # SHA-256 사용
)

# 3. Authorization URL 생성 (code_challenge 자동 포함)
auth_url, state = session.create_authorization_url(
    'https://k-auth.example.com/oauth/authorize',
    code_verifier=code_verifier
)

# 4. 토큰 교환 (code_verifier 포함)
token = session.fetch_token(
    'https://k-auth.example.com/oauth/token',
    authorization_response=callback_url,
    code_verifier=code_verifier
)
```

### 3.3 서버 측 PKCE 구현 (Authlib)

```python
# Authlib 서버 측 PKCE 검증
from authlib.oauth2.rfc7636 import CodeChallenge

# Authorization Endpoint에서 code_challenge 저장
def authorize(request):
    code_challenge = request.args.get('code_challenge')
    code_challenge_method = request.args.get('code_challenge_method', 'plain')
    
    # Authorization Code와 함께 저장
    save_auth_code(
        code=code,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method
    )

# Token Endpoint에서 code_verifier 검증
def token(request):
    code_verifier = request.form.get('code_verifier')
    auth_code_data = get_auth_code(request.form.get('code'))
    
    # PKCE 검증
    if auth_code_data.code_challenge:
        if not CodeChallenge.verify(
            code_verifier,
            auth_code_data.code_challenge,
            auth_code_data.code_challenge_method
        ):
            raise InvalidGrantError('Invalid code_verifier')
```

---

## 4. K-Auth OAuth 2.1 업그레이드 계획

### 4.1 Phase 1: PKCE 구현 (필수)

**수정 파일:**
- `k-auth/backend/app/oauth/service.py`
- `k-auth/backend/app/api.py` (OAuth 엔드포인트)

**구현 사항:**

```python
# 1. Authorization Code 생성 시 code_challenge 저장
async def generate_authorization_code(
    self,
    client_id: str,
    user_id: uuid.UUID,
    redirect_uri: str,
    scopes: List[str],
    code_challenge: Optional[str] = None,  # 추가
    code_challenge_method: str = "S256"     # 추가
) -> str:
    code_data = {
        "client_id": client_id,
        "user_id": str(user_id),
        "redirect_uri": redirect_uri,
        "scopes": scopes,
        "code_challenge": code_challenge,           # 추가
        "code_challenge_method": code_challenge_method  # 추가
    }
    # ...

# 2. 토큰 교환 시 code_verifier 검증
async def exchange_code_for_tokens(
    self,
    db: AsyncSession,
    code: str,
    client: OAuthClient,
    redirect_uri: str,
    code_verifier: Optional[str] = None  # 추가
) -> Optional[Dict]:
    code_data = await self.validate_authorization_code(...)
    
    # PKCE 검증
    if code_data.get("code_challenge"):
        if not self._verify_pkce(
            code_verifier,
            code_data["code_challenge"],
            code_data["code_challenge_method"]
        ):
            logger.warning("PKCE verification failed")
            return None
    # ...

def _verify_pkce(
    self,
    code_verifier: str,
    code_challenge: str,
    method: str
) -> bool:
    """PKCE 검증"""
    import hashlib
    import base64
    
    if method == "S256":
        # SHA-256 해시 후 Base64URL 인코딩
        digest = hashlib.sha256(code_verifier.encode()).digest()
        computed = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
        return computed == code_challenge
    elif method == "plain":
        return code_verifier == code_challenge
    return False
```

### 4.2 Phase 2: 공용 클라이언트 PKCE 필수화

```python
# 클라이언트 타입에 따른 PKCE 강제
async def validate_authorize_request(
    client: OAuthClient,
    code_challenge: Optional[str]
) -> bool:
    # 공용 클라이언트 (SPA, Mobile)는 PKCE 필수
    if client.token_endpoint_auth_method == "none":
        if not code_challenge:
            raise OAuth2Error(
                "invalid_request",
                "PKCE is required for public clients"
            )
    return True
```

### 4.3 Phase 3: 모든 클라이언트 PKCE 필수화 (OAuth 2.1 완전 준수)

```python
# OAuth 2.1 완전 준수: 모든 클라이언트에 PKCE 필수
async def validate_authorize_request(
    client: OAuthClient,
    code_challenge: Optional[str]
) -> bool:
    if not code_challenge:
        raise OAuth2Error(
            "invalid_request",
            "PKCE is required (OAuth 2.1)"
        )
    return True
```

---

## 5. 마이그레이션 전략

### 5.1 하위 호환성 유지 기간

```
Phase 1 (즉시): PKCE 지원 추가 (선택적)
    ↓
Phase 2 (1개월 후): 공용 클라이언트 PKCE 필수
    ↓
Phase 3 (3개월 후): 모든 클라이언트 PKCE 필수 (OAuth 2.1 완전 준수)
```

### 5.2 클라이언트 업데이트 가이드

**K-Jarvis Orchestrator 업데이트:**

```python
# backend/app/auth/kauth.py 수정

import hashlib
import base64
import secrets

def generate_pkce():
    """PKCE code_verifier 및 code_challenge 생성"""
    code_verifier = secrets.token_urlsafe(43)
    
    # S256: SHA-256 해시 후 Base64URL 인코딩
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    
    return code_verifier, code_challenge

# OAuth 로그인 시작
code_verifier, code_challenge = generate_pkce()
# 세션에 code_verifier 저장
session["code_verifier"] = code_verifier

# Authorization URL에 code_challenge 추가
auth_url = (
    f"{KAUTH_URL}/oauth/authorize"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&response_type=code"
    f"&scope=openid profile email"
    f"&code_challenge={code_challenge}"
    f"&code_challenge_method=S256"
)

# 토큰 교환 시 code_verifier 포함
token_response = await exchange_code(
    code=auth_code,
    code_verifier=session["code_verifier"]
)
```

---

## 6. 권장사항

### 6.1 즉시 조치 (High Priority)

1. **PKCE 구현**: `oauth/service.py`에 PKCE 검증 로직 추가
2. **API 엔드포인트 업데이트**: `/oauth/authorize`, `/oauth/token` 파라미터 추가
3. **클라이언트 업데이트 가이드 작성**: K-Jarvis, MCPHub 팀에 전달

### 6.2 중기 조치 (Medium Priority)

1. **Authlib 라이브러리 도입 검토**: 자체 구현보다 검증된 라이브러리 사용
2. **OAuth 2.1 완전 준수 로드맵 수립**
3. **보안 감사 수행**

### 6.3 문서화

1. **K-Auth OAuth 2.1 마이그레이션 가이드** 작성
2. **외부 개발자용 통합 가이드** 업데이트
3. **Confluence 문서 허브** 업데이트

---

## 7. 결론

**K-Auth의 OAuth 2.1 업그레이드는 필수입니다.**

현재 PKCE 미구현으로 인해 Authorization Code 탈취 공격에 취약합니다.  
특히 K-Jarvis Frontend (SPA)와 같은 공용 클라이언트는 즉시 PKCE가 필요합니다.

### 우선순위

| 우선순위 | 작업 | 예상 소요 |
|----------|------|----------|
| 🔴 P0 | PKCE 구현 | 2-3일 |
| 🟠 P1 | 클라이언트 업데이트 | 1-2일 |
| 🟡 P2 | 문서화 | 1일 |
| 🟢 P3 | OAuth 2.1 완전 준수 | 1주 |

---

## 📎 참고 자료

- [OAuth 2.1 Draft Specification](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-11)
- [Logto - OAuth 2.1이 도착했습니다](https://blog.logto.io/ko/oauth-2-1)
- [Authlib Documentation](https://docs.authlib.org/)
- [RFC 7636 - PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [Spring Authorization Server - OAuth 2.1](https://docs.spring.io/spring-authorization-server/reference/overview.html)

---

**K-Jarvis Orchestrator Team (K-Auth 담당)** 🔐

