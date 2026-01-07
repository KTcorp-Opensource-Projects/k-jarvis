# MCPHub Stateless 아키텍처 전환 제안에 대한 응답

**작성일**: 2025-12-29  
**작성팀**: Orchestrator Team (K-Auth 담당 포함)  
**대상**: K-ARC (MCPHub) Team  
**상태**: ✅ **동의 및 지지**

---

## 📌 전체 의견

**Stateless 아키텍처 전환에 동의합니다.**

운영 복잡도 감소, Scale-out 용이성, 장애 복구 개선 등 제안하신 장점에 전적으로 공감합니다.  
K-Auth 및 Orchestrator 관점에서도 Stateless 전환이 더 적합합니다.

---

## ❓ 질문에 대한 답변

### 1. K-Auth SSO 연동에서 세션 관련 의존성이 있나요?

**아니오, 의존성이 없습니다.**

K-Auth는 **JWT 기반 Stateless 인증**을 사용합니다:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────>│   K-Auth    │────>│   MCPHub    │
│             │     │ (JWT 발급)  │     │ (JWT 검증)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    JWT Token (Self-contained)
                    - user_id
                    - kauth_user_id
                    - exp (만료시간)
                    - scopes
```

**K-Auth의 인증 방식:**
- Access Token: JWT (Stateless) - 15분~1시간 유효
- Refresh Token: DB 저장 (Stateful) - K-Auth 내부에서만 관리
- MCPHub는 Access Token만 검증하면 됨

**결론**: MCPHub가 Stateless로 전환해도 K-Auth SSO 연동에 영향 없음

---

### 2. Stateless 전환 시 K-Auth 측에서 고려할 사항이 있나요?

**몇 가지 권장사항이 있습니다:**

#### 2.1. JWT 검증 방식

```typescript
// 권장: 매 요청마다 JWT 검증 (Stateless)
const verifyToken = async (token: string) => {
    // 1. JWT 서명 검증 (K-Auth 공개키 사용)
    const decoded = jwt.verify(token, KAUTH_PUBLIC_KEY);
    
    // 2. 만료 시간 확인
    if (decoded.exp < Date.now() / 1000) {
        throw new Error('Token expired');
    }
    
    // 3. (선택) K-Auth에 토큰 유효성 확인
    // await kauth.introspect(token);  // 필요시에만
    
    return decoded;
};
```

#### 2.2. 토큰 캐싱 (성능 최적화)

```typescript
// Redis에 검증된 토큰 캐싱 (선택적)
const cachedVerify = async (token: string) => {
    const cacheKey = `token:${hash(token)}`;
    
    // 캐시 확인
    const cached = await redis.get(cacheKey);
    if (cached) return JSON.parse(cached);
    
    // 검증 후 캐싱 (TTL: 토큰 남은 유효시간)
    const decoded = await verifyToken(token);
    const ttl = decoded.exp - Math.floor(Date.now() / 1000);
    await redis.setex(cacheKey, ttl, JSON.stringify(decoded));
    
    return decoded;
};
```

#### 2.3. MCPHub Key와 K-Auth 토큰 관계

현재 MCPHub Key 기반 인증을 사용 중이신 것으로 알고 있습니다:

```
Agent → MCPHub (Authorization: Bearer mcphub_xxx)
```

K-Auth SSO 연동 시에도 MCPHub Key 방식을 유지하시면 됩니다:
- MCPHub Key는 사용자별로 발급
- MCPHub Key에 `kauth_user_id` 연결
- K-Auth 세션과 독립적으로 동작

---

## ✅ Orchestrator 관점

### 현재 연동 방식

```
사용자 요청 → Orchestrator → Agent → MCPHub → MCP Server
                   │
                   └─ X-MCPHub-User-Id 헤더로 사용자 식별
```

### Stateless 전환 시 변경 사항

**변경 없음!**

Orchestrator는 이미 Stateless 방식으로 MCPHub와 통신합니다:
- 매 요청마다 `X-MCPHub-User-Id` 헤더 전송
- MCPHub 세션에 의존하지 않음
- Agent도 마찬가지로 MCPHub Key 기반 인증

---

## 📋 추가 의견

### 1. 동의하는 부분

| 항목 | 의견 |
|------|------|
| 세션 코드 제거 | ✅ 운영 복잡도 대폭 감소 |
| Scale-out 용이성 | ✅ Load Balancer Round-Robin 가능 |
| 장애 복구 | ✅ 노드 장애 시 영향 최소화 |
| `tools/list`, `tools/call` 지원 | ✅ 에이전트 핵심 기능 충분 |

### 2. 우려 사항 (경미)

| 항목 | 우려 | 대안 |
|------|------|------|
| 장기 실행 작업 | 30초+ 작업 타임아웃 | 비동기 작업 큐 도입 (필요시) |
| Server→Client 알림 | 실시간 알림 불가 | Polling 또는 WebSocket 별도 구현 |

### 3. 제안 사항

#### 3.1. 연결 풀 관리

Stateless여도 업스트림 MCP Server 연결 풀(`serverInfos`)은 유지하시는 것이 좋습니다:

```typescript
// 공유 연결 풀 (Stateless와 무관)
const serverInfos: Map<string, {
    client: MCPClient,
    tools: Tool[],
    lastConnected: Date
}> = new Map();
```

#### 3.2. Rate Limiting

Stateless 환경에서는 Rate Limiting이 더 중요합니다:

```typescript
// Redis 기반 Rate Limiting 권장
const rateLimit = async (userId: string, limit: number, window: number) => {
    const key = `rate:${userId}`;
    const count = await redis.incr(key);
    if (count === 1) await redis.expire(key, window);
    return count <= limit;
};
```

---

## 📅 일정 관련

제안하신 일정에 동의합니다:

| Phase | 기간 | 내용 |
|-------|------|------|
| Phase 1 | 1주 | 핵심 Stateless 전환 |
| Phase 2 | 3일 | 세션 코드 제거 |
| Phase 3 | 1주 | 테스트 및 검증 |

**Orchestrator 팀 지원 가능 사항:**
- Phase 3에서 E2E 통합 테스트 참여
- K-Auth 연동 테스트 지원

---

## 📞 결론

**Stateless 아키텍처 전환에 적극 동의합니다.**

K-Auth와 Orchestrator 모두 이미 Stateless 방식으로 설계되어 있어  
MCPHub의 Stateless 전환이 전체 시스템 일관성을 높여줄 것으로 기대합니다.

추가 논의가 필요하시면 언제든 연락주세요!

---

**Orchestrator Team 드림** 🚀

