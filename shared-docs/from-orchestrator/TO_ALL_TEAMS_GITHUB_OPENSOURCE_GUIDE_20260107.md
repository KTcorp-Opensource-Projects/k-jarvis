# K-Jarvis 오픈소스 GitHub 연동 가이드

**작성일**: 2026-01-07  
**작성팀**: Orchestrator Team  
**수신**: Agent Team, MCPHub Team  
**긴급도**: 🔴 높음

---

## 📋 개요

K-Jarvis 에코시스템을 별도 프로젝트로 오픈소스 배포합니다.
각 팀은 담당 Repository에 코드를 Push하고 동시에 관리합니다.

---

## 🏢 GitHub Organization 정보

```
Organization: KTcorp-Opensource-Projects
URL: https://github.com/KTcorp-Opensource-Projects
```

---

## 📦 Repository 배정

| Repository | URL | 담당 팀 | 설명 |
|------------|-----|---------|------|
| `k-jarvis` | https://github.com/KTcorp-Opensource-Projects/k-jarvis | Orchestrator Team | A2A 오케스트레이터 |
| `k-arc` | https://github.com/KTcorp-Opensource-Projects/k-arc | MCPHub Team | MCP 허브 |
| `k-auth` | https://github.com/KTcorp-Opensource-Projects/k-auth | Orchestrator Team | OAuth 2.0 인증 서버 |
| `k-agent-example` | https://github.com/KTcorp-Opensource-Projects/k-agent-example | Agent Team | 샘플 에이전트 |

---

## 🔧 GitHub Remote 연결 방법

### 1. 기존 프로젝트에 Remote 추가

```bash
# 기존 프로젝트 디렉토리로 이동
cd /path/to/your/project

# GitHub Public Remote 추가 (이름: public)
git remote add public https://github.com/kt-jarvis/[REPO_NAME].git

# Remote 확인
git remote -v
# origin  https://github.company.com/... (기존 회사 repo)
# public  https://github.com/kt-jarvis/... (새 public repo)
```

### 2. 각 팀별 설정

#### Orchestrator Team (k-jarvis)

```bash
cd /path/to/Agent-orchestrator

# opensource 브랜치로 전환
git checkout opensource/v1.0.0

# Public remote 추가
git remote add public https://github.com/KTcorp-Opensource-Projects/k-jarvis.git

# Push
git push public opensource/v1.0.0:main
```

#### Orchestrator Team (k-auth)

```bash
cd /path/to/k-auth

# Public remote 추가
git remote add public https://github.com/KTcorp-Opensource-Projects/k-auth.git

# Push (main 또는 적절한 브랜치)
git push public main:main
```

#### MCPHub Team (k-arc)

```bash
cd /path/to/mcphub

# Public remote 추가
git remote add public https://github.com/KTcorp-Opensource-Projects/k-arc.git

# Push
git push public main:main
```

#### Agent Team (k-agent-example)

```bash
cd /path/to/sample-agent

# Public remote 추가
git remote add public https://github.com/KTcorp-Opensource-Projects/k-agent-example.git

# Push
git push public main:main
```

---

## 🔐 Push 전 체크리스트

### ⚠️ 반드시 확인!

```
□ .env 파일이 .gitignore에 포함되어 있는가?
□ API Key, Secret이 코드에 하드코딩되어 있지 않은가?
□ 내부 서버 URL/IP가 노출되지 않는가?
□ .env.example 파일이 준비되어 있는가?
□ README.md가 작성되어 있는가?
□ LICENSE 파일이 있는가? (Apache 2.0)
```

### Git History 확인

```bash
# 커밋 히스토리에서 민감 정보 검색
git log -p | grep -i "api_key\|secret\|password" | head -20

# 민감 정보가 있다면 BFG로 제거
# java -jar bfg.jar --replace-text secrets.txt repo.git
```

---

## 🔄 동시 관리 워크플로우

### 일반적인 개발 흐름

```
[회사 Repo (origin)]     [Public Repo (public)]
        │                         │
        │   개발 작업              │
        ▼                         │
   feature branch                 │
        │                         │
        │   코드 리뷰              │
        ▼                         │
   origin/main ──────────────────►│ public/main
        │      (동기화 push)       │
        │                         │
```

### 변경사항 동기화

```bash
# 1. 회사 repo에서 개발 완료 후
git checkout main
git pull origin main

# 2. Public repo에 동기화
git push public main:main
```

### 브랜치 전략

```
origin/main      → 회사 내부 최신
public/main      → 오픈소스 공개 버전

# 동기화는 main → main 으로만
# feature 브랜치는 회사 repo에서만 관리
```

---

## 📝 커밋 메시지 규칙

오픈소스 커밋 시 다음 규칙을 따라주세요:

```
<type>(<scope>): <subject>

[body]

[footer]
```

### Type

| Type | 설명 |
|------|------|
| `feat` | 새로운 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `style` | 코드 포맷팅 |
| `refactor` | 리팩토링 |
| `test` | 테스트 |
| `chore` | 빌드, 설정 |

### 예시

```
feat(router): add Claude LLM support

- Add ClaudeClient implementation
- Update LLMClientFactory with fallback
- Add ANTHROPIC_API_KEY to .env.example

Closes #123
```

---

## 🏷️ 릴리즈 태그

### 버전 규칙 (Semantic Versioning)

```
v{MAJOR}.{MINOR}.{PATCH}

예: v1.0.0, v1.1.0, v1.1.1
```

### 태그 생성

```bash
# 태그 생성
git tag -a v1.0.0 -m "Initial open source release"

# Public repo에 태그 Push
git push public v1.0.0
```

---

## 📅 일정

| 단계 | 일정 | 내용 |
|------|------|------|
| **1. Repo 생성** | 오늘 | Orchestrator Team에서 생성 완료 예정 |
| **2. Remote 연결** | 오늘 | 각 팀 remote 추가 |
| **3. 초기 Push** | 오늘~내일 | 정리된 코드 Push |
| **4. 검증** | 이번 주 | Public repo에서 clone 후 테스트 |
| **5. 공개 발표** | 다음 주 | README, 문서 최종 정리 후 공개 |

---

## ❓ FAQ

### Q: 회사 repo와 public repo 중 어디가 메인인가요?

**A:** 회사 repo가 메인입니다. 개발은 회사 repo에서 하고, 안정 버전을 public으로 동기화합니다.

### Q: 외부 기여자의 PR은 어떻게 처리하나요?

**A:** Public repo의 PR을 검토 후, 회사 repo에 반영하고 다시 동기화합니다.

### Q: 민감 정보가 실수로 Push되면?

**A:** 즉시 알려주세요. GitHub에서 커밋 삭제 후 force push가 필요합니다.

---

## 📞 문의

- **Orchestrator Team**: GitHub 연동, k-jarvis, k-auth 관련
- **MCPHub Team**: k-arc 관련
- **Agent Team**: k-agent-example 관련

---

## ❓ SDK 관련 문의 사항

### 각 팀에서 개발한 SDK 처리 방안

현재 각 팀에서 개발한 SDK가 있습니다:

| 팀 | SDK | 현재 위치 |
|----|-----|----------|
| Orchestrator | `k-jarvis-utils` (Python) | `packages/k-jarvis-utils/` |
| MCPHub | `k-arc-utils` (TypeScript) | 별도 관리? |
| Agent | Agent SDK | 별도 관리? |

### 📋 각 팀 응답 요청

**다음 사항에 대해 의견 부탁드립니다:**

1. **SDK를 별도 Repository로 관리할지?**
   - 예: `k-jarvis-sdk`, `k-arc-sdk`
   
2. **메인 프로젝트에 포함할지?**
   - 예: `k-jarvis/packages/k-jarvis-utils/`

3. **npm/PyPI에 배포할 계획이 있는지?**

**Orchestrator Team 의견:**
- `k-jarvis-utils`는 현재 `k-jarvis` repo의 `packages/` 폴더에 포함
- 사용자가 하나의 repo에서 SDK까지 확인 가능
- PyPI 배포는 추후 검토

**각 팀의 SDK 처리 방안을 문서로 공유해 주세요!**

---

## 📎 Repository URL (확정)

```
Organization: KTcorp-Opensource-Projects

k-jarvis:        https://github.com/KTcorp-Opensource-Projects/k-jarvis
k-arc:           https://github.com/KTcorp-Opensource-Projects/k-arc
k-auth:          https://github.com/KTcorp-Opensource-Projects/k-auth
k-agent-example: https://github.com/KTcorp-Opensource-Projects/k-agent-example
```

---

## ✅ 다음 단계

1. **각 팀**: Remote 추가 및 Push
2. **각 팀**: SDK 처리 방안 응답
3. **Orchestrator Team**: k-jarvis, k-auth Push 완료 후 알림
4. **전체**: Clone 후 테스트

---

**바로 시작해 주세요! 🚀**

