# Sample Agent HTTP 500 에러 보고

**작성일**: 2025-12-19  
**작성팀**: Orchestrator Team  
**대상**: Agent Team  
**긴급도**: 🟡 중간

---

## 📋 배경

통합 테스트 중 Sample AI Agent로 라우팅은 성공했으나, Agent 내부에서 HTTP 500 에러가 발생했습니다.

---

## 🔴 에러 상황

### 테스트 요청
```
사용자 입력: "문서를 검색해줘"
```

### 응답
```
SAMPLE AI AGENT RESPONSE
Agent error: HTTP 500
PROCESSED BY SAMPLE AI AGENT
```

---

## 🔍 에러 로그 (Sample Agent)

```
2025-12-19 06:36:06.485 | ERROR | src.agent.langgraph_agent:initialize:166 - 
Failed to initialize MCP tools: cannot import name 'SampleMCPClient' from 'src.mcp.client' (/app/src/mcp/client.py)

2025-12-19 06:36:06.485 | ERROR | src.agent.a2a_server:tasks_send:378 - 
[/tasks/send] Error: cannot import name 'SampleMCPClient' from 'src.mcp.client' (/app/src/mcp/client.py)
```

---

## 📊 에러 분석

| 항목 | 상세 |
|------|------|
| **에러 유형** | ImportError |
| **위치** | `src.mcp.client.py` |
| **원인** | `SampleMCPClient` 클래스가 존재하지 않거나 export되지 않음 |
| **영향** | MCP 도구 초기화 실패 → Agent 처리 불가 |

---

## ✅ 통합 환경 테스트 결과 (Orchestrator → Agent)

| 단계 | 상태 | 비고 |
|------|------|------|
| K-Auth SSO 로그인 | ✅ 성공 | |
| Agent 등록 | ✅ 성공 | Sample AI Agent |
| Azure OpenAI 라우팅 | ✅ 성공 | `gpt-4.1` 모델 사용 |
| A2A 요청 전달 | ✅ 성공 | `/tasks/send` 호출됨 |
| Agent 내부 처리 | ❌ 실패 | HTTP 500, MCP 초기화 실패 |

---

## 🔧 예상 해결 방안

1. `src/mcp/client.py`에서 `SampleMCPClient` 클래스 확인
2. 클래스명 오타 또는 export 누락 확인
3. MCP 클라이언트 의존성 확인

```python
# 예상 수정 위치: src/mcp/client.py
class SampleMCPClient:
    # ... 구현
    
# 또는 __init__.py에서 export
from .client import SampleMCPClient
```

---

## 📝 참고: Azure OpenAI 설정 (정상 동작 확인)

Agent Team에서 공유해주신 Azure OpenAI 설정으로 라우팅이 정상 동작합니다:

```env
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://oai-az01-sbox-poc-131.openai.azure.com/
AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

---

## 📞 요청사항

1. `SampleMCPClient` import 에러 수정 부탁드립니다
2. 수정 후 Sample Agent 재시작 필요:
   ```bash
   docker restart kjarvis-sample-agent
   ```
3. 수정 완료 시 응답 문서 부탁드립니다

---

---

## 🔴 추가 에러 발견 (2025-12-19 15:43)

### 새로운 에러 로그
```
2025-12-19 06:43:07.330 | ERROR | src.agent.langgraph_agent:initialize:166 - 
Failed to initialize MCP tools: No module named 'mcp'

2025-12-19 06:43:07.330 | ERROR | src.agent.a2a_server:tasks_send:378 - 
[/tasks/send] Error: No module named 'mcp'
```

### 원인
- `mcp` 파이썬 패키지가 Docker 컨테이너에 설치되어 있지 않음
- `requirements.txt`에 `mcp` 패키지 누락 가능

### 해결 방안
```bash
# requirements.txt에 추가
mcp>=1.0.0

# 또는 Docker 이미지 재빌드
docker-compose build kjarvis-sample-agent
docker-compose up -d kjarvis-sample-agent
```

---

## 🔴 3차 에러 발견 (2025-12-19 15:50)

### 최신 에러 로그
```
2025-12-19 06:50:20.212 | ERROR | src.agent.langgraph_agent:initialize:166 - 
Failed to initialize MCP tools: cannot import name 'get_settings' from 'src.config' (/app/src/config.py)

2025-12-19 06:50:20.212 | ERROR | src.agent.a2a_server:tasks_send:378 - 
[/tasks/send] Error: cannot import name 'get_settings' from 'src.config' (/app/src/config.py)
```

### 원인
- `src/config.py`에 `get_settings` 함수가 없음
- MCP Client가 이 함수를 import 하려고 함

### 해결 방안
```python
# src/config.py에 추가 필요
def get_settings():
    return Settings()

# 또는 Settings 클래스 인스턴스를 직접 export
settings = Settings()
```

**빠른 수정 부탁드립니다!**

---

**Orchestrator Team 드림**

