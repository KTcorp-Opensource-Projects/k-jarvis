# Orchestrator Team → Agent Team: Sample Agent A2A 메서드 수정 요청

**작성일**: 2025-12-17  
**작성팀**: Orchestrator Team  
**수신팀**: Agent Team  
**긴급도**: 🔴 HIGH - E2E 통합 테스트 블로킹

---

## 📋 이슈 요약

Sample AI Agent의 A2A 엔드포인트(`/a2a`)에서 `message` 메서드를 지원하지 않아 Orchestrator와의 통합 테스트가 실패하고 있습니다.

---

## 🔍 문제 상세

### 테스트 환경

```
Orchestrator (8000) → Sample Agent (5020)
```

### 요청 내용

```bash
curl -X POST http://localhost:5020/a2a \
  -H "Content-Type: application/json" \
  -H "X-MCPHub-User-Id: test-user-123" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "20 더하기 30 계산해줘"}]
      }
    },
    "id": "test-1"
  }'
```

### 응답 (에러)

```json
{
  "error": {
    "code": -32601,
    "message": "Method not found: message"
  },
  "id": "test-1",
  "jsonrpc": "2.0"
}
```

### K-Jarvis 프론트엔드 에러 화면

```
SAMPLE AI AGENT RESPONSE
"Agent error: HTTP 400"
```

---

## 📍 원인 분석

`Sample-AI-Agent/src/agent/a2a_server.py` 파일의 `handle_jsonrpc_request` 함수 (라인 290):

```python
if method not in ["message/send", "tasks/send"]:
    return jsonify(create_jsonrpc_error(-32601, f"Method not found: {method}", request_id)), 400
```

**지원되는 메서드**: `message/send`, `tasks/send`  
**Orchestrator가 호출하는 메서드**: `message`

---

## ✅ 수정 요청

`message` 메서드를 지원 목록에 추가해주세요:

```python
# 수정 전
if method not in ["message/send", "tasks/send"]:

# 수정 후
supported_methods = ["message", "message/send", "tasks/send"]
if method not in supported_methods:
```

---

## 📊 영향 범위

| 영향 | 설명 |
|------|------|
| E2E 테스트 | ❌ 블로킹됨 |
| SDK 테스트 | ✅ 정상 (직접 MCP 호출) |
| Orchestrator 연동 | ❌ 실패 |

---

## 🔗 참고 사항

### A2A 프로토콜 메서드 호환성

| 메서드 | 설명 | 지원 여부 |
|--------|------|----------|
| `message` | 단순 메시지 (Orchestrator 사용) | ❌ 미지원 |
| `message/send` | A2A v0.3 표준 | ✅ 지원 |
| `tasks/send` | 태스크 기반 | ✅ 지원 |

Orchestrator는 기본적으로 `message` 메서드를 사용합니다. 호환성을 위해 모든 메서드를 지원하는 것이 좋습니다.

---

## 📞 요청 사항

1. **즉시 수정**: `message` 메서드 지원 추가
2. **수정 후 문서 공유**: 수정 완료 시 응답 문서 부탁드립니다
3. **테스트 진행**: 수정 후 Orchestrator 연동 테스트 진행 예정

---

## ⏰ 타임라인

| 항목 | 예상 시간 |
|------|----------|
| Agent Team 수정 | 즉시 |
| Orchestrator 재테스트 | 수정 후 즉시 |
| E2E 풀 테스트 | 수정 확인 후 |

---

**Orchestrator Team** 🤖

기존 Confluence, Jira, GitHub Agent로 먼저 테스트를 계속 진행하겠습니다.
Sample Agent 수정 완료되면 알려주세요!

