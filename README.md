# K-Jarvis 🤖

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docker.com)

**KT's Open Source AI Agent Orchestration Platform**

> A2A(Agent-to-Agent) 프로토콜 기반의 AI 에이전트 오케스트레이션 플랫폼입니다.  
> 여러 LLM 프로바이더(OpenAI, Azure, Claude, Gemini)를 지원하며, MCP 표준과 호환됩니다.

[English](README_EN.md) | 한국어

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **지능형 라우팅** | LLM 기반 의도 분석으로 최적의 에이전트 자동 선택 |
| 📡 **A2A 프로토콜** | Google A2A 표준 완전 지원 |
| 🔌 **MCP 호환** | Model Context Protocol 표준 지원 (K-ARC 연동) |
| 🤖 **멀티 LLM** | OpenAI, Azure OpenAI, Claude, Gemini 지원 |
| 🔐 **SSO 인증** | K-Auth OAuth 2.0 기반 통합 인증 |
| ⚡ **실시간 스트리밍** | SSE를 통한 실시간 응답 |
| 🎨 **현대적 UI** | J.A.R.V.I.S 스타일의 세련된 인터페이스 |

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         K-Jarvis Ecosystem                          │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   K-Jarvis   │  │    K-Auth    │  │    K-ARC     │              │
│  │ Orchestrator │  │  OAuth 2.0   │  │   MCP Hub    │              │
│  │              │  │              │  │              │              │
│  │  - Routing   │  │  - SSO       │  │  - MCP Mgmt  │              │
│  │  - A2A       │  │  - JWT       │  │  - Tokens    │              │
│  │  - Multi-LLM │  │  - Users     │  │  - Servers   │              │
│  └──────┬───────┘  └──────────────┘  └──────────────┘              │
│         │                                                            │
│         │ A2A Protocol                                               │
│         ▼                                                            │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                    AI Agents                              │      │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐         │      │
│  │  │ GitHub │  │  Jira  │  │Conflue │  │ Custom │         │      │
│  │  │ Agent  │  │ Agent  │  │ Agent  │  │ Agent  │ ...     │      │
│  │  └────────┘  └────────┘  └────────┘  └────────┘         │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (권장)
- **Python** 3.11+ (로컬 개발 시)
- **Node.js** 18+ (로컬 개발 시)
- **PostgreSQL** 15+ (로컬 개발 시)
- LLM API Key (OpenAI, Azure, Claude, 또는 Gemini 중 하나)

### Option 1: Docker (권장)

```bash
# 저장소 클론
git clone https://github.com/kt-jarvis/k-jarvis.git
cd k-jarvis

# 환경 변수 설정
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# .env 파일에서 LLM API 키 설정
# LLM_PROVIDER=openai (또는 azure, claude, gemini)
# OPENAI_API_KEY=sk-your-key-here

# Docker Compose로 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

✅ **접속**:
- Frontend: http://localhost:4000
- Backend API: http://localhost:4001
- API Docs: http://localhost:4001/docs

### Option 2: 로컬 개발

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일 편집 후
python run_orchestrator.py

# Frontend (새 터미널)
cd frontend
npm install
cp .env.example .env
npm start
```

---

## ⚙️ Configuration

### LLM Provider 설정

`.env` 파일에서 사용할 LLM 프로바이더를 선택합니다:

```env
# 지원 옵션: openai, azure, claude, gemini
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-key
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Google Gemini
GOOGLE_API_KEY=your-key
GEMINI_MODEL=gemini-1.5-pro
```

> 💡 **팁**: 여러 프로바이더의 키를 설정해두면, 주 프로바이더 장애 시 자동으로 폴백됩니다.

---

## 📚 Documentation

| 문서 | 설명 |
|------|------|
| [Getting Started](docs/GETTING_STARTED.md) | 설치 및 시작 가이드 |
| [Architecture](docs/ARCHITECTURE.md) | 아키텍처 상세 설명 |
| [Agent Development](docs/AGENT_DEVELOPMENT.md) | 에이전트 개발 가이드 |
| [API Reference](http://localhost:4001/docs) | Swagger API 문서 |
| [K-Auth Integration](docs/KAUTH_INTEGRATION.md) | K-Auth SSO 연동 |
| [K-ARC Integration](docs/KARC_INTEGRATION.md) | K-ARC(MCPHub) 연동 |

---

## 🔌 Creating Your Own Agent

K-Jarvis는 A2A 프로토콜을 따르는 모든 에이전트와 연동됩니다.

### 샘플 에이전트 구조

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Agent Card (필수)
@app.get("/.well-known/agent.json")
async def get_agent_card():
    return {
        "name": "My Agent",
        "description": "My custom AI agent",
        "url": "http://localhost:5020",
        "version": "1.0.0",
        "skills": [
            {
                "id": "my-skill",
                "name": "My Skill",
                "description": "Does something useful",
                "tags": ["custom", "example"]
            }
        ]
    }

# Message Handler (필수)
@app.post("/a2a")
async def handle_message(request: dict):
    method = request.get("method")
    
    if method == "message/send":
        message = request["params"]["message"]["parts"][0]["text"]
        # 여기서 메시지 처리
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {
                "message": {
                    "role": "agent",
                    "parts": [{"text": f"Processed: {message}"}]
                }
            }
        }
```

더 자세한 내용은 [Agent Development Guide](docs/AGENT_DEVELOPMENT.md)를 참조하세요.

---

## 🤝 Contributing

기여를 환영합니다! [CONTRIBUTING.md](CONTRIBUTING.md)를 읽어주세요.

### 개발 워크플로우

```bash
# 1. Fork & Clone
git clone https://github.com/YOUR_USERNAME/k-jarvis.git

# 2. 브랜치 생성
git checkout -b feature/my-feature

# 3. 변경 사항 커밋
git commit -m "feat: add amazing feature"

# 4. Push & PR
git push origin feature/my-feature
```

### 커밋 메시지 컨벤션

```
feat: 새로운 기능
fix: 버그 수정
docs: 문서 변경
style: 코드 포맷팅
refactor: 리팩토링
test: 테스트 추가/수정
chore: 빌드, 설정 변경
```

---

## 📄 License

이 프로젝트는 [Apache License 2.0](LICENSE) 하에 배포됩니다.

```
Copyright 2026 KT Corporation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```

---

## 🙏 Acknowledgments

- [Google A2A Protocol](https://github.com/google/a2a-spec)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [LangChain](https://langchain.com)
- [FastAPI](https://fastapi.tiangolo.com)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/kt-jarvis/k-jarvis/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kt-jarvis/k-jarvis/discussions)
- **Email**: opensource@kt.com

---

<p align="center">
  <strong>Made with ❤️ by KT</strong><br>
  <sub>Building the Future of AI Agent Ecosystem</sub>
</p>
