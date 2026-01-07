# k-jarvis-contracts 스키마 초안 v1.0

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team  
**상태**: Draft (리뷰 요청)

---

## 📦 저장소 구조

```
k-jarvis-contracts/
├── schemas/
│   ├── common.yaml           # 공통 타입
│   ├── headers.yaml          # HTTP 헤더 정의
│   ├── a2a-protocol.yaml     # A2A 프로토콜 스키마
│   ├── mcp-protocol.yaml     # MCP 프로토콜 스키마
│   ├── agent-card.yaml       # Agent Card 스키마
│   └── errors.yaml           # 에러 코드 정의
├── golden-files/
│   ├── a2a/
│   │   ├── request.json
│   │   └── response.json
│   ├── mcp/
│   │   ├── tools-list.json
│   │   └── tools-call.json
│   └── agent-card/
│       └── example.json
├── generated/
│   ├── python/               # 자동 생성된 Python 타입
│   └── typescript/           # 자동 생성된 TypeScript 타입
└── README.md
```

---

## 📋 스키마 정의

### 1. common.yaml - 공통 타입

```yaml
# k-jarvis-contracts/schemas/common.yaml
openapi: 3.0.3
info:
  title: K-Jarvis Common Types
  version: 1.0.0

components:
  schemas:
    # 서비스 토큰
    ServiceTokens:
      type: object
      additionalProperties:
        type: string
      description: |
        서비스 토큰 키-값 쌍.
        예: { "JIRA_TOKEN": "xxx", "JIRA_EMAIL": "user@example.com" }
      example:
        JIRA_TOKEN: "your-jira-token"
        JIRA_EMAIL: "user@example.com"
        JIRA_URL: "https://your-domain.atlassian.net"

    # 사용자 컨텍스트
    UserContext:
      type: object
      properties:
        userId:
          type: string
          description: MCPHub 사용자 ID
          example: "user-123"
        kauthUserId:
          type: string
          format: uuid
          description: K-Auth 사용자 ID (SSO 로그인 시)
          example: "717dabfd-70b1-4d5c-999a-5de90d850be6"
        serviceTokens:
          $ref: '#/components/schemas/ServiceTokens'
        requestId:
          type: string
          description: 요청 추적 ID
          example: "req-abc-123"
        timestamp:
          type: string
          format: date-time
          description: 요청 타임스탬프

    # 타임스탬프
    Timestamp:
      type: string
      format: date-time
      example: "2024-12-17T15:30:00Z"
```

---

### 2. headers.yaml - HTTP 헤더 정의

```yaml
# k-jarvis-contracts/schemas/headers.yaml
openapi: 3.0.3
info:
  title: K-Jarvis HTTP Headers
  version: 1.0.0

components:
  headers:
    X-Request-Id:
      description: 요청 추적 ID (없으면 서버에서 생성)
      schema:
        type: string
      example: "req-abc-123"

    X-User-Id:
      description: Orchestrator 사용자 ID
      schema:
        type: string
      example: "user-456"

    X-MCPHub-User-Id:
      description: |
        MCPHub(K-ARC) 사용자 ID.
        서비스 토큰 조회에 사용됨.
        K-Auth 로그인 시 kauthUserId와 매핑됨.
      schema:
        type: string
      required: true
      example: "mcphub-user-789"

    X-Service-Tokens:
      description: |
        서비스 토큰 (Base64 인코딩된 JSON 또는 URL-encoded).
        K-ARC Gateway가 MCP 서버로 전달.
      schema:
        type: string
      example: "eyJKSVJBX1RPS0VOIjoiLi4uIn0="

    Content-Type:
      description: 요청 본문 타입
      schema:
        type: string
        enum:
          - application/json
          - text/event-stream
      example: "application/json"

    Accept:
      description: 응답 타입 (스트리밍 시 text/event-stream)
      schema:
        type: string
      example: "application/json"

  # 헤더 그룹
  securitySchemes:
    MCPHubUserAuth:
      type: apiKey
      in: header
      name: X-MCPHub-User-Id
      description: MCPHub 사용자 인증
```

---

### 3. a2a-protocol.yaml - A2A 프로토콜 스키마

```yaml
# k-jarvis-contracts/schemas/a2a-protocol.yaml
openapi: 3.0.3
info:
  title: A2A Protocol Schema
  version: 0.3.0
  description: Agent-to-Agent Protocol (Google A2A 기반)

components:
  schemas:
    # A2A 메시지 파트
    A2APart:
      oneOf:
        - $ref: '#/components/schemas/TextPart'
        - $ref: '#/components/schemas/DataPart'
        - $ref: '#/components/schemas/FilePart'

    TextPart:
      type: object
      required:
        - type
        - text
      properties:
        type:
          type: string
          enum: [text]
        text:
          type: string
      example:
        type: "text"
        text: "검색 결과입니다."

    DataPart:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum: [data]
        data:
          type: object
      example:
        type: "data"
        data:
          total: 10
          items: []

    FilePart:
      type: object
      required:
        - type
        - file
      properties:
        type:
          type: string
          enum: [file]
        file:
          type: object
          properties:
            name:
              type: string
            mimeType:
              type: string
            url:
              type: string
              format: uri

    # A2A 메시지
    A2AMessage:
      type: object
      required:
        - role
        - parts
      properties:
        role:
          type: string
          enum: [user, agent]
        parts:
          type: array
          items:
            $ref: '#/components/schemas/A2APart'
        metadata:
          type: object
          additionalProperties: true
      example:
        role: "agent"
        parts:
          - type: "text"
            text: "검색 결과입니다."

    # JSON-RPC 요청
    JsonRpcRequest:
      type: object
      required:
        - jsonrpc
        - method
        - id
      properties:
        jsonrpc:
          type: string
          enum: ["2.0"]
        method:
          type: string
          enum:
            - message/send
            - message/stream
            - tasks/send
        params:
          type: object
          properties:
            message:
              $ref: '#/components/schemas/A2AMessage'
        id:
          oneOf:
            - type: string
            - type: integer
      example:
        jsonrpc: "2.0"
        method: "message/send"
        params:
          message:
            role: "user"
            parts:
              - type: "text"
                text: "컨플루언스에서 검색해줘"
        id: "req-1"

    # JSON-RPC 응답
    JsonRpcResponse:
      type: object
      required:
        - jsonrpc
        - id
      properties:
        jsonrpc:
          type: string
          enum: ["2.0"]
        id:
          oneOf:
            - type: string
            - type: integer
        result:
          type: object
          properties:
            message:
              $ref: '#/components/schemas/A2AMessage'
        error:
          $ref: '#/components/schemas/JsonRpcError'

    # JSON-RPC 에러
    JsonRpcError:
      type: object
      required:
        - code
        - message
      properties:
        code:
          type: integer
          description: |
            JSON-RPC 에러 코드:
            - -32001: 서비스 토큰 미설정
            - -32002: 서비스 토큰 만료
            - -32003: 서비스 토큰 무효
            - -32600: Invalid Request
            - -32601: Method not found
            - -32602: Invalid params
            - -32603: Internal error
        message:
          type: string
        data:
          type: object
```

---

### 4. agent-card.yaml - Agent Card 스키마

```yaml
# k-jarvis-contracts/schemas/agent-card.yaml
openapi: 3.0.3
info:
  title: Agent Card Schema
  version: 1.0.0
  description: K-Jarvis Agent Card 스키마 (A2A 기반 확장)

components:
  schemas:
    AgentCard:
      type: object
      required:
        - name
        - description
        - version
        - endpoints
      properties:
        # 기본 정보
        name:
          type: string
          description: Agent 이름
          example: "Confluence AI Agent"
        description:
          type: string
          description: Agent 설명
          example: "Confluence 문서 관리를 위한 AI 에이전트"
        version:
          type: string
          pattern: '^\d+\.\d+\.\d+$'
          description: 버전 (semver)
          example: "2.0.0"
        protocolVersion:
          type: string
          default: "0.3.0"
          description: A2A 프로토콜 버전

        # 엔드포인트
        endpoints:
          type: object
          required:
            - message
          properties:
            message:
              type: string
              description: 메시지 엔드포인트
              example: "/a2a"
            task:
              type: string
              description: 태스크 엔드포인트
              example: "/tasks/send"
            stream:
              type: string
              description: 스트리밍 엔드포인트
              example: "/a2a"

        # 스킬
        skills:
          type: array
          items:
            $ref: '#/components/schemas/AgentSkill'

        # K-Jarvis 확장: 라우팅
        routing:
          $ref: '#/components/schemas/AgentRouting'

        # K-Jarvis 확장: 요구사항
        requirements:
          $ref: '#/components/schemas/AgentRequirements'

        # 연락처
        contact:
          type: object
          properties:
            email:
              type: string
              format: email
            repository:
              type: string
              format: uri

    AgentSkill:
      type: object
      required:
        - id
        - name
      properties:
        id:
          type: string
          example: "search_confluence"
        name:
          type: string
          example: "Search Confluence"
        description:
          type: string
          example: "Confluence 문서를 검색합니다"
        tags:
          type: array
          items:
            type: string
          example: ["search", "confluence", "document"]
        inputSchema:
          type: object
          description: JSON Schema for input

    AgentRouting:
      type: object
      description: K-Jarvis RAG 라우팅용 메타데이터
      properties:
        domain:
          type: string
          description: 도메인 (documentation, project-management, etc.)
          example: "documentation"
        category:
          type: string
          description: 카테고리 (confluence, jira, github, etc.)
          example: "confluence"
        keywords:
          type: array
          items:
            type: string
          description: 라우팅 키워드
          example: ["컨플루언스", "문서", "위키", "confluence"]
        priority:
          type: integer
          minimum: 0
          maximum: 100
          default: 50
          description: 라우팅 우선순위 (높을수록 우선)

    AgentRequirements:
      type: object
      description: Agent 실행 요구사항
      properties:
        mcpHubToken:
          type: boolean
          default: false
          description: MCPHub 토큰 필요 여부
        mcpServers:
          type: array
          items:
            type: string
          description: 필요한 MCP 서버 목록
          example: ["atlassian-confluence"]
```

---

### 5. errors.yaml - 에러 코드 정의

```yaml
# k-jarvis-contracts/schemas/errors.yaml
openapi: 3.0.3
info:
  title: K-Jarvis Error Codes
  version: 1.0.0

components:
  schemas:
    # 통합 에러 코드
    ErrorCode:
      type: string
      enum:
        # K-Jarvis Orchestrator
        - KJARVIS_UNAUTHORIZED
        - KJARVIS_AGENT_NOT_FOUND
        - KJARVIS_ROUTING_FAILED
        
        # K-ARC (MCPHub)
        - KARC_UNAUTHORIZED
        - KARC_INVALID_API_KEY
        - KARC_MISSING_SERVICE_TOKEN
        - KARC_INVALID_SERVICE_TOKEN
        - KARC_EXPIRED_SERVICE_TOKEN
        - KARC_SERVER_NOT_FOUND
        - KARC_TOOL_NOT_FOUND
        - KARC_TOOL_EXECUTION_ERROR
        
        # 공통
        - INVALID_REQUEST
        - INTERNAL_ERROR
        - RATE_LIMITED

    # JSON-RPC 에러 코드 매핑
    JsonRpcErrorCodeMapping:
      type: object
      description: 문자열 에러 코드 → JSON-RPC 숫자 코드 매핑
      properties:
        KARC_MISSING_SERVICE_TOKEN:
          type: integer
          enum: [-32001]
        KARC_EXPIRED_SERVICE_TOKEN:
          type: integer
          enum: [-32002]
        KARC_INVALID_SERVICE_TOKEN:
          type: integer
          enum: [-32003]
        KARC_SERVER_NOT_FOUND:
          type: integer
          enum: [-32004]
        KARC_TOOL_NOT_FOUND:
          type: integer
          enum: [-32005]
        KARC_TOOL_EXECUTION_ERROR:
          type: integer
          enum: [-32006]

    # 에러 응답
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
              oneOf:
                - $ref: '#/components/schemas/ErrorCode'
                - type: integer
              description: 에러 코드 (문자열 또는 JSON-RPC 숫자)
            message:
              type: string
              description: 에러 메시지
            details:
              type: object
              additionalProperties: true
              description: 추가 상세 정보
        statusCode:
          type: integer
          description: HTTP 상태 코드
```

---

## 📁 Golden Files 예시

### a2a/request.json

```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "컨플루언스에서 K-Jarvis 관련 문서 검색해줘"
        }
      ]
    }
  },
  "id": "req-12345"
}
```

### a2a/response.json

```json
{
  "jsonrpc": "2.0",
  "id": "req-12345",
  "result": {
    "message": {
      "role": "agent",
      "parts": [
        {
          "type": "text",
          "text": "K-Jarvis 관련 문서 3건을 찾았습니다."
        },
        {
          "type": "data",
          "data": {
            "total": 3,
            "items": [
              {"title": "K-Jarvis 아키텍처", "url": "..."},
              {"title": "K-Jarvis 개발 가이드", "url": "..."},
              {"title": "K-Jarvis OAuth 연동", "url": "..."}
            ]
          }
        }
      ]
    }
  }
}
```

### agent-card/example.json

```json
{
  "name": "Confluence AI Agent",
  "description": "Confluence 문서 관리를 위한 AI 에이전트",
  "version": "2.0.0",
  "protocolVersion": "0.3.0",
  "endpoints": {
    "message": "/a2a",
    "task": "/tasks/send",
    "stream": "/a2a"
  },
  "skills": [
    {
      "id": "search_confluence",
      "name": "Search Confluence",
      "description": "Confluence 문서를 검색합니다",
      "tags": ["search", "confluence", "document"]
    },
    {
      "id": "create_page",
      "name": "Create Page",
      "description": "새 Confluence 페이지를 생성합니다",
      "tags": ["create", "confluence", "document"]
    }
  ],
  "routing": {
    "domain": "documentation",
    "category": "confluence",
    "keywords": ["컨플루언스", "문서", "위키", "confluence"],
    "priority": 50
  },
  "requirements": {
    "mcpHubToken": true,
    "mcpServers": ["atlassian-confluence"]
  }
}
```

---

## 🔄 피드백 요청

### Agent Team
- [ ] a2a-protocol.yaml 리뷰
- [ ] agent-card.yaml 리뷰
- [ ] Golden Files 검증

### K-ARC Team
- [ ] mcp-protocol.yaml 기여 (MCP 스키마)
- [ ] errors.yaml 리뷰 (KARC 에러 코드)
- [ ] headers.yaml 리뷰 (X-Service-Tokens)

---

## 📋 체크리스트 업데이트

```markdown
### Orchestrator Team
- [x] k-jarvis-utils API 설계 v1 ✅
- [x] k-jarvis-contracts 스키마 초안 v1 ✅
- [ ] Agent Team 피드백 반영
- [ ] K-ARC Team 피드백 반영
```

---

**Orchestrator Team**


