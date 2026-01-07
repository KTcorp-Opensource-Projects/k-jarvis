# K-Jarvis 오픈소스 전략 공유

**작성일**: 2026-01-07  
**작성팀**: Orchestrator Team  
**수신**: Agent Team, MCPHub Team

---

## 📋 요약

K-Jarvis 에코시스템을 KT 이름으로 오픈소스로 배포하기 위한 전략입니다.

---

## 🎯 목표

1. **K-Jarvis 에코시스템 공개** - KT의 AI 에이전트 플랫폼을 오픈소스로 공개
2. **개발자 생태계 확장** - A2A/MCP 표준 기반으로 누구나 쉽게 에이전트/MCP 서버 개발
3. **커뮤니티 구축** - 글로벌 개발자 커뮤니티와 함께 성장

---

## 🏢 GitHub Organization

### 권장: `kt-jarvis` Organization 생성

**이유:**
- 기업 공식 프로젝트 신뢰도
- 팀별 권한 관리
- 브랜딩 일관성

### Repository 구조

```
kt-jarvis (Organization)
├── k-jarvis              # 오케스트레이터 (Orchestrator Team)
├── k-auth                # 인증 서버 (Orchestrator Team)
├── k-arc                 # MCP 허브 (MCPHub Team)
├── agent-catalog         # 에이전트 카탈로그 (Orchestrator Team)
├── k-jarvis-agents       # 샘플 에이전트 (Agent Team)
├── k-jarvis-mcp-servers  # 샘플 MCP 서버 (MCPHub Team)
├── k-jarvis-docs         # 공식 문서 (공동)
└── k-jarvis-examples     # 예제 프로젝트 (공동)
```

---

## ⚖️ 라이선스

### Apache License 2.0 (권장)

| 장점 |
|------|
| ✅ 기업 친화적 (상업적 사용 자유) |
| ✅ 특허 보호 |
| ✅ 수정본 소스 공개 의무 없음 |
| ✅ Google, Microsoft 등 대기업이 선호 |

**⚠️ 모든 프로젝트에 동일 라이선스 적용 권장**

---

## 🔒 Credential 제거 (필수!)

### 즉시 조치 필요

각 팀은 공개 전에 다음을 제거해야 합니다:

| 제거 항목 | 예시 |
|----------|------|
| API Keys | OpenAI, Azure, Anthropic, Google |
| Database 비밀번호 | PostgreSQL, Redis |
| JWT Secret | 토큰 서명 키 |
| OAuth Secrets | Client Secret |
| 내부 URL | 회사 내부 서버 주소 |

### .env.example 필수

```env
# 실제 .env 파일은 .gitignore에 포함
# .env.example만 공개

LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here  # 실제 키 아님
```

### Git History 정리

기존 커밋에 키가 있다면 제거 필요:

```bash
# BFG Repo-Cleaner 사용
java -jar bfg.jar --replace-text secrets.txt repo.git
```

---

## 🤖 멀티 LLM 지원 (구현 완료)

K-Jarvis Orchestrator에서 4개 LLM 프로바이더를 지원합니다:

| Provider | 상태 | 환경변수 |
|----------|------|----------|
| OpenAI | ✅ 완료 | `OPENAI_API_KEY` |
| Azure OpenAI | ✅ 완료 | `AZURE_OPENAI_*` |
| Anthropic Claude | ✅ 완료 | `ANTHROPIC_API_KEY` |
| Google Gemini | ✅ 완료 | `GOOGLE_API_KEY` |

**사용자는 `.env`에서 `LLM_PROVIDER`를 선택하여 원하는 LLM 사용**

---

## 📚 문서화 요청

### 각 팀 작업 요청

#### Agent Team

1. **README.md** - k-jarvis-agents 저장소용
2. **Agent 개발 가이드** - A2A 표준 에이전트 만들기
3. **샘플 에이전트 정리** - 불필요한 코드 제거

#### MCPHub Team

1. **README.md** - k-arc 저장소용
2. **MCP 서버 개발 가이드** - MCP 표준 서버 만들기
3. **샘플 MCP 서버 정리** - 불필요한 코드 제거

---

## 📅 예상 일정

| Phase | 기간 | 작업 | 담당 |
|-------|------|------|------|
| 1. 준비 | 1-2주 | GitHub Org, Repo 설정 | 공동 |
| 2. 코드 정리 | 2-3주 | Credential 제거, 코드 정리 | 각 팀 |
| 3. 문서화 | 2주 | README, 가이드 작성 | 각 팀 |
| 4. CI/CD | 1주 | GitHub Actions, Docker | 공동 |
| 5. 릴리즈 | 1주 | v1.0.0 배포 | 공동 |

**총 예상: 8-10주**

---

## ✅ 각 팀 체크리스트

### Orchestrator Team (우리)

- [x] 오픈소스 전략 문서 작성
- [x] 멀티 LLM 지원 구현
- [x] README.md 작성
- [x] CONTRIBUTING.md 작성
- [x] LICENSE 파일 생성
- [ ] .gitignore 업데이트
- [ ] Git History 검토

### Agent Team

- [ ] .env 파일에서 실제 키 제거
- [ ] .env.example 작성
- [ ] README.md 작성
- [ ] 샘플 에이전트 코드 정리
- [ ] 에이전트 개발 가이드 작성

### MCPHub Team

- [ ] .env 파일에서 실제 키 제거
- [ ] .env.example 작성
- [ ] README.md 작성 (K-ARC 브랜딩)
- [ ] 샘플 MCP 서버 코드 정리
- [ ] MCP 서버 개발 가이드 작성

---

## 📞 논의 필요 사항

1. **GitHub Organization 이름** - `kt-jarvis` vs `kt-opensource` vs 다른 이름?
2. **배포 시점** - 언제 공개할 것인가?
3. **커뮤니티 채널** - Discord? Slack? GitHub Discussions만?
4. **각 팀별 담당자 지정**

---

## 📎 참고 자료

- [오픈소스 전략 상세 문서](docs/OPENSOURCE_STRATEGY.md)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- [GitHub Organization 설정 가이드](https://docs.github.com/en/organizations)

---

**피드백 부탁드립니다!**

각 팀의 의견을 문서로 공유해 주세요.

