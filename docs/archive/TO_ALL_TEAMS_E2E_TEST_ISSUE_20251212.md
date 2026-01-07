# 🚨 E2E 통합 테스트 이슈 공유

**작성일**: 2024-12-12  
**작성팀**: Orchestrator Team  
**긴급도**: 🔴 높음

---

## 📋 테스트 현황

### 완료된 항목 ✅
1. K-Auth 회원가입 페이지 구현 및 테스트 완료
2. K-Auth → Orchestrator SSO 로그인 정상
3. Orchestrator → Agent 호출 정상

### 미완료 항목 ❌
4. **MCPHub 서비스 토큰 등록 플로우** 테스트 불가
5. **실제 외부 API 호출** 테스트 불가

---

## 🔴 발견된 이슈

### Issue #1: 신규 사용자 MCPHub 서비스 토큰 등록 플로우 부재

**상황:**
- 신규 사용자 `johndoe`가 K-Auth 회원가입 후 Orchestrator SSO 로그인 성공
- Confluence Agent에 "스페이스 목록 알려줘" 요청
- Agent 응답: **"현재 MCP Hub 연결이 없어 실제 Confluence 인스턴스의 스페이스 목록을 직접 조회할 수 없습니다."**

**원인:**
```
johndoe 사용자가 MCPHub에:
1. 계정이 없음 (SSO 로그인 미수행)
2. 서비스 토큰 미등록 (Confluence/Jira/GitHub)
```

**질문 (MCPHub 팀):**
1. 신규 사용자가 MCPHub에 서비스 토큰을 등록하는 **UI 또는 API**가 있나요?
2. MCPHub K-Auth SSO 로그인이 구현되어 있나요?
3. 사용자가 토큰을 등록하는 절차가 어떻게 되나요?

---

### Issue #2: 사용자 온보딩 가이드 부재

**상황:**
- 사용자가 처음 로그인 후 어디서 서비스 토큰을 등록해야 하는지 모름
- Agent가 "토큰이 없어서 안됨"이라고만 응답

**필요한 것:**
1. Orchestrator에서 "MCPHub에서 토큰 등록하세요" 안내
2. MCPHub 대시보드 링크 제공
3. 토큰 등록 가이드 문서

---

## ❓ 각 팀에 질문

### MCPHub 팀에게

1. **MCPHub 웹 UI**가 있나요? 주소가 뭔가요?
   - `http://localhost:3000/` → "Route not found" 오류

2. **신규 사용자 토큰 등록 API**는 어떻게 되나요?
   ```
   POST /api/v1/service-tokens?
   ```

3. K-Auth SSO로 MCPHub 로그인 시 **자동 계정 생성**이 되나요?

### Agent 팀에게

1. MCPHub 토큰이 없을 때 **더 명확한 에러 메시지**를 줄 수 있나요?
   - 현재: "MCP Hub 연결이 없어..."
   - 개선: "MCPHub에서 Confluence 토큰을 등록해주세요. [링크]"

---

## 🎯 E2E 완료를 위한 필요사항

```
┌─────────────────────────────────────────────────────────────────┐
│  현재 테스트 진행 상황                                           │
│                                                                 │
│  [✅] K-Auth 회원가입                                           │
│       ↓                                                         │
│  [✅] Orchestrator K-Auth SSO 로그인                            │
│       ↓                                                         │
│  [❓] MCPHub K-Auth SSO 로그인 ← MCPHub팀 확인 필요             │
│       ↓                                                         │
│  [❓] MCPHub 서비스 토큰 등록 ← MCPHub팀 확인 필요              │
│       ↓                                                         │
│  [⏳] Orchestrator에서 Agent 호출 (실제 API)                    │
│       ↓                                                         │
│  [⏳] E2E 완료                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 테스트 계정 정보

| 항목 | 값 |
|------|-----|
| K-Auth Username | `johndoe` |
| K-Auth Email | `john.doe@company.com` |
| K-Auth Password | `SecurePass123!` |
| K-Auth User ID | `8233afac-365f-4086-8c99-72c2037c32b8` (추정) |

---

## 🚀 다음 단계

1. **MCPHub 팀**: 위 질문에 답변 부탁드립니다
2. **Agent 팀**: 토큰 미등록 시 사용자 안내 개선 검토
3. **Orchestrator 팀**: 답변 받은 후 테스트 계속 진행

**빠른 답변 부탁드립니다!** 🙏

---

*Orchestrator Team*  
*2024-12-12*

