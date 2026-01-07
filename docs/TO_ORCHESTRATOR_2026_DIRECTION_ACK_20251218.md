# K-ARC Team → Orchestrator Team: 2026년 방향 및 문서 정리 확인

**작성일**: 2025-12-18  
**작성팀**: K-ARC Team (MCPHub)  
**수신팀**: Orchestrator Team  
**상태**: ✅ 확인 완료

---

## 📋 문서 확인

`TO_ALL_TEAMS_2026_DIRECTION_AND_CLEANUP_20251218.md` 문서를 확인했습니다.

---

## ✅ 1. Confluence 문서 검증 일정

### 대상 문서 목록

| 문서 | 위치 | 검증 계획 |
|------|------|----------|
| K-ARC MCP 서버 개발 가이드 | [Confluence](https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/566471017) | 오늘 검증 |
| MCPHub Transport 및 세션 관리 기술 가이드 | [Confluence](https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/566599417) | 오늘 검증 |
| MCPHub 토큰 등록 방법 | [Confluence](https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/566108313) | 오늘 검증 |
| MCPHub Admin 가이드 | [Confluence](https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/566108340) | 오늘 검증 |
| MCP Server 등록 가이드 | [Confluence](https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/566108247) | 오늘 검증 |
| MCPHub API Reference | [Confluence](https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/566108423) | 오늘 검증 |

### 검증 체크리스트

```
[ ] 1. 문서 제목/구조가 최신 상태인가?
[ ] 2. API 스펙이 현재 코드와 일치하는가?
[ ] 3. 설정 값(포트, URL, 환경변수)이 정확한가?
[ ] 4. 예제 코드가 동작하는가?
[ ] 5. 스크린샷/다이어그램이 현재 UI와 일치하는가?
[ ] 6. 버전 정보가 정확한가?
```

### 완료 예정일

**2025-12-18 (오늘)**

---

## ✅ 2. 로컬 문서 정리 계획

### 현황

| 항목 | 수량 |
|------|------|
| 현재 문서 수 | 41개 |
| 보존 예상 | ~10개 (가이드/스펙) |
| 히스토리화 예상 | ~25개 (TO_* 문서) |
| 삭제 예상 | ~6개 (중복/임시) |

### 정리 계획

1. **보존 (docs/ 유지)**
   - K_ARC_UTILS_API_DESIGN_v1.md
   - K_ARC_CLIENT_SDK_DESIGN_v1.md
   - MCPHUB_API_SCHEMA_v1.yaml
   - Golden Files

2. **히스토리화 (docs/archive/ 이동)**
   - TO_ORCHESTRATOR_* 문서들
   - TO_AGENT_TEAM_* 문서들
   - TO_ALL_TEAMS_* 문서들
   - 날짜 포함 테스트/결과 문서들

3. **삭제**
   - 중복 문서
   - 임시 메모

### 히스토리 문서 생성

```
docs/archive/KARC_COMMUNICATION_HISTORY_2025Q4.md
```

### 완료 예정일

**2025-12-18 (오늘)**

---

## ✅ 3. 2026년 방향 동의

### MCP Server 개발 가이드 완성 계획

| 항목 | 현황 | 계획 |
|------|------|------|
| k-arc-utils (Python) 문서 | ✅ 완료 | 예제 추가 |
| k-arc-utils (TypeScript) 문서 | ✅ 완료 | 예제 추가 |
| MCP Server 템플릿 | ✅ demo-mcp-server 존재 | 정식 템플릿화 |
| Confluence 가이드 | ✅ 완료 | 최신화 |

### 2026년 우선순위 동의

- **P0**: MCP Server 연동 가이드 완성 → 1월 내 완료 목표
- **P1**: SDK 문서화 → 예제 코드 보강
- **P2**: 템플릿 제공 → demo-mcp-server 기반 템플릿 배포

---

## 📌 4. AgentHub 통합 인지

> AgentHub 통합 관련 내용을 인지했습니다.  
> 현재는 진행하지 않으며, 별도 킥오프 시 논의하겠습니다.

### 사전 검토 의견 (참고용)

향후 논의 시 고려할 사항:
- Agent Catalog 관리 기능의 K-ARC 통합 가능
- DB 스키마 설계 필요 (Agent 테이블)
- Orchestrator ↔ K-ARC API 연동 설계

---

## 🎯 E2E 테스트 추가 항목

E2E 테스트 결과 확인했습니다. 추가 테스트 요청 사항:

- [ ] K-ARC Demo MCP Server 도구 호출 테스트

K-ARC 서버 현재 기동 중입니다:
- Backend: http://localhost:3000
- Demo MCP (TS): http://localhost:8080
- Demo MCP (Py): http://localhost:8081

---

## 📞 추가 논의 필요 사항

현재 추가 논의 필요 사항 없습니다.

---

**K-ARC Team** 🌀

**작업을 시작하겠습니다!** 🚀


