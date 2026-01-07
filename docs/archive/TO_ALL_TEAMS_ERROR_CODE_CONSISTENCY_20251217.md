# k-arc-utils ↔ k-jarvis-utils 에러 코드 일관성 확인 완료

**작성일**: 2025-12-17  
**작성팀**: K-ARC Team  
**수신팀**: Orchestrator Team, Agent Team  
**상태**: ✅ 일관성 확보 완료

---

## 📋 요청 사항

Orchestrator Team `TO_ALL_TEAMS_PHASE3_START_20251217.md`에서:
> K-ARC Team: k-arc-utils와 에러 코드 일관성 확인

---

## ✅ 에러 코드 일관성 확보 완료

k-arc-utils를 k-jarvis-utils와 호환되도록 업데이트했습니다.

### 변경 커밋

- **GitHub**: https://github.com/OG056501-Opensource-Poc/k-arc-utils
- **커밋**: `35691f4` - "feat: k-jarvis-utils와 에러 코드 일관성 유지"

---

## 📊 에러 코드 매핑 (일관성 확보)

### MCP 에러 코드 (숫자형, JSON-RPC 규약)

| 코드 | k-jarvis-utils (Python) | k-arc-utils (TypeScript) | 설명 |
|------|-------------------------|--------------------------|------|
| -32001 | `NO_SERVICE_TOKEN` | `MCPErrorCode.NO_SERVICE_TOKEN` | 서비스 토큰 없음 |
| -32002 | `TOKEN_EXPIRED` | `MCPErrorCode.TOKEN_EXPIRED` | 토큰 만료 |
| -32003 | `TOKEN_INVALID` | `MCPErrorCode.TOKEN_INVALID` | 유효하지 않은 토큰 |
| -32004 | `SERVER_NOT_FOUND` | `MCPErrorCode.SERVER_NOT_FOUND` | 서버를 찾을 수 없음 |
| -32005 | `TOOL_NOT_FOUND` | `MCPErrorCode.TOOL_NOT_FOUND` | 도구를 찾을 수 없음 |
| -32006 | `EXECUTION_ERROR` | `MCPErrorCode.EXECUTION_ERROR` | 실행 오류 |
| -32007 | `NO_TOOLS_AVAILABLE` | `MCPErrorCode.NO_TOOLS_AVAILABLE` | 사용 가능한 도구 없음 |
| -32008 | `SESSION_EXPIRED` | `MCPErrorCode.SESSION_EXPIRED` | 세션 만료 |

---

## 🔧 k-arc-utils 업데이트 내역

### 1. MCPErrorCode enum 추가 (숫자형)

```typescript
// k-arc-utils (TypeScript)
export enum MCPErrorCode {
  NO_SERVICE_TOKEN = -32001,
  TOKEN_EXPIRED = -32002,
  TOKEN_INVALID = -32003,
  SERVER_NOT_FOUND = -32004,
  TOOL_NOT_FOUND = -32005,
  EXECUTION_ERROR = -32006,
  NO_TOOLS_AVAILABLE = -32007,
  SESSION_EXPIRED = -32008,
}
```

```python
# k-jarvis-utils (Python) - 동일한 값
class MCPErrorCode(IntEnum):
    NO_SERVICE_TOKEN = -32001
    TOKEN_EXPIRED = -32002
    TOKEN_INVALID = -32003
    SERVER_NOT_FOUND = -32004
    TOOL_NOT_FOUND = -32005
    EXECUTION_ERROR = -32006
    NO_TOOLS_AVAILABLE = -32007
    SESSION_EXPIRED = -32008
```

### 2. ErrorCode 별칭 추가

```typescript
export const ErrorCode = {
  // k-jarvis-utils 호환 이름
  NO_SERVICE_TOKEN: 'KARC_NO_SERVICE_TOKEN',
  MISSING_SERVICE_TOKEN: 'KARC_NO_SERVICE_TOKEN', // 별칭
  
  TOKEN_EXPIRED: 'KARC_TOKEN_EXPIRED',
  EXPIRED_SERVICE_TOKEN: 'KARC_TOKEN_EXPIRED', // 별칭
  
  TOKEN_INVALID: 'KARC_TOKEN_INVALID',
  INVALID_SERVICE_TOKEN: 'KARC_TOKEN_INVALID', // 별칭
  
  EXECUTION_ERROR: 'KARC_EXECUTION_ERROR',
  TOOL_EXECUTION_ERROR: 'KARC_EXECUTION_ERROR', // 별칭
  // ...
};
```

### 3. getUserMessage() 메서드 추가

```typescript
// k-arc-utils
const error = new KARCError(ErrorCode.NO_SERVICE_TOKEN, '토큰 없음');
console.log(error.getUserMessage('Confluence', 'http://localhost:5173'));
```

```python
# k-jarvis-utils - 동일한 API
error = MCPError(-32001, "토큰 없음")
print(error.get_user_message(service_name="Confluence", mcphub_url="http://localhost:5173"))
```

**출력** (동일):
```
⚠️ Confluence 서비스 토큰이 등록되지 않았습니다.

해결 방법:
1. K-ARC (http://localhost:5173)에 로그인
2. MCP 카탈로그에서 Confluence 서버 찾기
3. 토큰 등록 후 다시 시도해주세요.
```

### 4. fromResponse() 정적 메서드 추가

```typescript
// k-arc-utils
const error = KARCError.fromResponse({
  error: { code: -32001, message: "No service token" }
});
```

```python
# k-jarvis-utils - 동일한 API
error = MCPError.from_response({
    "error": {"code": -32001, "message": "No service token"}
})
```

### 5. isTokenError() 메서드 추가

```typescript
// k-arc-utils
if (error.isTokenError()) {
  // 토큰 관련 에러 처리
}
```

```python
# k-jarvis-utils - 동일한 API
if error.is_token_error():
    # 토큰 관련 에러 처리
```

---

## 📁 수정된 파일

```
k-arc-utils/src/errors/
├── errorCodes.ts   # MCPErrorCode enum 추가, 매핑 추가
├── KARCError.ts    # getUserMessage, fromResponse, isTokenError 추가
└── index.ts        # 새 export 추가
```

---

## ✅ 호환성 체크리스트

| 항목 | Python | TypeScript | 상태 |
|------|--------|------------|------|
| 에러 코드 값 | ✅ | ✅ | 일치 |
| 에러 코드 이름 | ✅ | ✅ | 일치 |
| 사용자 메시지 템플릿 | ✅ | ✅ | 일치 |
| from_response / fromResponse | ✅ | ✅ | 일치 |
| get_user_message / getUserMessage | ✅ | ✅ | 일치 |
| is_token_error / isTokenError | ✅ | ✅ | 일치 |

---

## 💡 사용 예시 비교

### Python (k-jarvis-utils)

```python
from k_jarvis_utils.errors import MCPError, MCPErrorCode, MCPErrorHandler

handler = MCPErrorHandler(mcphub_url="http://localhost:5173")

@handler.wrap(service_name="Confluence")
async def search_confluence(query: str):
    try:
        result = await mcp.call_tool(...)
        return result
    except MCPError as e:
        if e.is_token_error():
            return e.get_user_message(service_name="Confluence")
        raise
```

### TypeScript (k-arc-utils)

```typescript
import { KARCError, ErrorCode, MCPErrorCode } from '@og056501-opensource-poc/k-arc-utils';

async function searchConfluence(query: string) {
  try {
    const result = await mcp.callTool(...);
    return result;
  } catch (error) {
    if (error instanceof KARCError && error.isTokenError()) {
      return error.getUserMessage('Confluence', 'http://localhost:5173');
    }
    throw error;
  }
}
```

---

## 📞 문의

추가 일관성 요청사항이 있으면 언제든 문서로 공유해주세요!

---

**K-ARC Team** 🌀


