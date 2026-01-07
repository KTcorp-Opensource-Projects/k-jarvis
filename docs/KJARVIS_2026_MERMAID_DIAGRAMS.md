# K-Jarvis 2026 비전 문서 - Mermaid 다이어그램 코드

> **용도**: Confluence 업로드 시 수동 삽입용  
> **작성일**: 2025-12-29

---

## 1. 전체 아키텍처 다이어그램

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#00d4ff', 'primaryTextColor': '#fff', 'primaryBorderColor': '#00d4ff', 'lineColor': '#00d4ff', 'secondaryColor': '#1a1a2e', 'tertiaryColor': '#16213e'}}}%%
flowchart TB
    subgraph Users["👥 사용자 접점"]
        Web["🌐 Web Browser"]
        Mobile["📱 Mobile App"]
        GiGaGenie["🎙️ 기가지니"]
        SmartCar["🚗 스마트카"]
        API["🔌 External API"]
    end

    subgraph KJarvis["🤖 K-Jarvis Platform"]
        Orchestrator["🎯 Orchestrator<br/>(Agent Routing)"]
        HybridRouter["🧠 HybridRouter<br/>(RAG + LLM)"]
        ConversationMgr["💬 Conversation<br/>Manager"]
    end

    subgraph KAuth["🔐 K-Auth"]
        OAuth["OAuth 2.0<br/>Server"]
        JWT["JWT Token<br/>Service"]
        UserMgmt["User<br/>Management"]
    end

    subgraph KARC["⚡ K-ARC (MCPHub)"]
        MCPGateway["MCP Gateway"]
        TokenMgr["Token<br/>Manager"]
        ServerCatalog["Server<br/>Catalog"]
    end

    subgraph Agents["🤖 K-Agents"]
        ConfAgent["📄 Confluence<br/>Agent"]
        JiraAgent["📋 Jira<br/>Agent"]
        GitAgent["💻 GitHub<br/>Agent"]
        CalAgent["📅 Calendar<br/>Agent"]
        CustomAgent["🔧 Custom<br/>Agents..."]
    end

    subgraph MCPServers["🔧 MCP Servers"]
        ConfMCP["Confluence<br/>MCP"]
        JiraMCP["Jira<br/>MCP"]
        GitMCP["GitHub<br/>MCP"]
        SlackMCP["Slack<br/>MCP"]
        CustomMCP["Custom<br/>MCPs..."]
    end

    subgraph Infra["🏗️ Infrastructure"]
        PostgreSQL["🐘 PostgreSQL<br/>(pgvector)"]
        Redis["⚡ Redis"]
        AzureOpenAI["🧠 Azure<br/>OpenAI"]
    end

    Users --> KAuth
    KAuth --> KJarvis
    KJarvis --> Agents
    Agents --> KARC
    KARC --> MCPServers
    KJarvis --> Infra
    KARC --> Infra
    KAuth --> Infra
```

---

## 2. 연간 로드맵 Gantt 차트

```mermaid
%%{init: {'theme': 'dark'}}%%
gantt
    title K-Jarvis 2026 로드맵
    dateFormat  YYYY-MM-DD
    
    section Phase 1: 내부 안정화
    K-Jarvis 1.0 정식 출시     :done, p1a, 2026-01-01, 30d
    K-ARC Stateless 전환       :done, p1b, 2026-01-15, 21d
    핵심 에이전트 5종 안정화    :active, p1c, 2026-02-01, 28d
    사내 파일럿 10개 부서       :p1d, 2026-02-15, 42d
    
    section Phase 2: 거버넌스 체계
    k-jarvis-utils SDK 배포    :p2a, 2026-04-01, 21d
    k-arc-utils SDK 배포       :p2b, 2026-04-15, 21d
    등록 심사 프로세스 수립     :p2c, 2026-05-01, 30d
    개발자 포털 오픈           :p2d, 2026-05-15, 30d
    
    section Phase 3: 생태계 확장
    사내 Agent 50개 등록       :p3a, 2026-07-01, 90d
    MCP Server 30개 등록       :p3b, 2026-07-01, 90d
    외부 파트너 연동 시작       :p3c, 2026-09-01, 60d
    기가지니 연동 PoC          :p3d, 2026-10-01, 60d
```

---

## 3. Agent 개발 거버넌스 플로우

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    subgraph Required["✅ 필수 사항"]
        A1["Agent Card<br/>/.well-known/agent.json"]
        A2["JSON-RPC 2.0<br/>통신 프로토콜"]
        A3["Health Check<br/>엔드포인트"]
        A4["에러 핸들링<br/>표준 응답"]
    end
    
    subgraph Quality["📊 품질 기준"]
        Q1["응답 시간<br/>< 30초"]
        Q2["가용성<br/>> 99%"]
        Q3["문서화<br/>필수"]
    end
    
    Required --> Quality
```

---

## 4. 등록 심사 프로세스 상태 다이어그램

```mermaid
%%{init: {'theme': 'dark'}}%%
stateDiagram-v2
    [*] --> 신청: 개발자 포털에서 등록 신청
    신청 --> 자동검증: Agent Card / MCP 스키마 검증
    자동검증 --> 거절: 검증 실패
    자동검증 --> 수동심사: 검증 통과
    수동심사 --> 보완요청: 품질 미달
    수동심사 --> 승인: 심사 통과
    보완요청 --> 수동심사: 보완 완료
    거절 --> [*]
    승인 --> 등록완료
    등록완료 --> [*]
```

---

## 5. 개발자의 하루 시나리오 시퀀스 다이어그램

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    participant User as 👤 사용자
    participant Jarvis as 🤖 K-Jarvis
    participant Router as 🧠 HybridRouter
    participant Conf as 📄 Confluence Agent
    participant Jira as 📋 Jira Agent
    participant Git as 💻 GitHub Agent
    participant LLM as 🧠 Azure OpenAI

    User->>Jarvis: "어제 회의 내용 읽어줘..."
    Jarvis->>Router: 의도 분석 요청
    Router->>LLM: 멀티 에이전트 라우팅 판단
    LLM-->>Router: [Confluence, Jira, GitHub]
    
    par 병렬 처리
        Router->>Conf: 어제 회의록 검색
        Conf-->>Router: 회의록 내용
    and
        Router->>Jira: 어제 완료 이슈 조회
        Jira-->>Router: 완료된 이슈 목록
    and
        Router->>Git: 어제 커밋/PR 조회
        Git-->>Router: 커밋/PR 내용
    end
    
    Router->>LLM: 결과 종합 및 요약
    LLM-->>Router: 종합 응답
    Router-->>Jarvis: 최종 응답
    Jarvis-->>User: "어제 회의에서는... 오늘 회의에서는..."
```

---

## 6. 기가지니 연동 시퀀스 다이어그램

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    participant User as 🗣️ 사용자
    participant GiGa as 🎙️ 기가지니
    participant STT as 🔊 STT 서비스
    participant Jarvis as 🤖 K-Jarvis
    participant Cal as 📅 Calendar Agent
    participant TTS as 🔈 TTS 서비스

    User->>GiGa: "기가지니, 오늘 회사 일정 알려줘"
    GiGa->>STT: 음성 → 텍스트 변환
    STT-->>GiGa: "오늘 회사 일정 알려줘"
    GiGa->>GiGa: 사용자 음성 프로파일로 식별
    GiGa->>Jarvis: API 호출 (user_id, query)
    Jarvis->>Cal: 일정 조회 요청
    Cal-->>Jarvis: 오늘 일정 목록
    Jarvis-->>GiGa: 일정 응답 (텍스트)
    GiGa->>TTS: 텍스트 → 음성 변환
    TTS-->>GiGa: 음성 데이터
    GiGa-->>User: "오늘 오전 10시에 팀 회의가 있고..."
```

---

## 7. 스마트카 연동 시퀀스 다이어그램

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    participant Driver as 🚗 운전자
    participant Car as 🎤 차량 STT
    participant Jarvis as 🤖 K-Jarvis
    participant Cal as 📅 Calendar Agent
    participant Nav as 🗺️ 네비게이션

    Driver->>Car: "오늘 첫 미팅 장소로 안내해줘"
    Car->>Jarvis: API 호출 (user_id, query)
    Jarvis->>Cal: 오늘 첫 미팅 정보 조회
    Cal-->>Jarvis: {title: "팀 회의", location: "강남역 WeWork 5층"}
    Jarvis->>Jarvis: 위치 정보 추출
    Jarvis-->>Car: {response: "...", location: {...}}
    Car->>Nav: 목적지 설정
    Nav-->>Car: 경로 안내 시작
    Car-->>Driver: "오전 10시 강남역 WeWork로 안내합니다"
```

---

## 8. 인프라 구성 다이어그램

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart TB
    subgraph External["🌐 External"]
        Users["👥 Users"]
        Partners["🤝 Partners"]
    end

    subgraph LoadBalancer["⚖️ Load Balancer"]
        LB["Nginx / K8s Ingress"]
    end

    subgraph Services["🐳 Docker Services"]
        subgraph Orchestrator["K-Jarvis"]
            OFE["Frontend<br/>:4000"]
            OBE["Backend<br/>:4001"]
        end
        
        subgraph Auth["K-Auth"]
            KA["Auth Server<br/>:4002"]
        end
        
        subgraph ARC["K-ARC"]
            AFE["Frontend<br/>:5173"]
            ABE["Backend<br/>:3000"]
        end
        
        subgraph Agents["K-Agents"]
            A1["Confluence<br/>:5010"]
            A2["Jira<br/>:5011"]
            A3["GitHub<br/>:5012"]
        end
    end

    subgraph Data["💾 Data Layer"]
        PG["PostgreSQL<br/>(pgvector)"]
        RD["Redis"]
    end

    subgraph AI["🧠 AI Services"]
        Azure["Azure OpenAI"]
    end

    External --> LoadBalancer
    LoadBalancer --> Services
    Services --> Data
    Services --> AI
```

---

## 9. 생태계 성장 목표 차트

```mermaid
%%{init: {'theme': 'dark'}}%%
xychart-beta
    title "K-Jarvis 생태계 성장 목표"
    x-axis [Q1, Q2, Q3, Q4]
    y-axis "개수" 0 --> 60
    bar [5, 15, 35, 50]
    line [5, 15, 25, 30]
```

---

## 10. 비전 요약 다이어그램

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#00d4ff'}}}%%
mindmap
  root((K-Jarvis<br/>Ecosystem))
    🤖 K-Jarvis
      Agent Routing
      Multi-Agent Chaining
      RAG Router
      Conversation Context
    ⚡ K-ARC
      MCP Gateway
      Token Management
      Server Catalog
      Subscription
    🔐 K-Auth
      OAuth 2.0
      SSO
      JWT
      Developer Console
    🤖 K-Agents
      Confluence
      Jira
      GitHub
      Calendar
      Custom...
    🎯 2026 Goals
      50 Agents
      30 MCP Servers
      5000 MAU
      기가지니 연동
```

---

## Confluence 업로드 방법

1. Confluence 페이지 편집 모드 진입
2. `/` 입력 후 "Mermaid" 검색
3. Mermaid 매크로 삽입
4. 위 코드 복사하여 붙여넣기
5. 저장

**참고**: Confluence에서 Mermaid가 지원되지 않는 경우:
- Mermaid Live Editor (https://mermaid.live) 에서 PNG/SVG로 내보내기
- 이미지로 삽입

---

**K-Jarvis Orchestrator Team** 🚀

