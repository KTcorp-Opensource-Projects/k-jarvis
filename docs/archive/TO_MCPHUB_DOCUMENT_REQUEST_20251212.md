# 📝 MCPHub 팀 문서 작성 요청

**작성일**: 2024-12-12  
**작성팀**: Orchestrator Team  
**수신팀**: MCPHub Team

---

## 📋 요청 사항

Orchestrator 팀에서 **Agent 등록 가이드** 문서를 작성 완료했습니다.

**MCPHub 팀도 동일한 포맷으로 MCP Server 등록 가이드 문서를 작성해주세요.**

---

## 📄 참고 문서

**Orchestrator 작성 문서**: `Agent-orchestrator/docs/AGENT_REGISTRATION_GUIDE.md`

---

## 📐 문서 포맷 (동일하게 작성 요청)

```markdown
# 🔌 MCPHub MCP Server 등록 가이드

**버전**: 1.0.0  
**최종 수정일**: 2024-12-12  
**작성팀**: MCPHub Team

---

## 📋 개요
(MCP Server를 MCPHub에 등록하는 방법 설명)

---

## 🏗️ 아키텍처 개요
(ASCII 다이어그램으로 전체 구조 설명)

---

## ✅ 필수 요구사항

### 1. MCP Protocol 엔드포인트
(필수 엔드포인트 테이블)

### 2. Server 정보 JSON 구조
(필수 필드와 예시)

### 3. 필수 필드 설명
(각 필드별 상세 설명 테이블)

---

## 🔌 API 스펙

### tools/list
(요청/응답 예시)

### tools/call
(요청/응답 예시)

---

## 🔐 환경변수 템플릿

### 사용자별 토큰 설정 방법
(${VARIABLE_NAME} 형식 설명)

### 예시
```
headers:
  Authorization: "Bearer ${GITHUB_TOKEN}"
```

---

## 🛠️ 등록 절차

### 방법 1: Admin UI에서 등록
(스크린샷 또는 단계별 설명)

### 방법 2: API로 등록
(curl 예시)

---

## 🧪 테스트 체크리스트
(등록 전 확인사항)

---

## ❌ 에러 코드
(에러 코드별 설명)

---

## 📚 참고 자료
(관련 링크)
```

---

## 📌 필수 포함 내용

MCPHub MCP Server 등록 가이드에 **반드시 포함되어야 할 내용**:

| # | 항목 | 설명 |
|---|------|------|
| 1 | **MCP Server 등록 방법** | Admin UI 또는 API를 통한 등록 절차 |
| 2 | **필수 필드 정의** | name, url, headers 등 필수 정보 |
| 3 | **환경변수 템플릿** | `${GITHUB_TOKEN}` 형식 사용법 |
| 4 | **카탈로그 등록** | isMarketplace, 카테고리, 태그 설정 |
| 5 | **사용자 토큰 저장 위치** | user_server_subscriptions.settings.envVariables |
| 6 | **X-MCPHub-User-Id 처리** | Agent에서 전달받은 헤더 처리 방법 |
| 7 | **에러 코드** | 토큰 미등록, 서버 연결 실패 등 |
| 8 | **테스트 체크리스트** | 등록 전 확인사항 |

---

## 🎯 목적

이 문서의 목적:
1. **새로운 MCP Server 개발자**가 MCPHub에 서버를 등록하는 방법을 쉽게 이해
2. **Agent 개발자**가 필요한 MCP Server가 MCPHub에 없을 때 등록 요청 방법 안내
3. **운영팀**이 서버 등록/관리 절차를 표준화

---

## ⏰ 요청 마감

**마감일**: 가능한 빠른 시일 내

---

## 💬 문의

질문이 있으시면 Orchestrator 팀에 문의해주세요.

---

*Orchestrator Team*  
*2024-12-12*

