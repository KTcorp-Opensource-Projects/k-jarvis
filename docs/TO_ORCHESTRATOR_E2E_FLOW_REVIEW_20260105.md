# Agent Team E2E 플로우 검토 및 피드백

**작성일**: 2026-01-05  
**작성팀**: Agent Team  
**대상**: Orchestrator Team, MCPHub Team  
**상태**: ✅ 검토 완료

---

## 📋 검토 문서

`TO_ALL_TEAMS_E2E_TEST_SUCCESS_AND_REVIEW_REQUEST_20260105.md`

---

## 🎉 E2E 테스트 성공 축하

전체 플로우가 정상 동작한 것을 확인했습니다. 각 팀의 노력에 감사드립니다.

---

## 🔍 Agent Team 검토 결과

### 질문 1: MCPHub 연동이 정상 동작했나요?

**답변**: ✅ **정상 동작 확인**

| 항목 | 상태 | 비고 |
|------|------|------|
| MCP 도구 호출 | ✅ 성공 | `github_list_pull_requests` |
| X-MCPHub-User-Id 헤더 포워딩 | ✅ 성공 | 오케스트레이터에서 전달받은 값 그대로 전달 |
| tools/list 조회 | ✅ 성공 | 58개 도구 |
| tools/call 호출 | ✅ 성공 | 실제 GitHub PR 데이터 반환 |

---

### 질문 2: 현재 플로우에서 문제점이 있나요?

**답변**: ⚠️ **몇 가지 개선 필요 사항 있음**

#### 문제점 1: 네트워크 수동 연결 필요

```
현재: 에이전트가 mcphub_kjarvis-network에만 연결
문제: MCPHub와 통신하려면 mcphub_default에 수동 연결 필요
```

**제안**:
```yaml
# docker-compose.agents.yml
networks:
  mcphub_default:
    external: true
  mcphub_kjarvis-network:
    external: true

services:
  github-agent:
    networks:
      - mcphub_default        # MCPHub 통신용
      - mcphub_kjarvis-network # Orchestrator 통신용
```

**심각도**: 🟡 중간 (운영 환경에서는 자동화 필요)

---

#### 문제점 2: 타임아웃 설정 미흡

```python
# 현재 Agent MCP Client
self._http_client = httpx.AsyncClient(timeout=30.0)
```

**우려**:
- LLM 응답이 느릴 경우 30초 초과 가능
- 복잡한 도구 호출 시 타임아웃 발생 가능

**제안**:
```python
# 도구별 타임아웃 설정
TOOL_TIMEOUTS = {
    "github_list_pull_requests": 60.0,
    "jira_search": 45.0,
    "confluence_search": 45.0,
    "default": 30.0
}
```

**심각도**: 🟡 중간 (프로덕션 전 개선 필요)

---

#### 문제점 3: 에러 핸들링 부족

```python
# 현재: 단순 예외 처리
except Exception as e:
    logger.error(f"MCP Request error: {e}")
    return None
```

**우려**:
- MCPHub 장애 시 사용자에게 명확한 에러 메시지 전달 안됨
- 재시도 로직 없음

**제안**:
```python
# 개선된 에러 핸들링
class MCPError(Exception):
    def __init__(self, code: int, message: str, retryable: bool = False):
        self.code = code
        self.message = message
        self.retryable = retryable

# 재시도 로직 추가
@retry(max_attempts=3, backoff=exponential)
async def call_tool(self, name: str, arguments: dict):
    ...
```

**심각도**: 🟡 중간 (안정성 향상 필요)

---

### 질문 3: 다른 에이전트도 동일한 방식으로 동작하나요?

**답변**: ⚠️ **부분적으로만 동작**

| 에이전트 | 상태 | 문제점 |
|---------|------|--------|
| GitHub Agent | ✅ 정상 | - |
| Sample Agent | ✅ 정상 | - |
| Confluence Agent | ⏳ 대기 | Atlassian MCP Server 연결 안됨 |
| Jira Agent | ⏳ 대기 | Atlassian MCP Server 연결 안됨 |

**원인**: `mcp-atlassian` MCP Server가 MCPHub에서 `Reconnecting` 상태

**MCPHub 팀 확인 필요**: Atlassian MCP Server 연결 복구 일정

---

## 🔐 보안 관점 검토

### X-MCPHub-User-Id 헤더 보안

| 항목 | 현재 상태 | 위험도 | 제안 |
|------|----------|--------|------|
| 헤더 위변조 가능성 | 🔴 있음 | 높음 | 서명 또는 암호화 필요 |
| 내부 네트워크 통신 | ✅ Docker 네트워크 | 낮음 | 현재 수준 유지 |
| 에이전트 Key 노출 | 🟡 환경변수 저장 | 중간 | Secret Manager 검토 |

**냉정한 의견**:

현재 `X-MCPHub-User-Id` 헤더는 **단순 문자열**로 전달됩니다. 내부 Docker 네트워크에서는 괜찮지만, **프로덕션 환경**에서는 다음 위험이 있습니다:

1. **헤더 위변조**: 악의적인 에이전트가 다른 사용자 ID를 전달할 수 있음
2. **중간자 공격**: HTTP 통신 시 헤더 탈취 가능

**제안**:
```
방안 1: K-Auth JWT 토큰을 그대로 전달 (MCPHub가 검증)
방안 2: X-MCPHub-User-Id에 서명 추가 (HMAC)
방안 3: mTLS 적용 (서비스 간 상호 인증)
```

**우선순위**: 프로덕션 배포 전 반드시 해결 필요

---

## 📊 플로우 검증 의견

### 현재 플로우가 올바른가?

**답변**: ✅ **기본 구조는 올바름, 세부 사항 개선 필요**

```
[사용자] → [K-Auth] → [Orchestrator] → [Agent] → [MCPHub] → [MCP Server]
                            ↓
                    X-MCPHub-User-Id
```

**올바른 점**:
1. ✅ K-Auth SSO로 통합 인증
2. ✅ Orchestrator가 라우팅 담당
3. ✅ Agent가 도구 호출 담당
4. ✅ MCPHub가 토큰 관리 담당
5. ✅ User-Context로 사용자별 토큰 사용

**개선 필요한 점**:
1. ⚠️ X-MCPHub-User-Id 보안 강화
2. ⚠️ 네트워크 자동 구성
3. ⚠️ 에러 핸들링 및 재시도 로직
4. ⚠️ 타임아웃 설정 최적화

---

## ❓ 역질문

### Orchestrator 팀에게

1. **K-Auth JWT 토큰을 에이전트까지 전달할 수 있나요?**
   - 현재: User ID만 전달
   - 제안: JWT 토큰 전달 → MCPHub가 직접 검증

2. **에이전트 선택 로직은 어떻게 되나요?**
   - 키워드 기반? LLM 기반?
   - 여러 에이전트가 필요한 경우 어떻게 처리?

3. **에이전트 응답 타임아웃은 어떻게 설정되어 있나요?**
   - 현재 값?
   - 조정 가능?

### MCPHub 팀에게

1. **Atlassian MCP Server 연결 복구 일정은?**
   - 현재 `Reconnecting` 상태
   - Jira/Confluence Agent 테스트 대기 중

2. **X-MCPHub-User-Id 대신 K-Auth JWT 검증이 가능한가요?**
   - 보안 강화 목적
   - 구현 난이도?

3. **에이전트별 MCPHub Key 발급 절차는?**
   - 현재 테스트용 공용 Key 사용 중
   - 프로덕션용 Key 발급 필요

---

## 📝 Agent Team 액션 아이템

| 항목 | 우선순위 | 예상 일정 |
|------|----------|----------|
| 네트워크 설정 자동화 (docker-compose 수정) | 높음 | 1일 |
| 타임아웃 설정 최적화 | 중간 | 1일 |
| 에러 핸들링 개선 | 중간 | 2일 |
| Atlassian Agent 테스트 (MCP Server 복구 후) | 높음 | 대기 |

---

## 🎯 결론

### 현재 상태

| 항목 | 평가 |
|------|------|
| **기능 동작** | ✅ 정상 |
| **아키텍처** | ✅ 적절 |
| **보안** | ⚠️ 개선 필요 |
| **안정성** | ⚠️ 개선 필요 |
| **운영 편의성** | ⚠️ 개선 필요 |

### 냉정한 평가

**E2E 플로우 자체는 올바른 방향**입니다. 그러나 **프로덕션 배포 전**에 다음 사항이 반드시 해결되어야 합니다:

1. **보안**: X-MCPHub-User-Id 헤더 위변조 방지
2. **안정성**: 에러 핸들링, 재시도 로직, 타임아웃 최적화
3. **운영**: 네트워크 자동 구성, 모니터링, 로깅

**현재 수준**: 개발/테스트 환경에 적합  
**프로덕션 준비 수준**: 60% (보안 및 안정성 개선 필요)

---

## 📞 연락처

**Agent Team**  
Slack: #agent-dev

---

**피드백 감사합니다. 추가 논의가 필요하시면 연락주세요.** 🙏

