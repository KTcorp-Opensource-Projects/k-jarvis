# 외부 Agent Builder 플랫폼 연동 계획

**작성일**: 2026-01-05  
**담당**: Orchestrator Team  
**상태**: 📋 **테스트 계획**

---

## 🎯 목표

> **K-Jarvis가 A2A 프로토콜을 준수하므로, 외부 Agent Builder 플랫폼에서 만든 Agent도 쉽게 연동할 수 있어야 한다.**

---

## 📊 외부 Agent Builder 플랫폼 분석

### 주요 플랫폼 현황

| 플랫폼 | 유형 | A2A 지원 | 연동 방식 | 난이도 |
|--------|------|----------|----------|--------|
| **Dify** | No-Code AI App Builder | ❌ (Adapter 필요) | REST API | 🟡 중 |
| **n8n** | Workflow Automation | ❌ (Adapter 필요) | Webhook | 🟢 쉬움 |
| **CrewAI** | Python Agent Framework | ❌ (Adapter 필요) | Python API | 🟡 중 |
| **LangGraph** | Agent Framework | ❌ (Adapter 필요) | Python API | 🟡 중 |
| **AutoGen** | Multi-Agent Framework | ❌ (Adapter 필요) | Python API | 🔴 어려움 |
| **Flowise** | No-Code LLM Builder | ❌ (Adapter 필요) | REST API | 🟢 쉬움 |

### 연동 전략

```
[외부 Agent Builder]
     ↓ (플랫폼 고유 API)
[A2A Adapter] ← 우리가 개발
     ↓ (A2A Protocol)
[K-Jarvis Orchestrator]
```

---

## 🧪 테스트 환경 구축 방안

### 1. Docker 기반 로컬 설치

모든 플랫폼을 Docker로 로컬에 설치하여 테스트합니다.

#### Dify 설치

```bash
# Dify Docker Compose
git clone https://github.com/langgenius/dify.git
cd dify/docker
cp .env.example .env
docker-compose up -d

# 접속: http://localhost:3000 (Dify 기본 포트)
```

#### n8n 설치

```bash
# n8n Docker
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n

# 접속: http://localhost:5678
```

#### Flowise 설치

```bash
# Flowise Docker
docker run -d \
  --name flowise \
  -p 3001:3000 \
  -v flowise_data:/root/.flowise \
  flowiseai/flowise

# 접속: http://localhost:3001
```

### 2. 테스트용 Docker Compose

```yaml
# docker-compose.agent-builders.yml
version: '3.8'

services:
  # Dify
  dify-web:
    image: langgenius/dify-web:latest
    ports:
      - "3000:3000"
    depends_on:
      - dify-api
  
  dify-api:
    image: langgenius/dify-api:latest
    ports:
      - "5001:5001"
    environment:
      - SECRET_KEY=your-secret-key
  
  # n8n
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
  
  # Flowise
  flowise:
    image: flowiseai/flowise:latest
    ports:
      - "3001:3000"
    volumes:
      - flowise_data:/root/.flowise

volumes:
  n8n_data:
  flowise_data:
```

---

## 🔌 A2A Adapter 설계

### Adapter 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                 A2A Adapter Layer                    │
├─────────────────────────────────────────────────────┤
│  DifyAdapter  │  N8nAdapter  │  FlowiseAdapter      │
│  ├─ API 호출  │  ├─ Webhook  │  ├─ API 호출         │
│  ├─ 응답 변환 │  ├─ 응답 변환│  ├─ 응답 변환        │
│  └─ Agent Card│  └─ Agent Card│ └─ Agent Card       │
├─────────────────────────────────────────────────────┤
│                 Base A2A Adapter                     │
│  ├─ A2A Protocol 구현                                │
│  ├─ Agent Card 생성                                  │
│  └─ 표준 응답 변환                                   │
└─────────────────────────────────────────────────────┘
```

### Base Adapter 인터페이스

```python
# adapters/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel

class AgentCard(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    skills: list = []
    capabilities: dict = {}

class A2ARequest(BaseModel):
    method: str
    params: dict

class A2AResponse(BaseModel):
    message: dict

class BaseA2AAdapter(ABC):
    """외부 Agent Builder를 A2A 프로토콜로 래핑하는 기본 어댑터"""
    
    def __init__(self, config: dict):
        self.config = config
        self.agent_card = self._create_agent_card()
    
    @abstractmethod
    def _create_agent_card(self) -> AgentCard:
        """플랫폼별 Agent Card 생성"""
        pass
    
    @abstractmethod
    async def _call_platform(self, message: str) -> str:
        """플랫폼 고유 API 호출"""
        pass
    
    async def handle_a2a_request(self, request: A2ARequest) -> A2AResponse:
        """A2A 표준 요청 처리"""
        if request.method == "SendMessage":
            # 메시지 추출
            message = request.params.get("message", {})
            parts = message.get("parts", [])
            text = parts[0].get("text", "") if parts else ""
            
            # 플랫폼 호출
            result = await self._call_platform(text)
            
            # A2A 표준 응답 생성
            return A2AResponse(
                message={
                    "role": "agent",
                    "parts": [{"text": result}]
                }
            )
        
        raise ValueError(f"Unknown method: {request.method}")
    
    def get_agent_card(self) -> dict:
        """/.well-known/agent.json 반환"""
        return self.agent_card.dict()
```

### Dify Adapter

```python
# adapters/dify_adapter.py
import httpx
from .base import BaseA2AAdapter, AgentCard

class DifyAdapter(BaseA2AAdapter):
    """Dify 앱을 A2A Agent로 래핑"""
    
    def __init__(self, config: dict):
        """
        config:
            - dify_url: Dify API URL (e.g., http://localhost:5001)
            - api_key: Dify API Key
            - app_id: Dify App ID
            - agent_name: Agent 이름
            - agent_description: Agent 설명
        """
        super().__init__(config)
    
    def _create_agent_card(self) -> AgentCard:
        return AgentCard(
            name=self.config.get("agent_name", "Dify Agent"),
            description=self.config.get("agent_description", "Dify로 생성된 AI Agent"),
            version="1.0.0",
            skills=[
                {
                    "id": "chat",
                    "name": "chat",
                    "description": "Dify 앱과 대화",
                    "tags": ["dify", "chat", "ai"]
                }
            ],
            capabilities={
                "streaming": False,
                "pushNotifications": False
            }
        )
    
    async def _call_platform(self, message: str) -> str:
        """Dify API 호출"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config['dify_url']}/v1/chat-messages",
                headers={
                    "Authorization": f"Bearer {self.config['api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": {},
                    "query": message,
                    "response_mode": "blocking",
                    "user": "k-jarvis-user"
                }
            )
            
            data = response.json()
            return data.get("answer", "No response from Dify")
```

### n8n Adapter

```python
# adapters/n8n_adapter.py
import httpx
from .base import BaseA2AAdapter, AgentCard

class N8nAdapter(BaseA2AAdapter):
    """n8n Workflow를 A2A Agent로 래핑"""
    
    def __init__(self, config: dict):
        """
        config:
            - webhook_url: n8n Webhook URL
            - agent_name: Agent 이름
            - agent_description: Agent 설명
        """
        super().__init__(config)
    
    def _create_agent_card(self) -> AgentCard:
        return AgentCard(
            name=self.config.get("agent_name", "n8n Workflow Agent"),
            description=self.config.get("agent_description", "n8n으로 생성된 Workflow Agent"),
            version="1.0.0",
            skills=[
                {
                    "id": "execute_workflow",
                    "name": "execute_workflow",
                    "description": "n8n 워크플로우 실행",
                    "tags": ["n8n", "workflow", "automation"]
                }
            ],
            capabilities={
                "streaming": False,
                "pushNotifications": False
            }
        )
    
    async def _call_platform(self, message: str) -> str:
        """n8n Webhook 호출"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config['webhook_url'],
                json={"message": message}
            )
            
            data = response.json()
            # n8n 응답 형식에 따라 파싱
            return data.get("response", str(data))
```

### Flowise Adapter

```python
# adapters/flowise_adapter.py
import httpx
from .base import BaseA2AAdapter, AgentCard

class FlowiseAdapter(BaseA2AAdapter):
    """Flowise Chatflow를 A2A Agent로 래핑"""
    
    def __init__(self, config: dict):
        """
        config:
            - flowise_url: Flowise API URL
            - chatflow_id: Chatflow ID
            - agent_name: Agent 이름
            - agent_description: Agent 설명
        """
        super().__init__(config)
    
    def _create_agent_card(self) -> AgentCard:
        return AgentCard(
            name=self.config.get("agent_name", "Flowise Agent"),
            description=self.config.get("agent_description", "Flowise로 생성된 AI Agent"),
            version="1.0.0",
            skills=[
                {
                    "id": "chat",
                    "name": "chat",
                    "description": "Flowise Chatflow와 대화",
                    "tags": ["flowise", "chat", "llm"]
                }
            ],
            capabilities={
                "streaming": False,
                "pushNotifications": False
            }
        )
    
    async def _call_platform(self, message: str) -> str:
        """Flowise API 호출"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config['flowise_url']}/api/v1/prediction/{self.config['chatflow_id']}",
                json={"question": message}
            )
            
            data = response.json()
            return data.get("text", "No response from Flowise")
```

---

## 🚀 Adapter 서버 구현

```python
# adapter_server.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from adapters.dify_adapter import DifyAdapter
from adapters.n8n_adapter import N8nAdapter
from adapters.flowise_adapter import FlowiseAdapter

app = FastAPI(title="K-Jarvis A2A Adapter Server")

# Adapter 인스턴스 (설정에 따라 동적 생성)
adapters = {}

def register_adapter(adapter_id: str, adapter):
    adapters[adapter_id] = adapter

# Agent Card 엔드포인트
@app.get("/{adapter_id}/.well-known/agent.json")
async def get_agent_card(adapter_id: str):
    if adapter_id not in adapters:
        return JSONResponse(status_code=404, content={"error": "Adapter not found"})
    return adapters[adapter_id].get_agent_card()

# A2A 메시지 처리 엔드포인트
@app.post("/{adapter_id}/")
async def handle_message(adapter_id: str, request: Request):
    if adapter_id not in adapters:
        return JSONResponse(status_code=404, content={"error": "Adapter not found"})
    
    body = await request.json()
    
    from adapters.base import A2ARequest
    a2a_request = A2ARequest(
        method=body.get("method"),
        params=body.get("params", {})
    )
    
    response = await adapters[adapter_id].handle_a2a_request(a2a_request)
    
    return {
        "jsonrpc": "2.0",
        "result": {"message": response.message},
        "id": body.get("id")
    }

# 예시: Dify Adapter 등록
@app.on_event("startup")
async def startup():
    # Dify Adapter
    register_adapter("dify-agent", DifyAdapter({
        "dify_url": "http://localhost:5001",
        "api_key": "your-dify-api-key",
        "agent_name": "Dify Customer Support",
        "agent_description": "Dify로 만든 고객 지원 Agent"
    }))
    
    # n8n Adapter
    register_adapter("n8n-workflow", N8nAdapter({
        "webhook_url": "http://localhost:5678/webhook/your-webhook-id",
        "agent_name": "n8n Automation Agent",
        "agent_description": "n8n 워크플로우 기반 자동화 Agent"
    }))
    
    # Flowise Adapter
    register_adapter("flowise-chat", FlowiseAdapter({
        "flowise_url": "http://localhost:3001",
        "chatflow_id": "your-chatflow-id",
        "agent_name": "Flowise Q&A Agent",
        "agent_description": "Flowise로 만든 Q&A Agent"
    }))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

## 📋 테스트 시나리오

### Phase 1: 플랫폼 설치 및 기본 연동

| 단계 | 작업 | 예상 시간 |
|------|------|----------|
| 1 | Docker로 Dify/n8n/Flowise 설치 | 1일 |
| 2 | 각 플랫폼에서 간단한 Agent/Workflow 생성 | 1일 |
| 3 | Base Adapter 구현 | 1일 |
| 4 | 플랫폼별 Adapter 구현 | 2일 |
| 5 | Adapter Server 구현 및 테스트 | 1일 |

### Phase 2: K-Jarvis 연동 테스트

| 단계 | 작업 | 예상 시간 |
|------|------|----------|
| 1 | Adapter Agent를 K-Jarvis에 등록 | 0.5일 |
| 2 | K-Jarvis → Adapter → 외부 플랫폼 호출 테스트 | 1일 |
| 3 | 멀티 에이전트 체이닝 테스트 | 1일 |
| 4 | 에러 핸들링 및 안정성 테스트 | 1일 |

### Phase 3: 실제 사용 시나리오 테스트

```
[시나리오 1: Dify 고객 지원 Agent]
사용자: "제품 반품 절차 알려줘"
K-Jarvis → Dify Adapter → Dify App → 응답

[시나리오 2: n8n 자동화 Agent]
사용자: "오늘 날씨 확인하고 일정에 추가해줘"
K-Jarvis → n8n Adapter → n8n Workflow → 응답

[시나리오 3: 복합 시나리오]
사용자: "GitHub PR 확인하고 관련 고객 문의도 찾아줘"
K-Jarvis → GitHub Agent + Dify Adapter (병렬) → 통합 응답
```

---

## 🎯 기대 효과

### K-Jarvis 생태계 확장

```
현재:
- 직접 개발한 Agent만 연동 가능
- Agent 개발 진입 장벽 높음

Adapter 도입 후:
- Dify/n8n/Flowise 등에서 만든 Agent 연동 가능
- 비개발자도 Agent 생성 가능
- 생태계 빠른 확장
```

### 개발자 경험

```
[일반 사용자]
Dify/n8n에서 No-Code로 Agent 생성
     ↓
Adapter 설정만 하면 K-Jarvis 연동 완료

[개발자]
SDK로 직접 Agent 개발
     ↓
K-Jarvis 직접 연동
```

---

## 📝 다음 단계

1. **Docker 환경 구축**: Dify, n8n, Flowise 로컬 설치
2. **Base Adapter 개발**: 공통 인터페이스 구현
3. **Dify Adapter 우선 개발**: A2A 연동 PoC
4. **K-Jarvis 연동 테스트**: Agent Card 등록 및 호출 테스트
5. **문서화**: Adapter 사용 가이드 작성

---

**이 계획으로 외부 Agent Builder와의 연동 테스트를 진행할 수 있습니다!**


