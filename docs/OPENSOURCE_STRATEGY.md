# K-Jarvis Ecosystem 오픈소스 전략

**작성일**: 2026-01-07  
**작성자**: K-Jarvis Team  
**버전**: 1.0.0

---

## 📋 목차

1. [개요](#-개요)
2. [프로젝트 구조](#-프로젝트-구조)
3. [GitHub Organization 설정](#-github-organization-설정)
4. [라이선스 선택](#-라이선스-선택)
5. [보안 점검 (Credential 제거)](#-보안-점검-credential-제거)
6. [멀티 LLM 지원](#-멀티-llm-지원)
7. [문서화 전략](#-문서화-전략)
8. [커뮤니티 관리](#-커뮤니티-관리)
9. [릴리즈 전략](#-릴리즈-전략)
10. [체크리스트](#-체크리스트)

---

## 📌 개요

### 목표

KT 이름으로 K-Jarvis 에코시스템을 오픈소스로 공개하여:
- 개발자들이 A2A/MCP 표준 기반 AI 에이전트를 쉽게 개발
- K-Jarvis 플랫폼에 연동하여 활용
- 오픈소스 커뮤니티와 함께 성장

### 프로젝트 구성

| 프로젝트 | 설명 | 공개 범위 |
|----------|------|-----------|
| **K-Jarvis** | AI 에이전트 오케스트레이터 | ✅ 전체 공개 |
| **K-Auth** | OAuth 2.0 인증 서버 | ✅ 전체 공개 |
| **K-ARC** | MCP 서버 허브 (MCPHub) | ✅ 전체 공개 |
| **Agent Catalog** | 에이전트 카탈로그 | ✅ 전체 공개 |
| **Sample Agents** | 샘플 에이전트 (GitHub, Jira 등) | ✅ 예제로 공개 |
| **Sample MCP Servers** | 샘플 MCP 서버 | ✅ 예제로 공개 |

---

## 📁 프로젝트 구조

### GitHub Organization 구조

```
kt-jarvis (GitHub Organization)
│
├── k-jarvis                    # 메인 오케스트레이터
│   ├── backend/
│   ├── frontend/
│   └── docker-compose.yml
│
├── k-auth                      # 인증 서버
│   ├── backend/
│   └── docs/
│
├── k-arc                       # MCP 허브 (MCPHub 리브랜딩)
│   ├── apps/backend/
│   ├── apps/frontend/
│   └── docker-compose.yml
│
├── agent-catalog               # 에이전트 카탈로그 서비스
│   ├── app/
│   └── docker-compose.yml
│
├── k-jarvis-agents             # 샘플 에이전트 모음
│   ├── github-agent/
│   ├── jira-agent/
│   ├── confluence-agent/
│   └── sample-agent/
│
├── k-jarvis-mcp-servers        # 샘플 MCP 서버 모음
│   ├── github-mcp/
│   ├── atlassian-mcp/
│   └── weather-mcp/
│
├── k-jarvis-sdk                # Python SDK
│   └── k-jarvis-utils/
│
├── k-arc-sdk                   # TypeScript SDK
│   └── k-arc-utils/
│
├── k-jarvis-docs               # 공식 문서 사이트
│   └── (Docusaurus or GitBook)
│
└── k-jarvis-examples           # 예제 프로젝트
    ├── simple-agent/
    ├── mcp-server-template/
    └── full-stack-example/
```

---

## 🏢 GitHub Organization 설정

### 1. Organization 생성

```
이름: kt-jarvis
URL: https://github.com/kt-jarvis
설명: "KT's Open Source AI Agent Orchestration Platform"
```

### 2. Team 구조

```
kt-jarvis (Organization)
├── @kt-jarvis/maintainers     # 핵심 유지보수 팀
├── @kt-jarvis/orchestrator    # K-Jarvis 담당
├── @kt-jarvis/auth            # K-Auth 담당
├── @kt-jarvis/arc             # K-ARC 담당
└── @kt-jarvis/community       # 커뮤니티 관리
```

### 3. Repository 설정

각 저장소에 적용할 설정:

```yaml
# Branch Protection Rules
main:
  - Require pull request reviews (1+)
  - Require status checks to pass
  - Require signed commits (권장)
  
develop:
  - Require pull request reviews (1+)
  - Require status checks to pass
```

---

## ⚖️ 라이선스 선택

### 권장: Apache License 2.0

| 항목 | Apache 2.0 | MIT | GPL 3.0 |
|------|------------|-----|---------|
| 상업적 사용 | ✅ | ✅ | ✅ |
| 수정 배포 | ✅ | ✅ | ⚠️ 소스 공개 필수 |
| 특허 보호 | ✅ | ❌ | ✅ |
| 기업 친화적 | ✅ | ✅ | ❌ |

**Apache 2.0 선택 이유**:
- 기업이 안심하고 사용 가능
- 특허 조항으로 법적 보호
- 수정본 소스 공개 의무 없음
- Google, Microsoft, Apache 재단 등 대기업이 선호

### LICENSE 파일

```
Copyright 2026 KT Corporation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## 🔒 보안 점검 (Credential 제거)

### 1. 제거해야 할 항목

```
[CRITICAL - 반드시 제거]
- API Keys (OpenAI, Azure, Claude, Gemini)
- Database 비밀번호
- JWT Secret Keys
- OAuth Client Secrets
- 내부 서버 URL/IP

[중요 - 환경변수로 대체]
- 모든 서비스 포트
- 데이터베이스 호스트
- Redis 호스트
- 외부 서비스 Endpoint
```

### 2. .env.example 템플릿

```env
# =============================================================================
# K-Jarvis Configuration
# Copy this file to .env and fill in your values
# =============================================================================

# -----------------------------------------------------------------------------
# LLM Provider Configuration
# Supported: openai, azure, claude, gemini
# -----------------------------------------------------------------------------
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-azure-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Google Gemini
GOOGLE_API_KEY=your-google-api-key
GEMINI_MODEL=gemini-1.5-pro

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kjarvis
DB_USER=postgres
DB_PASSWORD=your-secure-password

# -----------------------------------------------------------------------------
# Redis Configuration
# -----------------------------------------------------------------------------
REDIS_URL=redis://localhost:6379/0

# -----------------------------------------------------------------------------
# Authentication (K-Auth)
# -----------------------------------------------------------------------------
JWT_SECRET_KEY=generate-a-secure-random-string
KAUTH_URL=http://localhost:4002
KAUTH_CLIENT_ID=your-oauth-client-id
KAUTH_CLIENT_SECRET=your-oauth-client-secret

# -----------------------------------------------------------------------------
# Service URLs
# -----------------------------------------------------------------------------
ORCHESTRATOR_URL=http://localhost:4001
MCPHUB_URL=http://localhost:3000

# -----------------------------------------------------------------------------
# CORS Origins (comma-separated)
# -----------------------------------------------------------------------------
CORS_ORIGINS=http://localhost:3000,http://localhost:4000
```

### 3. Git History 정리

```bash
# BFG Repo-Cleaner를 사용하여 민감한 정보 제거
# 1. secrets.txt 파일에 제거할 문자열 목록 작성
# 2. BFG 실행
java -jar bfg.jar --replace-text secrets.txt my-repo.git

# 또는 git-filter-repo 사용
pip install git-filter-repo
git filter-repo --replace-text replacements.txt
```

### 4. .gitignore

```gitignore
# Environment
.env
.env.local
.env.*.local

# Secrets
*.pem
*.key
secrets/

# IDE
.idea/
.vscode/
*.swp

# Dependencies
node_modules/
venv/
__pycache__/

# Build
dist/
build/
*.egg-info/

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db
```

---

## 🤖 멀티 LLM 지원

### 현재 상태

```
지원: OpenAI, Azure OpenAI
미지원: Claude, Gemini
```

### 추가할 LLM Provider

#### 1. Claude (Anthropic)

```python
# backend/app/llm/claude_client.py
from anthropic import Anthropic

class ClaudeClient:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL or "claude-3-5-sonnet-20241022"
    
    async def chat(self, messages: list, **kwargs) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=self._convert_messages(messages)
        )
        return response.content[0].text
    
    def _convert_messages(self, messages):
        # OpenAI 형식을 Claude 형식으로 변환
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]
```

#### 2. Gemini (Google)

```python
# backend/app/llm/gemini_client.py
import google.generativeai as genai

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(
            settings.GEMINI_MODEL or "gemini-1.5-pro"
        )
    
    async def chat(self, messages: list, **kwargs) -> str:
        # 메시지 변환 (OpenAI 형식 → Gemini 형식)
        history = self._convert_to_history(messages[:-1])
        chat = self.model.start_chat(history=history)
        response = chat.send_message(messages[-1]["content"])
        return response.text
```

#### 3. 통합 LLM Factory

```python
# backend/app/llm/factory.py
from enum import Enum
from .openai_client import OpenAIClient
from .azure_client import AzureOpenAIClient
from .claude_client import ClaudeClient
from .gemini_client import GeminiClient

class LLMProvider(Enum):
    OPENAI = "openai"
    AZURE = "azure"
    CLAUDE = "claude"
    GEMINI = "gemini"

class LLMFactory:
    _clients = {
        LLMProvider.OPENAI: OpenAIClient,
        LLMProvider.AZURE: AzureOpenAIClient,
        LLMProvider.CLAUDE: ClaudeClient,
        LLMProvider.GEMINI: GeminiClient,
    }
    
    @classmethod
    def create(cls, provider: str = None):
        provider = provider or settings.LLM_PROVIDER
        provider_enum = LLMProvider(provider.lower())
        
        if provider_enum not in cls._clients:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        return cls._clients[provider_enum]()
```

### requirements.txt 추가

```txt
# LLM Providers
openai>=1.0.0
anthropic>=0.18.0
google-generativeai>=0.3.0
```

---

## 📚 문서화 전략

### 1. README.md 구조

```markdown
# K-Jarvis 🤖

> KT's Open Source AI Agent Orchestration Platform

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)]
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)]
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)]

## 🌟 Features
- A2A Protocol 기반 에이전트 오케스트레이션
- MCP 표준 지원 (K-ARC 연동)
- 멀티 LLM 지원 (OpenAI, Azure, Claude, Gemini)
- K-Auth SSO 인증

## 🚀 Quick Start
...

## 📖 Documentation
...

## 🤝 Contributing
...

## 📄 License
Apache License 2.0
```

### 2. 문서 사이트 구조 (Docusaurus)

```
docs/
├── intro.md                    # 소개
├── getting-started/
│   ├── installation.md         # 설치
│   ├── quick-start.md          # 빠른 시작
│   └── configuration.md        # 설정
├── architecture/
│   ├── overview.md             # 아키텍처 개요
│   ├── k-jarvis.md             # K-Jarvis 상세
│   ├── k-auth.md               # K-Auth 상세
│   └── k-arc.md                # K-ARC 상세
├── guides/
│   ├── create-agent.md         # 에이전트 개발
│   ├── create-mcp-server.md    # MCP 서버 개발
│   └── deploy-production.md    # 프로덕션 배포
├── api/
│   ├── k-jarvis-api.md         # K-Jarvis API
│   ├── k-auth-api.md           # K-Auth API
│   └── k-arc-api.md            # K-ARC API
└── community/
    ├── contributing.md         # 기여 가이드
    ├── code-of-conduct.md      # 행동 강령
    └── support.md              # 지원
```

### 3. CONTRIBUTING.md

```markdown
# Contributing to K-Jarvis

## 행동 강령
모든 기여자는 [Code of Conduct](CODE_OF_CONDUCT.md)를 준수해야 합니다.

## 기여 방법

### 버그 리포트
- GitHub Issues 사용
- 템플릿에 따라 상세히 작성

### 기능 제안
- Discussion에서 먼저 논의
- RFC 작성 후 PR

### Pull Request
1. Fork & Clone
2. Branch 생성 (`feature/my-feature`)
3. 변경 사항 커밋
4. 테스트 통과 확인
5. PR 생성

## 개발 환경 설정
...

## 코드 스타일
- Python: Black, isort, flake8
- TypeScript: ESLint, Prettier
```

---

## 👥 커뮤니티 관리

### 1. 소통 채널

| 채널 | 용도 |
|------|------|
| **GitHub Discussions** | 질문, 아이디어, 공지 |
| **GitHub Issues** | 버그 리포트, 기능 요청 |
| **Discord** (선택) | 실시간 커뮤니티 |
| **Twitter/X** | 공지, 업데이트 |

### 2. Issue Templates

```yaml
# .github/ISSUE_TEMPLATE/bug_report.yml
name: Bug Report
description: 버그 리포트
labels: ["bug"]
body:
  - type: textarea
    attributes:
      label: 버그 설명
      description: 버그에 대해 상세히 설명해주세요
    validations:
      required: true
  - type: textarea
    attributes:
      label: 재현 방법
      description: 버그를 재현하는 단계
  - type: textarea
    attributes:
      label: 예상 동작
  - type: textarea
    attributes:
      label: 실제 동작
  - type: input
    attributes:
      label: K-Jarvis 버전
```

### 3. PR Template

```markdown
## 변경 사항
<!-- 이 PR에서 변경된 내용 -->

## 관련 Issue
<!-- Fixes #123 -->

## 테스트
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 문서 업데이트

## 체크리스트
- [ ] 코드 스타일 준수
- [ ] Breaking Change 없음
- [ ] 보안 이슈 없음
```

---

## 🚀 릴리즈 전략

### 1. 버전 관리 (Semantic Versioning)

```
MAJOR.MINOR.PATCH

예: 1.0.0
- MAJOR: Breaking Changes
- MINOR: 새로운 기능 (호환 유지)
- PATCH: 버그 수정
```

### 2. 브랜치 전략

```
main          ← 안정 릴리즈
  ↑
develop       ← 개발 브랜치
  ↑
feature/*     ← 기능 개발
hotfix/*      ← 긴급 수정
release/*     ← 릴리즈 준비
```

### 3. 릴리즈 프로세스

```mermaid
graph LR
    A[develop] --> B[release/v1.0.0]
    B --> C[테스트 & QA]
    C --> D{통과?}
    D -->|Yes| E[main merge]
    D -->|No| F[수정]
    F --> C
    E --> G[Tag v1.0.0]
    G --> H[GitHub Release]
    H --> I[Docker Hub Push]
```

### 4. GitHub Release 자동화

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker Images
        run: |
          docker build -t kt-jarvis/k-jarvis:${{ github.ref_name }} .
          
      - name: Push to Docker Hub
        run: |
          docker push kt-jarvis/k-jarvis:${{ github.ref_name }}
          
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
```

---

## ✅ 체크리스트

### Phase 1: 준비 (1-2주)

```
[ ] GitHub Organization 생성 (kt-jarvis)
[ ] 팀원 초대 및 권한 설정
[ ] Repository 생성 (k-jarvis, k-auth, k-arc 등)
[ ] 라이선스 파일 추가 (Apache 2.0)
[ ] .gitignore 설정
```

### Phase 2: 코드 정리 (2-3주)

```
[ ] 모든 .env 파일에서 실제 credential 제거
[ ] .env.example 생성 및 문서화
[ ] Git History에서 민감 정보 제거
[ ] 하드코딩된 URL/IP 환경변수로 변경
[ ] 멀티 LLM 지원 구현 (Claude, Gemini)
[ ] 코드 스타일 통일 (Black, ESLint)
[ ] 데드코드, 주석 정리
```

### Phase 3: 문서화 (2주)

```
[ ] README.md 작성 (각 저장소)
[ ] CONTRIBUTING.md 작성
[ ] CODE_OF_CONDUCT.md 작성
[ ] API 문서 (Swagger/OpenAPI)
[ ] 아키텍처 다이어그램
[ ] 설치 가이드
[ ] 개발자 가이드 (Agent, MCP Server 개발)
```

### Phase 4: CI/CD 설정 (1주)

```
[ ] GitHub Actions 워크플로우
[ ] 자동 테스트 (pytest, jest)
[ ] 자동 린팅
[ ] Docker 이미지 빌드 & 푸시
[ ] 릴리즈 자동화
```

### Phase 5: 커뮤니티 준비 (1주)

```
[ ] Issue Templates
[ ] PR Template
[ ] GitHub Discussions 활성화
[ ] Discord 서버 (선택)
[ ] 공식 웹사이트 (docs)
```

### Phase 6: 초기 릴리즈 (1주)

```
[ ] v1.0.0 태그
[ ] GitHub Release 생성
[ ] Docker Hub 배포
[ ] 공지 및 홍보
```

---

## 📅 예상 일정

| Phase | 기간 | 주요 작업 |
|-------|------|----------|
| 준비 | 1-2주 | Organization, Repository 설정 |
| 코드 정리 | 2-3주 | Credential 제거, 멀티 LLM |
| 문서화 | 2주 | README, 가이드, API 문서 |
| CI/CD | 1주 | GitHub Actions, Docker |
| 커뮤니티 | 1주 | Templates, Discussions |
| 릴리즈 | 1주 | v1.0.0 배포 |

**총 예상 기간: 8-10주**

---

## 📞 담당

| 역할 | 담당 | 책임 |
|------|------|------|
| 전체 리드 | Orchestrator Team | 전략, 조율 |
| K-Jarvis | Orchestrator Team | 코드, 문서 |
| K-Auth | Orchestrator Team | 코드, 문서 |
| K-ARC | MCPHub Team | 코드, 문서 |
| Agents | Agent Team | 코드, 문서 |
| MCP Servers | MCPHub Team | 코드, 문서 |

---

**KT K-Jarvis Team**

