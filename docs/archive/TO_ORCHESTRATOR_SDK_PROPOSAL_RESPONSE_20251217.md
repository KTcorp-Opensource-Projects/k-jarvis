# K-Jarvis SDK 제안에 대한 MCPHub (K-ARC) 팀 응답

**작성일**: 2025-12-17  
**작성팀**: MCPHub (K-ARC) Team  
**수신팀**: Orchestrator Team, Agent Team

---

## 📋 응답 요약

| 항목 | 응답 |
|------|------|
| SDK 개발 동의 | ✅ **동의** |
| 역할 분담 동의 | ✅ **동의 (일부 조정 제안)** |
| 일정 현실성 | ⚠️ **조정 필요** |

---

## 1. ✅ SDK 개발에 동의합니다

### 동의 이유

1. **표준화 필요성 공감**
   - 현재 MCP 서버 개발 시 K-ARC 연동 방법이 문서로만 존재
   - SDK를 통해 표준 준수를 자동화하면 생태계 품질 향상

2. **개발자 경험(DX) 개선**
   - K-ARC에 MCP 서버를 등록하려는 외부 개발자에게 진입 장벽 감소
   - 보일러플레이트 코드 제거로 핵심 비즈니스 로직에 집중 가능

3. **거버넌스 자동 적용**
   - 서비스 토큰 처리, 헤더 전파 등 보안 베스트 프랙티스 강제
   - 프로토콜 버전 업그레이드 시 SDK 업데이트로 일괄 적용

---

## 2. ✅ 역할 분담에 동의합니다 (일부 조정 제안)

### 제안된 역할

| 담당 영역 | MCPHub (K-ARC) Team 역할 |
|----------|-------------------------|
| k-jarvis-contracts | MCP 스키마 기여 |
| k-arc-mcp-sdk | **SDK 핵심 개발** |
| 문서화 | MCP 개발 가이드 |

### 조정 제안

**k-arc-mcp-sdk 공동 개발 제안**:

현재 K-ARC 백엔드가 TypeScript 기반이므로, TypeScript 버전은 K-ARC 팀이 주도하되:

| 버전 | 담당 | 이유 |
|------|------|------|
| **TypeScript** | K-ARC 팀 주도 | K-ARC 내부 코드베이스와 일관성 |
| **Python** | Orchestrator + K-ARC 협업 | Agent 팀 사용 환경 고려 |

---

## 3. 📌 추가 기능 제안

### 3.1 k-arc-mcp-sdk에 포함되어야 할 기능

```typescript
// 제안하는 SDK API 예시

import { MCPServer, Tool, ServiceTokenHandler } from '@k-arc/mcp-sdk';

const server = new MCPServer({
  name: 'my-mcp-server',
  version: '1.0.0',
  // K-ARC 자동 등록 설정
  karc: {
    autoRegister: true,
    serverUrl: 'https://mcp.example.com',
  }
});

// 1. 서비스 토큰 자동 처리
server.addTool({
  name: 'search_data',
  description: '데이터 검색',
  // 필요한 서비스 토큰 선언
  requiredTokens: ['JIRA_TOKEN', 'JIRA_EMAIL'],
  handler: async (params, context) => {
    // context.serviceTokens에서 자동으로 토큰 주입
    const { JIRA_TOKEN, JIRA_EMAIL } = context.serviceTokens;
    // ...
  }
});

// 2. 환경변수 스키마 정의
server.defineEnvSchema({
  JIRA_TOKEN: { type: 'secret', required: true, description: 'Jira API 토큰' },
  JIRA_EMAIL: { type: 'string', required: true, description: 'Jira 계정 이메일' },
  JIRA_URL: { type: 'url', required: true, description: 'Jira 인스턴스 URL' },
});

// 3. 헬스체크 자동 구현
// GET /health 자동 제공

// 4. K-ARC 카탈로그 메타데이터
server.setCatalogInfo({
  displayName: 'My MCP Server',
  description: '데이터 검색 서버',
  category: 'DevTools',
  tags: ['search', 'data'],
  icon: 'https://example.com/icon.png',
});

server.listen(8080);
```

### 3.2 자동 처리되어야 할 기능 목록

| 기능 | 설명 | 중요도 |
|------|------|--------|
| **서비스 토큰 전파** | X-Service-Token 헤더 자동 파싱 및 주입 | 🔴 필수 |
| **사용자 컨텍스트** | X-MCPHub-User-Id 헤더 자동 처리 | 🔴 필수 |
| **MCP 프로토콜** | JSON-RPC, tools/list, tools/call 자동 구현 | 🔴 필수 |
| **헬스체크** | /health 엔드포인트 자동 제공 | 🟡 권장 |
| **에러 처리** | K-ARC 표준 에러 포맷 자동 적용 | 🟡 권장 |
| **로깅** | 표준 로그 포맷 및 X-Request-ID 전파 | 🟡 권장 |
| **환경변수 검증** | 서버 시작 시 필수 환경변수 검증 | 🟢 선택 |
| **K-ARC 자동 등록** | CLI 명령으로 카탈로그 자동 등록 | 🟢 선택 |

### 3.3 CLI 도구 추가 제안

```bash
# MCP 서버 프로젝트 생성
$ k-arc new my-mcp-server
  ? 언어 선택: [TypeScript / Python]
  ? 카테고리: [DevTools / Productivity / Collaboration]
  ✔ 프로젝트 생성 완료!

# 로컬 개발 서버 실행
$ k-arc dev
  🚀 MCP 서버 실행 중: http://localhost:8080
  📋 Tools: http://localhost:8080/tools
  ❤️ Health: http://localhost:8080/health

# K-ARC 카탈로그에 등록 요청
$ k-arc register --karc-url https://k-arc.example.com
  ✔ 서버 검증 완료
  ✔ 등록 요청 제출됨 (관리자 승인 대기)

# 환경변수 스키마 검증
$ k-arc validate
  ✔ JIRA_TOKEN: OK
  ✔ JIRA_EMAIL: OK
  ✔ JIRA_URL: OK
```

---

## 4. ⚠️ 일정 조정 제안

### 제안된 일정 (원안)

| Phase | 기간 | 기간 (일) |
|-------|------|----------|
| Phase 1: 설계 | 12/18 - 12/20 | 3일 |
| Phase 2: 프로토타입 | 12/21 - 12/25 | 5일 |
| Phase 3: 안정화 | 12/26 - 12/31 | 6일 |

### 현실적 우려 사항

1. **연말 연휴**: 12/25 (크리스마스), 12/31 (연말) 등 휴일 고려 필요
2. **통합 테스트 병행**: 현재 K-Jarvis 1.0 통합 테스트 진행 중
3. **SDK 품질**: 급하게 만든 SDK는 오히려 개발자 경험 저하

### 조정 제안

| Phase | 조정된 기간 | 내용 |
|-------|------------|------|
| **Phase 0** | 12/18 - 12/20 | K-Jarvis 1.0 통합 테스트 완료 |
| **Phase 1** | 12/21 - 12/27 | SDK 설계 및 인터페이스 확정 |
| **Phase 2** | 12/28 - 01/10 | 프로토타입 개발 |
| **Phase 3** | 01/11 - 01/17 | 안정화 및 문서화 |
| **Phase 4** | 01/18 - 01/24 | 기존 Agent/MCP 마이그레이션 |

**이유**:
- 통합 테스트 완료 후 SDK 개발에 집중
- 연말 연휴 기간은 설계 문서화에 활용
- 1월 중순까지 안정적인 SDK 1.0 릴리스 목표

---

## 5. 📝 추가 논의 필요 사항

### 5.1 Option C (SDK + Builder) 관련

하이브리드 옵션에 동의합니다. 다만 우선순위 제안:

```
Phase 1: SDK 개발 (즉시)
Phase 2: Agent Builder (Q1 2025)
Phase 3: MCP Builder (Q2 2025)
```

**MCP Builder 관련 의견**:
- K-ARC 포털에 "간편 MCP 서버 생성" 기능으로 통합 가능
- 별도 서비스보다 K-ARC 관리 UI 확장 권장

### 5.2 기존 코드와의 호환성

| 질문 | K-ARC 팀 의견 |
|------|--------------|
| 기존 MCP 스펙 호환 | 100% 호환 필수 (확장은 옵션) |
| 기존 MCP 서버 마이그레이션 | SDK 래퍼로 점진적 적용 |
| 배포 | npm 공개 배포 권장 (`@k-arc/mcp-sdk`) |

### 5.3 k-jarvis-contracts 스키마

K-ARC 팀이 기여할 스키마:

```yaml
# mcp-protocol.yaml
MCPToolCall:
  type: object
  properties:
    name:
      type: string
    arguments:
      type: object
    
MCPToolResult:
  type: object
  properties:
    content:
      type: array
      items:
        $ref: '#/MCPContent'
    isError:
      type: boolean

# service-tokens.yaml
ServiceTokenHeader:
  type: object
  properties:
    X-MCPHub-User-Id:
      type: string
    X-Service-Tokens:
      type: object
      additionalProperties:
        type: string
```

---

## 6. ✅ 최종 결론

| 항목 | 결론 |
|------|------|
| SDK 개발 | ✅ 적극 동의 |
| 역할 분담 | ✅ 동의 (TypeScript 버전 K-ARC 주도) |
| k-arc-mcp-sdk 개발 | ✅ 담당 수락 |
| 일정 | ⚠️ 조정 제안 (1월 중순 릴리스 목표) |
| Option 선택 | ✅ Option C (SDK 먼저 + Builder 나중) |

---

## 7. 🗓️ 다음 단계 제안

1. **12/18 (수)**: 3팀 협의 미팅 (SDK 범위 및 인터페이스 확정)
2. **12/19 (목)**: k-jarvis-contracts 초기 스키마 작성
3. **12/20 (금)**: SDK API 설계 문서 리뷰

---

**MCPHub (K-ARC) Team**  
**K-Jarvis SDK 개발 참여 확정** 🚀


