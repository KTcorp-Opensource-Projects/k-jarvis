# Option C 구현 상태 보고서

**작성일**: 2024-12-12
**작성팀**: Orchestrator Team

---

## 📋 구현 완료 항목

### 1. JWT 토큰에 kauth_user_id 포함 ✅

**파일**: `backend/app/auth/service.py`

```python
token_data = {
    "sub": str(user.id),
    "email": user.email,
    "role": user.role_name,
    "kauth_user_id": user.kauth_user_id  # K-Auth user ID for MCPHub
}
```

### 2. Agent 호출 시 X-MCPHub-User-Id 헤더 전달 ✅

**파일**: `backend/app/orchestrator.py`

```python
# Build headers
headers = {
    "Content-Type": "application/json",
    "X-Request-Id": request_id
}

# Add K-Auth User-Id header for MCPHub to apply service tokens
if kauth_user_id:
    headers["X-MCPHub-User-Id"] = kauth_user_id
```

### 3. K-Auth SSO 로그인 플로우 ✅

**확인된 네트워크 흐름**:
1. `GET /auth/kauth` → K-Auth OAuth 시작
2. `GET /oauth/authorize` → K-Auth 로그인 페이지
3. `POST /oauth/authorize/callback` → K-Auth 인증 완료
4. `GET /auth/kauth/callback?code=...` → Orchestrator 콜백
5. `GET /auth/callback?token=...` → Frontend 콜백 (토큰 포함)

**JWT 토큰 예시** (K-Auth SSO 로그인 후):
```json
{
  "sub": "orchadmin",
  "user_id": "2b321734-2939-437b-a143-568a8f261216",
  "kauth_user_id": "131eb74f-a028-48d4-ab33-6f73e5eecafd",
  "is_admin": false,
  "exp": 1765501387,
  "type": "access"
}
```

---

## ⏳ 대기 중인 작업

### 1. Frontend SSO 콜백 토큰 저장 문제

**문제**: `/auth/callback` 라우트에서 URL 파라미터의 토큰을 localStorage에 저장하지 않음

**영향**: K-Auth SSO 로그인 후 UI가 로그인 상태로 전환되지 않음

**해결 방안**: Frontend의 AuthCallback 컴포넌트 수정 필요

---

## 📢 MCPHub 팀 구현 요청사항

### 1. X-MCPHub-User-Id 헤더 처리

Agent로부터 전달되는 `X-MCPHub-User-Id` 헤더를 수신하여:
1. 해당 K-Auth User ID로 사용자 조회
2. 해당 사용자의 서비스 토큰 자동 적용
3. MCP 서버 호출 시 토큰 포함

### 2. 토큰 플로우 예시

```
Orchestrator (User: orchadmin, kauth_user_id: 131eb74f-...)
    ↓ X-MCPHub-User-Id: 131eb74f-...
Agent (Confluence/Jira/GitHub)
    ↓ X-MCPHub-User-Id: 131eb74f-...
MCPHub
    ↓ 사용자별 서비스 토큰 자동 적용
External API (Confluence/Jira/GitHub API)
```

---

## ✅ 테스트 결과

| 항목 | 상태 | 비고 |
|------|------|------|
| K-Auth 사용자 등록 | ✅ | testuser1 등록 완료 |
| K-Auth SSO 로그인 | ✅ | OAuth 플로우 정상 작동 |
| JWT kauth_user_id 포함 | ✅ | 네트워크 로그에서 확인 |
| X-MCPHub-User-Id 헤더 | ✅ | 코드 구현 완료 |
| Agent 등록 및 호출 | ✅ | 3개 Agent 정상 등록 |
| Frontend 토큰 저장 | ❌ | 수정 필요 |

---

## 📝 결론

**Option C (MCPHub-centric proxy) 구현이 완료되었습니다.**

Orchestrator는 K-Auth SSO를 통해 인증된 사용자의 `kauth_user_id`를 Agent 호출 시 `X-MCPHub-User-Id` 헤더로 전달합니다. MCPHub 팀에서 이 헤더를 처리하여 사용자별 서비스 토큰을 자동 적용하면 전체 플로우가 완성됩니다.
