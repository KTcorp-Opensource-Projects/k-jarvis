# K-ARC Utils API 설계 리뷰 피드백

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team  
**수신팀**: K-ARC Team

---

## ✅ 전체 평가: **훌륭합니다!** ⭐⭐⭐⭐⭐

K-ARC Team의 API 설계가 매우 상세하고 체계적입니다.

---

## 👍 좋은 점

### 1. 완전한 TypeScript 타입 정의
```typescript
// 모든 인터페이스가 명확하게 정의됨
export interface UserContext {
  userId?: string;
  kauthUserId?: string;
  serviceTokens: ServiceTokens;
  requestId?: string;
  timestamp: Date;
  rawHeaders: Record<string, string>;
}
```

### 2. 환경변수 검증 시스템
```typescript
// MCP 서버 시작 시 필수 검증 - 훌륭한 DX
const result = validateEnvSchema(schema);
if (!result.valid) {
  console.error(result.errors);
  process.exit(1);
}
```
→ **k-jarvis-utils에도 유사한 기능 추가 검토**

### 3. 에러 코드 표준화
```typescript
export const ErrorCode = {
  MISSING_SERVICE_TOKEN: 'KARC_MISSING_SERVICE_TOKEN',
  // ...
};
```
→ **JSON-RPC 에러 코드(-32001 등)와 매핑 필요**

### 4. 완전한 MCP 서버 예시
→ 새로운 MCP 서버 개발자에게 매우 유용

---

## 💬 피드백 & 제안

### 1. 에러 코드 매핑 필요

**현재 문제**: 
- K-ARC: `KARC_MISSING_SERVICE_TOKEN` (문자열)
- 기존 시스템: `-32001` (JSON-RPC 숫자 코드)

**제안**:
```typescript
// ErrorCode에 JSON-RPC 코드 매핑 추가
export const ErrorCode = {
  MISSING_SERVICE_TOKEN: 'KARC_MISSING_SERVICE_TOKEN',
  // ...
};

// JSON-RPC 매핑 추가
export const JsonRpcErrorMap: Record<ErrorCode, number> = {
  [ErrorCode.MISSING_SERVICE_TOKEN]: -32001,
  [ErrorCode.EXPIRED_SERVICE_TOKEN]: -32002,
  [ErrorCode.INVALID_SERVICE_TOKEN]: -32003,
  // ...
};
```

### 2. k-jarvis-utils와의 일관성

| k-jarvis-utils | k-arc-utils | 제안 |
|---------------|-------------|------|
| `KJarvisHeaders` | `createUserContext` | ✅ 다른 접근, 괜찮음 |
| `MCPHubClient` | `KARCClient` | ✅ 동일한 역할 |
| `MCPError` | `KARCError` | 🔄 에러 코드 형식 통일 제안 |

### 3. K-Auth 연동 고려

```typescript
export interface UserContext {
  userId?: string;           // MCPHub User ID
  kauthUserId?: string;      // ✅ K-Auth User ID 포함됨
  // ...
}
```
→ **잘 반영됨!**

---

## 🔗 k-jarvis-contracts 스키마 연동

### 공통 타입 정의 (제안)

```yaml
# k-jarvis-contracts/schemas/common.yaml

ServiceTokens:
  type: object
  additionalProperties:
    type: string
  description: 서비스 토큰 키-값 쌍

UserContext:
  type: object
  properties:
    userId:
      type: string
    kauthUserId:
      type: string
    serviceTokens:
      $ref: '#/ServiceTokens'
    requestId:
      type: string
    timestamp:
      type: string
      format: date-time

ErrorResponse:
  type: object
  required:
    - error
  properties:
    error:
      type: object
      required:
        - code
        - message
      properties:
        code:
          type: string
        message:
          type: string
        details:
          type: object
```

K-ARC Team에서 위 스키마를 리뷰해주시고, `k-jarvis-contracts`에 기여 부탁드립니다.

---

## ✅ 결론

| 항목 | 평가 |
|------|------|
| API 설계 | ⭐⭐⭐⭐⭐ 훌륭 |
| 타입 정의 | ⭐⭐⭐⭐⭐ 완벽 |
| 문서화 | ⭐⭐⭐⭐⭐ 상세 |
| 일관성 | ⭐⭐⭐⭐ (에러 코드 매핑 추가 필요) |

**Phase 3 (개발) 진행 승인!** 🚀

---

## 📋 체크리스트 업데이트

```markdown
### K-ARC Team
- [x] k-arc-utils API 설계 v1 ✅
- [ ] 에러 코드 JSON-RPC 매핑 추가
- [ ] k-jarvis-contracts 스키마 기여
- [ ] Phase 3: 프로토타입 개발 시작
```

---

**Orchestrator Team**

