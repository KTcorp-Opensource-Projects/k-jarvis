# [K-ARC Team] SDK 전략 의견

**작성일**: 2025-12-17  
**작성팀**: K-ARC Team (구 MCPHub Team)  
**수신팀**: Orchestrator Team, Agent Team

---

## 1. 선호 Option

- [ ] A. Full SDK
- [x] **B. Thin Wrapper** ⭐ (MCP 측면)
- [ ] C. Template/Generator
- [ ] D. Builder Only
- [x] **E. Hybrid (B+D)** ⭐ (장기적 방향)

**결론**: 당장은 **Option B (Thin Wrapper)**, 장기적으로 **Option E (Hybrid)** 추진

---

## 2. 선택 이유

### 2.1 Full SDK를 권장하지 않는 이유

```
MCP Protocol 버전 히스토리 (2024년 기준):
- 2024-11-05: MCP 공개 발표
- 이후 빠르게 버전 업데이트 진행 중
- @modelcontextprotocol/sdk: v0.5.0 → v0.6.0 → v1.0.0 (활발한 업데이트)
```

**Anthropic이 MCP를 활발히 개선 중**이므로:
- Full SDK로 래핑 시 버전 추적 부담이 현실적으로 큼
- 공식 SDK가 이미 잘 만들어져 있음
- 우리가 추가해야 할 건 **K-Jarvis 플랫폼 특화 기능**뿐

### 2.2 Thin Wrapper가 적합한 이유

**K-ARC가 제공해야 할 핵심 기능**:

```typescript
// k-arc-utils (Thin Wrapper)

// 1. 서비스 토큰 처리
export function extractServiceTokens(headers: Headers): ServiceTokens;
export function injectServiceTokens(request: Request, tokens: ServiceTokens): void;

// 2. 사용자 컨텍스트
export function getMCPHubUserId(headers: Headers): string;
export function createUserContext(headers: Headers): UserContext;

// 3. K-ARC 연동
export class KARCClient {
  constructor(baseUrl: string, apiKey: string);
  async callTool(serverName: string, toolName: string, args: object): Promise<ToolResult>;
  async listTools(serverName: string): Promise<Tool[]>;
}

// 4. 환경변수 스키마 검증
export function validateEnvSchema(schema: EnvSchema): ValidationResult;
export function generateEnvTemplate(schema: EnvSchema): string;

// 5. 표준 에러 처리
export class KARCError extends Error {
  constructor(code: string, message: string, details?: object);
}
```

**위 기능들은 MCP 프로토콜 버전과 무관**합니다:
- 공식 MCP SDK가 프로토콜 처리
- K-ARC Utils는 플랫폼 연동만 담당
- MCP 버전 업데이트 → 공식 SDK만 업데이트하면 됨

### 2.3 Builder는 나중에

**현재 상황**:
- MCP 서버 개발자는 대부분 전문 개발자
- 노코드 빌더 수요는 아직 검증 안 됨

**제안**:
- Phase 1: Thin Wrapper 먼저 (즉시)
- Phase 2: 사용자 피드백 후 Builder 검토 (Q1 2025)

---

## 3. 외부 프로토콜 버전 관리 의견

### MCP 버전 변경 빈도 경험

| 항목 | 상태 |
|------|------|
| MCP 프로토콜 | 활발히 업데이트 중 (신규 프로토콜) |
| @modelcontextprotocol/sdk | 주 1-2회 업데이트 |
| Breaking Changes | 아직 드물지만 예상됨 |

### 버전 추적 부담에 대한 의견

**K-ARC 관점에서 2가지 레이어**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        K-ARC Gateway                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            Layer 1: 프로토콜 처리 (K-ARC 내부)          │   │
│  │                                                          │   │
│  │  • MCP 클라이언트 연결 처리                             │   │
│  │  • 도구 목록/호출 라우팅                                │   │
│  │  • 세션 관리                                            │   │
│  │                                                          │   │
│  │  → 공식 SDK 사용 (@modelcontextprotocol/sdk)            │   │
│  │  → MCP 버전 업데이트는 K-ARC만 업데이트하면 됨!         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          Layer 2: Upstream MCP 서버 통신 (HTTP)         │   │
│  │                                                          │   │
│  │  • HTTP + JSON 기반 통신                                │   │
│  │  • 서비스 토큰 전파                                     │   │
│  │  • 에러 변환                                            │   │
│  │                                                          │   │
│  │  → HTTP 기반이라 프로토콜 변경 영향 적음                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**결론**: 
- MCP 프로토콜 버전 변경 시 **K-ARC만 업데이트하면 됨**
- Upstream MCP 서버들은 HTTP API 기반이라 영향 최소화
- **k-arc-mcp-sdk로 Full 래핑할 필요 없음** → Thin Wrapper 충분

---

## 4. 유지보수 참여 의향

- [x] **제한적 참여 가능**

### 참여 가능 범위

| 항목 | 참여 수준 |
|------|----------|
| k-arc-utils (Thin Wrapper) | ✅ 주도 개발 |
| k-jarvis-contracts MCP 스키마 | ✅ 적극 기여 |
| Agent SDK 유지보수 | ❌ 참여 어려움 |
| Builder UI 개발 | ⚠️ 제한적 (K-ARC Portal 확장 형태로) |

### 이유

- K-ARC 팀 리소스는 **K-ARC Gateway 운영 및 고도화**에 집중
- MCP 관련 유틸리티는 담당 가능하나, Agent SDK는 Orchestrator/Agent 팀이 더 적합
- Builder는 K-ARC 관리자 포털에 **MCP 서버 간편 등록** 기능으로 추가 가능

---

## 5. 추가 의견

### 5.1 k-arc-utils 패키지 구조 제안

```
@k-arc/utils/
├── headers/
│   ├── extractServiceTokens.ts
│   ├── getMCPHubUserId.ts
│   └── createUserContext.ts
├── client/
│   └── KARCClient.ts
├── validation/
│   ├── envSchema.ts
│   └── serverConfig.ts
├── errors/
│   └── KARCError.ts
└── index.ts
```

### 5.2 TypeScript vs Python

| 버전 | 제안 |
|------|------|
| **TypeScript** | K-ARC 팀 주도 (K-ARC 백엔드가 TS 기반) |
| **Python** | Agent 팀 피드백 후 결정 |

Python 버전이 필요하면 Orchestrator 팀과 협업하여 개발.

### 5.3 체크리스트 기반 진행 동의

날짜별 일정보다 체크리스트 기반이 현실적입니다.

**K-ARC 팀 체크리스트**:

```markdown
### Phase 1: 전략 확정
- [x] SDK 전략 의견 제출 ← 완료
- [ ] 팀 간 합의

### Phase 2: 설계
- [ ] k-arc-utils 인터페이스 설계
- [ ] k-jarvis-contracts MCP 스키마 기여

### Phase 3: 개발
- [ ] k-arc-utils 프로토타입 (TypeScript)
- [ ] 문서화

### Phase 4: 테스트
- [ ] 기존 MCP 서버에 적용 테스트
- [ ] 신규 MCP 서버 개발 테스트

### Phase 5: 배포
- [ ] npm 배포 (@k-arc/utils)
- [ ] 문서 공개
```

---

## 6. 최종 요약

| 항목 | K-ARC 의견 |
|------|-----------|
| **선호 Option** | B (Thin Wrapper) + 장기적 E (Hybrid) |
| **핵심 이유** | MCP 버전 추적은 K-ARC Gateway가 흡수, SDK는 플랫폼 기능만 |
| **담당 범위** | k-arc-utils (TS) 주도, 스키마 기여, Builder 제한적 |
| **일정 방식** | 체크리스트 기반 동의 |

---

**K-ARC Team** 🌀


