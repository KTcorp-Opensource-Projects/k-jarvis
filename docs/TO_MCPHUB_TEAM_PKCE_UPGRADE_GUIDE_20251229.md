# K-Auth PKCE 업그레이드 가이드 - MCPHub (K-ARC) 팀용

**From**: Orchestrator Team  
**To**: MCPHub (K-ARC) Team  
**Date**: 2025-12-29  
**Subject**: OAuth 2.1 PKCE 보안 업그레이드 완료 및 적용 가이드

---

## 📋 요약

K-Auth에 **OAuth 2.1 핵심 보안 기능인 PKCE (Proof Key for Code Exchange)**가 구현되었습니다.
K-Jarvis Orchestrator에서 테스트를 완료했으며, MCPHub (K-ARC)에도 동일하게 적용해주시기 바랍니다.

---

## 🔐 PKCE란?

**PKCE (Proof Key for Code Exchange)**는 Authorization Code 가로채기 공격을 방지하는 OAuth 2.1 필수 보안 기능입니다.

### 기존 OAuth 2.0의 취약점
```
[악의적 앱] → 인증 코드 가로채기 → 토큰 탈취 가능
```

### PKCE 적용 후
```
[악의적 앱] → 인증 코드 가로채도 → code_verifier 없이 토큰 교환 불가
```

---

## 🛠️ 구현 방법

### Step 1: code_verifier 및 code_challenge 생성

```python
import secrets
import hashlib
import base64

def create_s256_code_challenge(code_verifier: str) -> str:
    """PKCE S256 code_challenge 생성"""
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')

# 로그인 시작 시 생성
code_verifier = secrets.token_urlsafe(64)  # 43-128자 랜덤 문자열
code_challenge = create_s256_code_challenge(code_verifier)
```

### Step 2: Authorization 요청에 PKCE 파라미터 추가

```python
# K-Auth /oauth/authorize 요청
authorize_url = (
    f"{KAUTH_URL}/oauth/authorize"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=openid%20profile%20email"
    f"&state={state}"
    f"&code_challenge={code_challenge}"      # ← 추가
    f"&code_challenge_method=S256"           # ← 추가
)
```

### Step 3: code_verifier 저장 (세션/Redis)

```python
# Redis에 state와 함께 code_verifier 저장
await redis_client.setex(
    f"oauth_state:{state}",
    600,  # 10분 TTL
    json.dumps({
        "created_at": datetime.utcnow().isoformat(),
        "code_verifier": code_verifier  # ← 저장
    })
)
```

### Step 4: Token 요청에 code_verifier 추가

```python
# K-Auth /oauth/token 요청
token_response = await client.post(
    f"{KAUTH_URL}/oauth/token",
    data={
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,  # Confidential Client인 경우
        "code_verifier": code_verifier   # ← 추가 (PKCE)
    }
)
```

---

## 📝 K-Auth API 변경사항

### GET /oauth/authorize

| 파라미터 | 필수 | 설명 |
|---------|------|------|
| code_challenge | 권장* | S256으로 해시된 code_verifier |
| code_challenge_method | 권장* | `S256` (고정) |

*Public Client (token_endpoint_auth_method=none)의 경우 필수

### POST /oauth/token

| 파라미터 | 필수 | 설명 |
|---------|------|------|
| code_verifier | 권장* | 원본 code_verifier (43-128자) |

*code_challenge가 전송된 경우 필수

---

## ✅ 테스트 결과 (K-Jarvis Orchestrator)

```
2025-12-29 07:38:29 | INFO | [PKCE] Authorization code created with code_challenge (method: S256)
2025-12-29 07:38:29 | DEBUG | [PKCE] Verification successful
2025-12-29 07:38:29 | INFO | [PKCE] Token exchange: PKCE verification passed
```

**전체 플로우 성공:**
1. ✅ Orchestrator Frontend → K-Auth /oauth/authorize (with code_challenge)
2. ✅ K-Auth 로그인 → Redirect with authorization code
3. ✅ Orchestrator Backend → K-Auth /oauth/token (with code_verifier)
4. ✅ PKCE 검증 통과 → 토큰 발급 → 로그인 완료

---

## 🔧 참고 코드 (Orchestrator 구현)

### 파일: `backend/app/auth/kauth.py`

```python
# PKCE 헬퍼 함수
def create_s256_code_challenge(code_verifier: str) -> str:
    """PKCE S256 code_challenge 생성"""
    import hashlib
    import base64
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')

# 로그인 시작
@kauth_router.get("")
async def kauth_login():
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = create_s256_code_challenge(code_verifier)
    
    # Redis에 저장
    await redis_client.setex(
        f"oauth_state:{state}",
        600,
        json.dumps({
            "created_at": datetime.utcnow().isoformat(),
            "code_verifier": code_verifier
        })
    )
    
    # authorize URL에 PKCE 파라미터 추가
    authorize_url = f"{KAUTH_URL}/oauth/authorize?...&code_challenge={code_challenge}&code_challenge_method=S256"
    return RedirectResponse(url=authorize_url)

# 콜백 처리
@kauth_router.get("/callback")
async def kauth_callback(code: str, state: str):
    # Redis에서 code_verifier 조회
    state_data = await redis_client.get(f"oauth_state:{state}")
    code_verifier = json.loads(state_data).get("code_verifier")
    
    # 토큰 요청에 code_verifier 포함
    token_response = await client.post(
        f"{KAUTH_URL}/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code_verifier": code_verifier  # PKCE
        }
    )
```

---

## 📌 주의사항

1. **code_verifier 길이**: 43-128자 사이 (secrets.token_urlsafe(64) 권장)
2. **해시 알고리즘**: S256만 지원 (plain은 보안 이유로 미지원)
3. **저장소**: code_verifier는 반드시 서버 측(Redis/세션)에 저장
4. **일회성**: code_verifier는 토큰 교환 후 즉시 삭제

---

## 🚀 적용 체크리스트

- [ ] code_verifier 생성 로직 추가
- [ ] code_challenge 생성 함수 구현
- [ ] /oauth/authorize 요청에 code_challenge, code_challenge_method 추가
- [ ] Redis/세션에 code_verifier 저장
- [ ] /oauth/token 요청에 code_verifier 추가
- [ ] 통합 테스트 수행

---

## 📞 문의

구현 중 문제가 있으시면 Orchestrator Team에 문의해주세요.

**관련 파일:**
- K-Auth: `k-auth/backend/app/oauth/service.py`
- K-Auth: `k-auth/backend/app/api.py`
- Orchestrator: `backend/app/auth/kauth.py`

---

**작성자**: Orchestrator Team  
**검증일**: 2025-12-29

