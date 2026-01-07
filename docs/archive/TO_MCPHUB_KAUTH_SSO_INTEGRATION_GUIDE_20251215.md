# MCPHub K-Auth SSO 연동 가이드

**작성일**: 2024-12-15  
**작성팀**: Orchestrator Team  
**수신팀**: MCPHub Team  
**우선순위**: 🔴 HIGH

---

## 1. 개요

K-Jarvis 플랫폼의 SSO 통합을 위해 MCPHub도 K-Auth와 연동해야 합니다.

현재 K-Jarvis Orchestrator는 K-Auth SSO 연동이 완료되어 정상 작동 중입니다.
MCPHub도 동일한 방식으로 연동하여 **단일 계정으로 모든 서비스 접근**이 가능하도록 해주세요.

---

## 2. 현재 상태

### Orchestrator (✅ 완료)
- K-Auth SSO 로그인 버튼 구현
- OAuth 2.0 Authorization Code Flow 적용
- JIT Provisioning (최초 로그인 시 자동 계정 생성)
- JWT에 `kauth_user_id` 포함하여 MCPHub 토큰 조회에 활용

### MCPHub (⏳ 필요)
- K-Auth SSO 로그인 버튼 추가 필요
- OAuth 2.0 콜백 처리 구현 필요
- 사용자 DB 연동 (JIT Provisioning)

---

## 3. 구현 가이드

### 3.1 K-Auth OAuth App 등록

MCPHub용 OAuth App이 이미 등록되어 있습니다:

```
Client ID: kauth_dhsCDjZxNeQ-NhVhqsce7A
Client Name: MCPHub
Redirect URIs:
  - http://localhost:3000/auth/kauth/callback
  - https://mcphub.example.com/auth/kauth/callback
```

> ⚠️ Client Secret은 MCPHub 팀에서 관리해야 합니다. 필요 시 K-Auth 개발자 콘솔에서 재발급하세요.

### 3.2 환경변수 설정

**.env 파일에 추가:**

```bash
# K-Auth OAuth 설정
KAUTH_URL=http://localhost:4002
# 프로덕션: KAUTH_URL=https://k-auth.k-jarvis.com

KAUTH_CLIENT_ID=kauth_dhsCDjZxNeQ-NhVhqsce7A
KAUTH_CLIENT_SECRET=<your_client_secret>
KAUTH_CALLBACK_URL=http://localhost:3000/auth/kauth/callback
KAUTH_SCOPES=openid profile email
```

### 3.3 Backend 구현 (Python 예시)

Orchestrator의 구현을 참고하여 MCPHub에 맞게 수정하세요:

**kauth.py (라우터):**

```python
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
import httpx
import secrets
import os

KAUTH_URL = os.getenv("KAUTH_URL", "http://localhost:4002")
KAUTH_CLIENT_ID = os.getenv("KAUTH_CLIENT_ID")
KAUTH_CLIENT_SECRET = os.getenv("KAUTH_CLIENT_SECRET")
KAUTH_CALLBACK_URL = os.getenv("KAUTH_CALLBACK_URL")

router = APIRouter(prefix="/auth/kauth")

# State 저장 (프로덕션에서는 Redis 사용)
states = {}


@router.get("")
async def kauth_login():
    """K-Auth SSO 로그인 시작"""
    state = secrets.token_urlsafe(16)
    states[state] = True
    
    auth_url = (
        f"{KAUTH_URL}/oauth/authorize?"
        f"response_type=code&"
        f"client_id={KAUTH_CLIENT_ID}&"
        f"redirect_uri={KAUTH_CALLBACK_URL}&"
        f"scope=openid%20profile%20email&"
        f"state={state}"
    )
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def kauth_callback(code: str = None, state: str = None, error: str = None):
    """K-Auth OAuth 콜백 처리"""
    if error:
        return RedirectResponse(url=f"/?error={error}")
    
    if state not in states:
        return RedirectResponse(url="/?error=invalid_state")
    del states[state]
    
    async with httpx.AsyncClient() as client:
        # 1. Code → Token 교환
        token_res = await client.post(
            f"{KAUTH_URL}/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": KAUTH_CALLBACK_URL,
                "client_id": KAUTH_CLIENT_ID,
                "client_secret": KAUTH_CLIENT_SECRET
            }
        )
        tokens = token_res.json()
        
        # 2. 사용자 정보 조회
        user_res = await client.get(
            f"{KAUTH_URL}/oauth/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        kauth_user = user_res.json()
    
    # 3. MCPHub DB에 사용자 등록/조회 (JIT Provisioning)
    user = await find_or_create_user(kauth_user)
    
    # 4. MCPHub 자체 JWT 발급 (kauth_user_id 포함!)
    mcphub_token = create_mcphub_token(
        user_id=user["id"],
        kauth_user_id=kauth_user["sub"],  # ⚠️ 중요: Orchestrator에서 이 값으로 토큰 조회
        email=kauth_user["email"]
    )
    
    # 5. Frontend로 토큰 전달
    return RedirectResponse(url=f"/?token={mcphub_token}")


async def find_or_create_user(kauth_user: dict) -> dict:
    """
    K-Auth 사용자 정보로 MCPHub 사용자 조회 또는 생성
    
    핵심: kauth_user_id (sub) 로 사용자 매칭
    """
    kauth_user_id = kauth_user["sub"]
    email = kauth_user["email"]
    username = kauth_user["username"]
    
    # DB에서 kauth_user_id로 조회
    user = await db.users.find_one({"kauth_user_id": kauth_user_id})
    
    if user:
        return user
    
    # 없으면 새로 생성 (JIT Provisioning)
    new_user = {
        "id": str(uuid.uuid4()),
        "kauth_user_id": kauth_user_id,  # ⚠️ 필수!
        "email": email,
        "username": username,
        "name": kauth_user.get("name", username),
        "auth_provider": "kauth",
        "created_at": datetime.utcnow()
    }
    await db.users.insert_one(new_user)
    
    return new_user
```

### 3.4 Frontend 구현 (React 예시)

**로그인 버튼 추가:**

```jsx
const LoginPage = () => {
  const handleKAuthLogin = () => {
    // Backend의 K-Auth 로그인 엔드포인트로 리다이렉트
    window.location.href = '/auth/kauth';
  };
  
  return (
    <div className="login-container">
      {/* 기존 로그인 폼 */}
      <form>...</form>
      
      {/* K-Auth SSO 버튼 추가 */}
      <div className="sso-divider">OR</div>
      
      <button 
        onClick={handleKAuthLogin}
        className="kauth-login-btn"
      >
        🔐 K-AUTH SSO LOGIN
      </button>
    </div>
  );
};
```

**콜백 처리 (토큰 저장):**

```jsx
// App.jsx 또는 콜백 페이지에서
useEffect(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token');
  
  if (token) {
    localStorage.setItem('mcphub_token', token);
    window.history.replaceState({}, '', '/'); // URL 정리
  }
}, []);
```

---

## 4. 중요: kauth_user_id 활용

### Orchestrator → MCPHub 토큰 조회 흐름

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestrator  │    │     MCPHub      │    │   MCP Server    │
│                 │    │                 │    │   (Jira 등)     │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         │  X-MCPHub-User-Id    │                      │
         │  (kauth_user_id)     │                      │
         │─────────────────────►│                      │
         │                      │                      │
         │                      │ kauth_user_id로      │
         │                      │ 서비스 토큰 조회     │
         │                      │                      │
         │                      │  API 호출 (토큰 적용)│
         │                      │─────────────────────►│
         │                      │                      │
         │                      │◄─────────────────────│
         │◄─────────────────────│                      │
         │                      │                      │
```

### MCPHub DB 스키마 요구사항

**users 테이블:**
```sql
ALTER TABLE users ADD COLUMN kauth_user_id UUID UNIQUE;
ALTER TABLE users ADD COLUMN auth_provider VARCHAR(50) DEFAULT 'local';

-- 인덱스 추가 (성능)
CREATE INDEX idx_users_kauth_user_id ON users(kauth_user_id);
```

**service_tokens 테이블:**
```sql
-- user_id가 kauth_user_id를 참조할 수 있도록 확인
-- Orchestrator가 X-MCPHub-User-Id 헤더로 kauth_user_id를 전달하면
-- MCPHub에서 해당 사용자의 서비스 토큰을 조회해야 함
```

---

## 5. 테스트 체크리스트

### 기능 테스트
- [ ] K-Auth SSO 로그인 버튼 클릭 시 K-Auth 로그인 페이지로 리다이렉트
- [ ] K-Auth 로그인 성공 후 MCPHub로 정상 리다이렉트
- [ ] 최초 로그인 사용자 자동 계정 생성 (JIT Provisioning)
- [ ] 기존 K-Auth 사용자 재로그인 시 기존 계정 연동
- [ ] MCPHub JWT에 kauth_user_id 포함 확인

### 연동 테스트
- [ ] Orchestrator에서 MCPHub 호출 시 X-MCPHub-User-Id 헤더로 토큰 조회 성공
- [ ] Jira/Confluence/GitHub 서비스 토큰 정상 적용

---

## 6. 참고 자료

- **K-Auth OAuth 연동 가이드**: https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/560028699
- **Orchestrator K-Auth 구현 코드**: `backend/app/auth/kauth.py`

---

## 7. 문의

구현 중 이슈가 있으면 Orchestrator 팀에 연락해주세요.

**응답 기한**: 가능한 빨리 (K-Jarvis 1.0 릴리즈 전 완료 필요)

