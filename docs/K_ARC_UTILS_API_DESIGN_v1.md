# k-arc-utils API 설계 문서 v1.0

**작성일**: 2025-12-17  
**작성팀**: K-ARC Team  
**상태**: Phase 2 - 설계

---

## 📋 개요

### 패키지 정보

| 항목 | 값 |
|------|-----|
| **패키지명** | `@k-arc/utils` |
| **언어** | TypeScript |
| **대상** | MCP 서버 개발자 |
| **배포** | npm (공개) |

### 설계 원칙

1. **Thin Wrapper**: MCP 프로토콜 래핑 안함, K-ARC 특화 기능만
2. **Type-Safe**: 모든 API에 완전한 TypeScript 타입 제공
3. **Zero Dependencies**: 최소 의존성 (런타임 의존성 최소화)
4. **Tree-Shakable**: 사용하는 기능만 번들에 포함

---

## 📦 패키지 구조

```
@k-arc/utils/
├── src/
│   ├── index.ts                    # 메인 진입점
│   ├── headers/
│   │   ├── index.ts
│   │   ├── extractServiceTokens.ts
│   │   ├── getMCPHubUserId.ts
│   │   ├── createUserContext.ts
│   │   └── types.ts
│   ├── client/
│   │   ├── index.ts
│   │   ├── KARCClient.ts
│   │   └── types.ts
│   ├── validation/
│   │   ├── index.ts
│   │   ├── envSchema.ts
│   │   ├── serverConfig.ts
│   │   └── types.ts
│   ├── errors/
│   │   ├── index.ts
│   │   ├── KARCError.ts
│   │   └── errorCodes.ts
│   └── types/
│       ├── index.ts
│       ├── common.ts
│       └── mcp.ts
├── package.json
├── tsconfig.json
├── README.md
└── LICENSE
```

---

## 🔧 API 상세 설계

### 1. Headers Module (`@k-arc/utils/headers`)

#### 1.1 `extractServiceTokens`

MCP 서버로 전달된 서비스 토큰을 추출합니다.

```typescript
/**
 * HTTP 요청 헤더에서 서비스 토큰을 추출합니다.
 * K-ARC Gateway가 X-Service-Tokens 헤더로 전달한 토큰을 파싱합니다.
 * 
 * @param headers - HTTP 요청 헤더 객체
 * @returns 서비스 토큰 객체 (키-값 쌍)
 * 
 * @example
 * ```typescript
 * import { extractServiceTokens } from '@k-arc/utils';
 * 
 * app.post('/mcp', (req, res) => {
 *   const tokens = extractServiceTokens(req.headers);
 *   // tokens: { JIRA_TOKEN: '...', JIRA_EMAIL: '...', JIRA_URL: '...' }
 *   
 *   const jiraClient = new JiraClient({
 *     token: tokens.JIRA_TOKEN,
 *     email: tokens.JIRA_EMAIL,
 *     url: tokens.JIRA_URL,
 *   });
 * });
 * ```
 */
export function extractServiceTokens(
  headers: IncomingHttpHeaders | Headers
): ServiceTokens;

// 타입 정의
export interface ServiceTokens {
  [key: string]: string | undefined;
}
```

**구현 로직**:
```typescript
export function extractServiceTokens(
  headers: IncomingHttpHeaders | Headers
): ServiceTokens {
  // 1. 헤더에서 X-Service-Tokens 추출
  const tokenHeader = getHeader(headers, 'x-service-tokens');
  
  if (!tokenHeader) {
    return {};
  }
  
  // 2. Base64 디코딩 (인코딩된 경우)
  const decoded = isBase64(tokenHeader) 
    ? Buffer.from(tokenHeader, 'base64').toString('utf-8')
    : tokenHeader;
  
  // 3. JSON 파싱
  try {
    return JSON.parse(decoded);
  } catch {
    // 4. URL-encoded 형식 파싱 (fallback)
    return parseUrlEncoded(decoded);
  }
}
```

---

#### 1.2 `getMCPHubUserId`

요청한 사용자의 MCPHub User ID를 추출합니다.

```typescript
/**
 * HTTP 요청 헤더에서 MCPHub 사용자 ID를 추출합니다.
 * K-ARC Gateway가 인증된 사용자 정보를 X-MCPHub-User-Id 헤더로 전달합니다.
 * 
 * @param headers - HTTP 요청 헤더 객체
 * @returns MCPHub 사용자 ID 또는 undefined
 * 
 * @example
 * ```typescript
 * import { getMCPHubUserId } from '@k-arc/utils';
 * 
 * app.post('/mcp', (req, res) => {
 *   const userId = getMCPHubUserId(req.headers);
 *   if (!userId) {
 *     throw new KARCError('UNAUTHORIZED', '사용자 인증 필요');
 *   }
 *   
 *   // 사용자별 로깅, 권한 확인 등
 *   logger.info(`User ${userId} called tool`);
 * });
 * ```
 */
export function getMCPHubUserId(
  headers: IncomingHttpHeaders | Headers
): string | undefined;
```

---

#### 1.3 `createUserContext`

사용자 컨텍스트 객체를 생성합니다.

```typescript
/**
 * HTTP 요청 헤더에서 전체 사용자 컨텍스트를 추출합니다.
 * 서비스 토큰, 사용자 ID, 요청 메타데이터를 포함합니다.
 * 
 * @param headers - HTTP 요청 헤더 객체
 * @returns 사용자 컨텍스트 객체
 * 
 * @example
 * ```typescript
 * import { createUserContext } from '@k-arc/utils';
 * 
 * app.post('/mcp', (req, res) => {
 *   const context = createUserContext(req.headers);
 *   
 *   // context.userId: 사용자 ID
 *   // context.serviceTokens: 서비스 토큰들
 *   // context.requestId: 요청 추적 ID
 *   // context.kauthUserId: K-Auth 사용자 ID (있는 경우)
 * });
 * ```
 */
export function createUserContext(
  headers: IncomingHttpHeaders | Headers
): UserContext;

// 타입 정의
export interface UserContext {
  /** MCPHub 사용자 ID */
  userId?: string;
  
  /** K-Auth 사용자 ID (SSO 로그인 시) */
  kauthUserId?: string;
  
  /** 서비스 토큰 (환경변수) */
  serviceTokens: ServiceTokens;
  
  /** 요청 추적 ID */
  requestId?: string;
  
  /** 요청 타임스탬프 */
  timestamp: Date;
  
  /** 원본 헤더 (필요시 추가 정보 접근) */
  rawHeaders: Record<string, string>;
}
```

---

### 2. Client Module (`@k-arc/utils/client`)

#### 2.1 `KARCClient`

K-ARC Gateway와 통신하는 클라이언트입니다.

```typescript
/**
 * K-ARC Gateway와 통신하는 클라이언트.
 * MCP 서버에서 다른 MCP 서버의 도구를 호출할 때 사용합니다.
 * 
 * @example
 * ```typescript
 * import { KARCClient } from '@k-arc/utils';
 * 
 * // 클라이언트 생성
 * const karc = new KARCClient({
 *   baseUrl: process.env.KARC_URL || 'https://k-arc.example.com',
 *   apiKey: process.env.MCPHUB_API_KEY,
 * });
 * 
 * // 도구 호출
 * const result = await karc.callTool('jira-server', 'search', {
 *   jql: 'project = PROJ',
 *   limit: 10,
 * });
 * 
 * // 도구 목록 조회
 * const tools = await karc.listTools('jira-server');
 * ```
 */
export class KARCClient {
  constructor(options: KARCClientOptions);
  
  /**
   * MCP 서버의 도구를 호출합니다.
   * 
   * @param serverName - MCP 서버 이름
   * @param toolName - 도구 이름
   * @param args - 도구 인자
   * @param options - 호출 옵션 (타임아웃 등)
   * @returns 도구 실행 결과
   */
  async callTool<T = unknown>(
    serverName: string,
    toolName: string,
    args: Record<string, unknown>,
    options?: CallToolOptions
  ): Promise<ToolResult<T>>;
  
  /**
   * MCP 서버의 도구 목록을 조회합니다.
   * 
   * @param serverName - MCP 서버 이름
   * @returns 도구 목록
   */
  async listTools(serverName: string): Promise<Tool[]>;
  
  /**
   * 사용 가능한 MCP 서버 목록을 조회합니다.
   * 
   * @returns MCP 서버 목록
   */
  async listServers(): Promise<MCPServer[]>;
  
  /**
   * 연결 상태를 확인합니다.
   * 
   * @returns 연결 상태
   */
  async healthCheck(): Promise<HealthCheckResult>;
}

// 타입 정의
export interface KARCClientOptions {
  /** K-ARC Gateway URL */
  baseUrl: string;
  
  /** MCPHub API Key */
  apiKey: string;
  
  /** 기본 타임아웃 (ms) */
  timeout?: number;
  
  /** 재시도 횟수 */
  retries?: number;
  
  /** 사용자 ID (대리 호출 시) */
  userId?: string;
}

export interface CallToolOptions {
  /** 타임아웃 (ms) */
  timeout?: number;
  
  /** 추가 헤더 */
  headers?: Record<string, string>;
  
  /** 서비스 토큰 전달 */
  serviceTokens?: ServiceTokens;
}

export interface ToolResult<T = unknown> {
  /** 성공 여부 */
  success: boolean;
  
  /** 결과 데이터 */
  data?: T;
  
  /** 에러 정보 */
  error?: {
    code: string;
    message: string;
  };
  
  /** 실행 시간 (ms) */
  duration: number;
}

export interface Tool {
  name: string;
  description: string;
  inputSchema: JsonSchema;
}

export interface MCPServer {
  name: string;
  displayName: string;
  description: string;
  status: 'active' | 'inactive' | 'maintenance';
  tools: Tool[];
}

export interface HealthCheckResult {
  status: 'healthy' | 'unhealthy';
  latency: number;
  timestamp: Date;
}
```

**사용 예시 - MCP 서버 내에서 다른 MCP 도구 호출**:

```typescript
import { KARCClient, createUserContext } from '@k-arc/utils';

// MCP 서버 도구 핸들러 내부
async function handleSearchAndAnalyze(req: Request, args: { query: string }) {
  const context = createUserContext(req.headers);
  
  // K-ARC 클라이언트 생성 (사용자 토큰 전달)
  const karc = new KARCClient({
    baseUrl: process.env.KARC_URL!,
    apiKey: process.env.MCPHUB_API_KEY!,
  });
  
  // 1. Jira에서 이슈 검색
  const jiraResult = await karc.callTool('jira-server', 'search', {
    jql: args.query,
    limit: 10,
  }, {
    serviceTokens: context.serviceTokens, // 사용자 토큰 전달
  });
  
  // 2. Confluence에서 관련 문서 검색
  const confluenceResult = await karc.callTool('confluence-server', 'search', {
    query: args.query,
    limit: 5,
  }, {
    serviceTokens: context.serviceTokens,
  });
  
  // 3. 결과 통합
  return {
    issues: jiraResult.data,
    documents: confluenceResult.data,
  };
}
```

---

### 3. Validation Module (`@k-arc/utils/validation`)

#### 3.1 `validateEnvSchema`

환경변수 스키마를 검증합니다.

```typescript
/**
 * 환경변수 스키마를 정의하고 검증합니다.
 * MCP 서버 시작 시 필수 환경변수가 설정되었는지 확인합니다.
 * 
 * @example
 * ```typescript
 * import { validateEnvSchema, EnvSchema } from '@k-arc/utils';
 * 
 * // 스키마 정의
 * const schema: EnvSchema = {
 *   JIRA_TOKEN: {
 *     type: 'secret',
 *     required: true,
 *     description: 'Jira API 토큰',
 *   },
 *   JIRA_EMAIL: {
 *     type: 'string',
 *     required: true,
 *     description: 'Jira 계정 이메일',
 *     pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
 *   },
 *   JIRA_URL: {
 *     type: 'url',
 *     required: true,
 *     description: 'Jira 인스턴스 URL',
 *   },
 *   MAX_RESULTS: {
 *     type: 'number',
 *     required: false,
 *     default: 100,
 *     min: 1,
 *     max: 1000,
 *   },
 * };
 * 
 * // 검증 실행
 * const result = validateEnvSchema(schema);
 * 
 * if (!result.valid) {
 *   console.error('환경변수 검증 실패:');
 *   result.errors.forEach(e => console.error(`  - ${e.key}: ${e.message}`));
 *   process.exit(1);
 * }
 * 
 * // 검증된 환경변수 사용
 * const { JIRA_TOKEN, JIRA_EMAIL, JIRA_URL, MAX_RESULTS } = result.values;
 * ```
 */
export function validateEnvSchema(
  schema: EnvSchema,
  env?: Record<string, string | undefined>
): EnvValidationResult;

// 타입 정의
export interface EnvSchema {
  [key: string]: EnvVarDefinition;
}

export interface EnvVarDefinition {
  /** 변수 타입 */
  type: 'string' | 'number' | 'boolean' | 'url' | 'secret';
  
  /** 필수 여부 */
  required: boolean;
  
  /** 설명 (문서 생성용) */
  description: string;
  
  /** 기본값 (required가 false일 때) */
  default?: string | number | boolean;
  
  /** 문자열 패턴 (정규식) */
  pattern?: RegExp;
  
  /** 숫자 최소값 */
  min?: number;
  
  /** 숫자 최대값 */
  max?: number;
  
  /** 허용 값 목록 */
  enum?: string[];
}

export interface EnvValidationResult {
  /** 검증 성공 여부 */
  valid: boolean;
  
  /** 검증된 환경변수 값들 */
  values: Record<string, string | number | boolean>;
  
  /** 에러 목록 */
  errors: EnvValidationError[];
  
  /** 경고 목록 */
  warnings: EnvValidationWarning[];
}

export interface EnvValidationError {
  key: string;
  message: string;
  type: 'missing' | 'invalid_type' | 'invalid_pattern' | 'out_of_range';
}

export interface EnvValidationWarning {
  key: string;
  message: string;
}
```

---

#### 3.2 `generateEnvTemplate`

환경변수 템플릿을 생성합니다.

```typescript
/**
 * 환경변수 스키마로부터 .env 파일 템플릿을 생성합니다.
 * 
 * @example
 * ```typescript
 * import { generateEnvTemplate } from '@k-arc/utils';
 * 
 * const template = generateEnvTemplate(schema);
 * console.log(template);
 * // # Jira API 토큰 (필수)
 * // JIRA_TOKEN=
 * // 
 * // # Jira 계정 이메일 (필수)
 * // JIRA_EMAIL=
 * // ...
 * ```
 */
export function generateEnvTemplate(
  schema: EnvSchema,
  options?: GenerateTemplateOptions
): string;

export interface GenerateTemplateOptions {
  /** 주석 포함 여부 */
  includeComments?: boolean;
  
  /** 기본값 포함 여부 */
  includeDefaults?: boolean;
  
  /** 예시 값 포함 여부 */
  includeExamples?: boolean;
}
```

---

#### 3.3 `validateServerConfig`

MCP 서버 설정을 검증합니다.

```typescript
/**
 * MCP 서버 설정 객체를 검증합니다.
 * K-ARC 카탈로그 등록 전 필수 정보 확인용.
 * 
 * @example
 * ```typescript
 * import { validateServerConfig, ServerConfig } from '@k-arc/utils';
 * 
 * const config: ServerConfig = {
 *   name: 'my-mcp-server',
 *   displayName: 'My MCP Server',
 *   description: '데이터 검색 서버',
 *   version: '1.0.0',
 *   url: 'https://my-mcp-server.example.com',
 *   transport: 'http',
 *   envSchema: {
 *     API_KEY: { type: 'secret', required: true, description: 'API Key' },
 *   },
 * };
 * 
 * const result = validateServerConfig(config);
 * if (!result.valid) {
 *   console.error(result.errors);
 * }
 * ```
 */
export function validateServerConfig(
  config: ServerConfig
): ServerConfigValidationResult;

export interface ServerConfig {
  /** 서버 식별자 (영문, 숫자, 하이픈) */
  name: string;
  
  /** 표시 이름 */
  displayName: string;
  
  /** 설명 */
  description: string;
  
  /** 버전 (semver) */
  version: string;
  
  /** 서버 URL */
  url: string;
  
  /** Transport 타입 */
  transport: 'http' | 'sse' | 'stdio';
  
  /** 환경변수 스키마 */
  envSchema?: EnvSchema;
  
  /** 카테고리 */
  category?: string;
  
  /** 태그 */
  tags?: string[];
  
  /** 아이콘 URL */
  iconUrl?: string;
}
```

---

### 4. Errors Module (`@k-arc/utils/errors`)

#### 4.1 `KARCError`

K-ARC 표준 에러 클래스입니다.

```typescript
/**
 * K-ARC 표준 에러 클래스.
 * 에러 코드와 메시지를 표준화합니다.
 * 
 * @example
 * ```typescript
 * import { KARCError, ErrorCode } from '@k-arc/utils';
 * 
 * // 에러 발생
 * throw new KARCError(
 *   ErrorCode.MISSING_SERVICE_TOKEN,
 *   'JIRA_TOKEN 환경변수가 설정되지 않았습니다',
 *   { requiredToken: 'JIRA_TOKEN' }
 * );
 * 
 * // 에러 처리
 * try {
 *   await someOperation();
 * } catch (error) {
 *   if (error instanceof KARCError) {
 *     // K-ARC 표준 에러 응답
 *     return {
 *       error: {
 *         code: error.code,
 *         message: error.message,
 *         details: error.details,
 *       }
 *     };
 *   }
 *   throw error;
 * }
 * ```
 */
export class KARCError extends Error {
  /** 에러 코드 */
  readonly code: string;
  
  /** 추가 상세 정보 */
  readonly details?: Record<string, unknown>;
  
  /** HTTP 상태 코드 */
  readonly statusCode: number;
  
  constructor(
    code: ErrorCode | string,
    message: string,
    details?: Record<string, unknown>
  );
  
  /** JSON 직렬화 */
  toJSON(): KARCErrorJSON;
  
  /** 에러 응답 객체 생성 */
  toResponse(): ErrorResponse;
}

export interface KARCErrorJSON {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ErrorResponse {
  error: KARCErrorJSON;
  statusCode: number;
}
```

---

#### 4.2 `ErrorCode`

표준 에러 코드 상수입니다.

```typescript
/**
 * K-ARC 표준 에러 코드.
 */
export const ErrorCode = {
  // 인증 관련 (4xx)
  UNAUTHORIZED: 'KARC_UNAUTHORIZED',
  INVALID_API_KEY: 'KARC_INVALID_API_KEY',
  EXPIRED_API_KEY: 'KARC_EXPIRED_API_KEY',
  
  // 서비스 토큰 관련
  MISSING_SERVICE_TOKEN: 'KARC_MISSING_SERVICE_TOKEN',
  INVALID_SERVICE_TOKEN: 'KARC_INVALID_SERVICE_TOKEN',
  EXPIRED_SERVICE_TOKEN: 'KARC_EXPIRED_SERVICE_TOKEN',
  
  // 서버 관련
  SERVER_NOT_FOUND: 'KARC_SERVER_NOT_FOUND',
  SERVER_UNAVAILABLE: 'KARC_SERVER_UNAVAILABLE',
  SERVER_TIMEOUT: 'KARC_SERVER_TIMEOUT',
  
  // 도구 관련
  TOOL_NOT_FOUND: 'KARC_TOOL_NOT_FOUND',
  TOOL_EXECUTION_ERROR: 'KARC_TOOL_EXECUTION_ERROR',
  INVALID_TOOL_ARGUMENTS: 'KARC_INVALID_TOOL_ARGUMENTS',
  
  // 요청 관련
  INVALID_REQUEST: 'KARC_INVALID_REQUEST',
  RATE_LIMITED: 'KARC_RATE_LIMITED',
  
  // 시스템 관련
  INTERNAL_ERROR: 'KARC_INTERNAL_ERROR',
  CONFIGURATION_ERROR: 'KARC_CONFIGURATION_ERROR',
} as const;

export type ErrorCode = typeof ErrorCode[keyof typeof ErrorCode];

/**
 * 에러 코드별 HTTP 상태 코드 매핑
 */
export const ErrorStatusMap: Record<ErrorCode, number> = {
  [ErrorCode.UNAUTHORIZED]: 401,
  [ErrorCode.INVALID_API_KEY]: 401,
  [ErrorCode.EXPIRED_API_KEY]: 401,
  [ErrorCode.MISSING_SERVICE_TOKEN]: 400,
  [ErrorCode.INVALID_SERVICE_TOKEN]: 400,
  [ErrorCode.EXPIRED_SERVICE_TOKEN]: 401,
  [ErrorCode.SERVER_NOT_FOUND]: 404,
  [ErrorCode.SERVER_UNAVAILABLE]: 503,
  [ErrorCode.SERVER_TIMEOUT]: 504,
  [ErrorCode.TOOL_NOT_FOUND]: 404,
  [ErrorCode.TOOL_EXECUTION_ERROR]: 500,
  [ErrorCode.INVALID_TOOL_ARGUMENTS]: 400,
  [ErrorCode.INVALID_REQUEST]: 400,
  [ErrorCode.RATE_LIMITED]: 429,
  [ErrorCode.INTERNAL_ERROR]: 500,
  [ErrorCode.CONFIGURATION_ERROR]: 500,
};
```

---

## 📝 사용 예시

### 완전한 MCP 서버 예시

```typescript
import express from 'express';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { 
  createUserContext, 
  validateEnvSchema, 
  KARCError, 
  ErrorCode,
  EnvSchema 
} from '@k-arc/utils';

// 1. 환경변수 스키마 정의
const envSchema: EnvSchema = {
  JIRA_TOKEN: { type: 'secret', required: true, description: 'Jira API 토큰' },
  JIRA_EMAIL: { type: 'string', required: true, description: 'Jira 이메일' },
  JIRA_URL: { type: 'url', required: true, description: 'Jira URL' },
};

// 2. 환경변수 검증
const envResult = validateEnvSchema(envSchema);
if (!envResult.valid) {
  console.error('환경변수 검증 실패:', envResult.errors);
  process.exit(1);
}

const app = express();
app.use(express.json());

// 3. MCP 엔드포인트
app.post('/mcp', async (req, res) => {
  try {
    // 4. 사용자 컨텍스트 추출
    const context = createUserContext(req.headers);
    
    if (!context.userId) {
      throw new KARCError(
        ErrorCode.UNAUTHORIZED,
        '사용자 인증이 필요합니다'
      );
    }
    
    // 5. 서비스 토큰 확인
    const { JIRA_TOKEN, JIRA_EMAIL, JIRA_URL } = context.serviceTokens;
    
    if (!JIRA_TOKEN || !JIRA_EMAIL || !JIRA_URL) {
      throw new KARCError(
        ErrorCode.MISSING_SERVICE_TOKEN,
        'Jira 서비스 토큰이 설정되지 않았습니다',
        { 
          required: ['JIRA_TOKEN', 'JIRA_EMAIL', 'JIRA_URL'],
          provided: Object.keys(context.serviceTokens),
        }
      );
    }
    
    // 6. MCP 요청 처리
    const { method, params } = req.body;
    
    if (method === 'tools/list') {
      return res.json({
        tools: [
          {
            name: 'search',
            description: 'Jira 이슈 검색',
            inputSchema: { /* ... */ },
          },
        ],
      });
    }
    
    if (method === 'tools/call') {
      const result = await handleToolCall(params, {
        jiraToken: JIRA_TOKEN,
        jiraEmail: JIRA_EMAIL,
        jiraUrl: JIRA_URL,
      });
      return res.json(result);
    }
    
    res.status(400).json({ error: 'Unknown method' });
    
  } catch (error) {
    if (error instanceof KARCError) {
      return res.status(error.statusCode).json(error.toResponse());
    }
    
    console.error('Unexpected error:', error);
    res.status(500).json({
      error: {
        code: ErrorCode.INTERNAL_ERROR,
        message: '서버 내부 오류가 발생했습니다',
      },
    });
  }
});

app.listen(8080, () => {
  console.log('MCP Server running on :8080');
});
```

---

## 📊 API 요약 테이블

| 모듈 | 함수/클래스 | 용도 |
|------|------------|------|
| **headers** | `extractServiceTokens` | 서비스 토큰 추출 |
| | `getMCPHubUserId` | 사용자 ID 추출 |
| | `createUserContext` | 전체 컨텍스트 생성 |
| **client** | `KARCClient` | K-ARC Gateway 클라이언트 |
| **validation** | `validateEnvSchema` | 환경변수 검증 |
| | `generateEnvTemplate` | .env 템플릿 생성 |
| | `validateServerConfig` | 서버 설정 검증 |
| **errors** | `KARCError` | 표준 에러 클래스 |
| | `ErrorCode` | 에러 코드 상수 |

---

## 🗓️ 다음 단계

### Phase 3: 개발

- [ ] `@k-arc/utils` 프로토타입 구현
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 (K-ARC Gateway 연동)

### Phase 4: 테스트

- [ ] 기존 MCP 서버에 적용 테스트
- [ ] 신규 MCP 서버 개발 테스트

### Phase 5: 배포

- [ ] npm 배포 (`@k-arc/utils`)
- [ ] 문서 공개

---

**K-ARC Team** 🌀


