# Orchestrator Team → Agent Team: A2A 프로토콜 불일치 문제

**작성일**: 2025-12-17  
**작성팀**: Orchestrator Team  
**수신팀**: Agent Team  
**긴급도**: 🔴 HIGH - E2E 테스트 블로커

---

## 🔴 문제 상황

Sample Agent가 등록되고 ONLINE 상태이지만, Orchestrator를 통한 채팅에서 **HTTP 400** 에러가 발생합니다.

```
Agent error: HTTP 400
```

---

## 🔍 원인 분석

### Orchestrator가 보내는 A2A 요청

```python
# orchestrator.py 라인 745-750
response = await client.post(
    f"{agent_url}/tasks/send",  # ❌ /tasks/send 엔드포인트 사용
    json=payload,
    headers=headers
)
```

```json
{
  "jsonrpc": "2.0",
  "id": "uuid",
  "method": "message/send",  // ❌ message/send 메서드
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "kind": "text",  // ❌ "kind" 사용
          "text": "메시지"
        }
      ]
    }
  }
}
```

### 직접 테스트로 성공한 요청 (curl)

```json
{
  "jsonrpc": "2.0",
  "method": "message",  // ✅ message 메서드
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",  // ✅ "type" 사용
          "text": "메시지"
        }
      ]
    }
  },
  "id": "test-1"
}
```

---

## 📋 불일치 사항 정리

| 항목 | Orchestrator 전송 | Sample Agent 기대 | 상태 |
|------|------------------|------------------|------|
| **Endpoint** | `/tasks/send` | `/a2a` | ❌ 불일치 |
| **Method** | `message/send` | `message` | ❌ 불일치 |
| **Parts key** | `kind` | `type` | ❌ 불일치 |

---

## 🛠️ 해결 방안

### Option A: Sample Agent 수정 (Agent Team)

Sample Agent가 Orchestrator의 요청 형식도 지원하도록 확장:

1. **`/tasks/send` 엔드포인트** 지원 추가
2. **`message/send` 메서드** 지원 추가  
3. **`kind` 키** 지원 추가 (`type`과 호환)

### Option B: Orchestrator 수정 (Orchestrator Team)

Orchestrator가 Sample Agent 형식으로 요청하도록 수정:

1. `/a2a` 엔드포인트 사용
2. `message` 메서드 사용
3. `type` 키 사용

---

## 📞 요청

**어떤 방식으로 통일할지 결정해주세요:**

1. **Option A**: Sample Agent가 Orchestrator 형식에 맞춤 (권장 - A2A 표준 준수)
2. **Option B**: Orchestrator가 Sample Agent 형식에 맞춤

결정 후 응답 문서 공유 부탁드립니다!

---

## 참고: A2A 표준

A2A 프로토콜 표준에서는:
- 메서드: `message/send` 또는 `tasks/send`
- Parts: `type` 또는 `kind` (둘 다 허용하는 것이 일반적)
- 엔드포인트: Agent Card에 명시된 endpoint 사용

---

**Orchestrator Team** 🤖

