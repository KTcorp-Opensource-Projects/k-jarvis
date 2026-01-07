# K-ARC Team → All Teams: k-arc-utils Python SDK 문서화 완료

**작성일**: 2025-12-17  
**작성팀**: K-ARC Team  
**수신팀**: Agent Team, Orchestrator Team, 모든 MCP 서버 개발자

---

## 📢 공지

MCP 서버 개발자를 위한 **k-arc-utils Python SDK** 문서화가 완료되었습니다!

---

## 📚 생성된 문서

### 1. Confluence 문서 (공식 가이드)

| 문서 | URL |
|------|-----|
| **K-ARC MCP 서버 개발 가이드** | https://ktspace.atlassian.net/wiki/spaces/CNCORE/pages/566471017 |

**포함 내용**:
- K-ARC 아키텍처 개요
- k-arc-utils 설치 방법
- 핵심 개념 (헤더, 서비스 토큰, 에러 코드)
- 완전한 API 레퍼런스
- 전체 MCP 서버 예제 코드
- K-ARC 등록 절차
- 베스트 프랙티스
- 문제 해결 가이드

### 2. GitHub README

| 항목 | 위치 |
|------|------|
| **k-arc-utils README** | `/chihoon/k-arc-utils-python/README.md` |

**개선된 내용**:
- 개요 및 아키텍처 다이어그램
- 빠른 시작 가이드
- 상세 API 레퍼런스
- 전체 예제 코드
- 문제 해결 섹션

---

## 🎯 k-arc-utils란?

K-ARC 플랫폼에 등록되는 **MCP 서버 개발자**를 위한 공식 Python SDK입니다.

### 주요 기능

| 모듈 | 기능 |
|------|------|
| `headers` | K-ARC Gateway가 전달하는 사용자 정보/토큰 추출 |
| `validation` | 환경변수 스키마 검증 및 타입 변환 |
| `errors` | 표준 에러 코드 (k-jarvis-utils 호환) |

### 빠른 예시

```python
from k_arc_utils import (
    create_user_context,
    KARCError,
    MCPErrorCode,
)

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    # 사용자 컨텍스트 생성
    ctx = create_user_context(request.headers)
    
    # 인증 확인
    if not ctx.is_authenticated:
        raise KARCError(MCPErrorCode.NO_SERVICE_TOKEN, "인증 필요")
    
    # 서비스 토큰 확인
    if not ctx.has_tokens("JIRA_TOKEN"):
        raise KARCError(MCPErrorCode.NO_SERVICE_TOKEN, "JIRA_TOKEN 필요")
    
    # 토큰 사용
    jira_token = ctx.get_token("JIRA_TOKEN")
    # ... Jira API 호출
```

---

## 📦 설치 방법

```bash
# PyPI에서 설치 (권장)
pip install k-arc-utils

# 개발 모드 설치
git clone https://github.com/OG056501-Opensource-Poc/k-arc-utils-python.git
cd k-arc-utils-python
pip install -e ".[dev]"
```

---

## 🔗 관련 패키지

| 패키지 | 대상 | 언어 |
|--------|------|------|
| **k-arc-utils** | MCP 서버 개발자 | Python |
| **k-jarvis-utils** | Agent 개발자 | Python |
| **k-arc-utils (TS)** | K-ARC 내부 | TypeScript |

**에러 코드는 모든 패키지에서 호환됩니다!**

---

## 📂 소스 코드 위치

| 항목 | 경로 |
|------|------|
| k-arc-utils (Python) | `/chihoon/k-arc-utils-python` |
| 데모 MCP 서버 (Python) | `/chihoon/demo-mcp-server-python` |
| k-arc-utils (TypeScript) | `/chihoon/k-arc-utils` |

---

## 📋 다음 단계

1. ✅ k-arc-utils Python SDK 개발 완료
2. ✅ Confluence 문서 작성 완료
3. ✅ README.md 상세화 완료
4. 🔜 PyPI 배포 (레포지토리 확정 후)
5. 🔜 MCP 서버 거버넌스 문서 작성 (12/18)

---

## 📞 문의

MCP 서버 개발 관련 질문이 있으면 언제든 문의해주세요!

---

**K-ARC Team** 🌀

