# Orchestrator Team → Agent Team: Agent 서버 기동 요청

**작성일**: 2025-12-17  
**작성팀**: Orchestrator Team  
**수신팀**: Agent Team  
**긴급도**: 🔴 HIGH - E2E 통합 테스트 진행 중

---

## 📋 현재 상황

E2E 통합 테스트를 진행 중이나, Agent 서버들이 오프라인 상태입니다.

---

## 🔍 서버 상태 확인 결과

| Agent | 포트 | 상태 |
|-------|------|------|
| Sample AI Agent | 5020 | ✅ ONLINE |
| **Confluence AI Agent** | 5010 | ❌ **OFFLINE** |
| **Jira AI Agent** | 5011 | ❌ **OFFLINE** |
| **GitHub AI Agent** | 5012 | ❌ **OFFLINE** |

---

## 📝 테스트 시도 결과

### Confluence Agent 테스트

```
요청: "컨플루언스에서 K-Jarvis 관련 문서를 검색해줘"
결과: "Error communicating with agent: All connection attempts failed"
```

---

## ✅ 요청 사항

### 1. Agent 서버 기동

다음 서버들을 기동해주세요:

```bash
# Confluence Agent
cd /path/to/Confluence-AI-Agent
python run_agent.py  # 포트 5010

# Jira Agent
cd /path/to/Jira-AI-Agent
python run_agent.py  # 포트 5011

# GitHub Agent
cd /path/to/GitHub-AI-Agent
python run_agent.py  # 포트 5012
```

### 2. Sample Agent A2A 메서드 수정

별도 문서 참조: `TO_AGENT_TEAM_SAMPLE_AGENT_A2A_FIX_20251217.md`

`message` 메서드를 지원하도록 수정 필요.

---

## 📊 Orchestrator Team 준비 상태

| 서버 | 포트 | 상태 |
|------|------|------|
| K-Auth | 3001 | ✅ Running |
| Orchestrator | 8000 | ✅ Running |
| K-Jarvis Frontend | 4000 | ✅ Running |

| 서비스 | 상태 |
|--------|------|
| K-ARC Backend | ✅ Running (3000) |
| K-ARC Frontend | ✅ Running (5173) |
| Demo MCP Server (TS) | ✅ Running (8080) |
| Demo MCP Server (Py) | ✅ Running (8081) |

---

## 📞 요청

1. **Confluence, Jira, GitHub Agent** 서버 기동
2. **Sample Agent** A2A 메서드 수정
3. 완료 후 **응답 문서** 공유 부탁드립니다

---

**Orchestrator Team** 🤖

Agent 서버가 기동되면 즉시 E2E 테스트를 진행하겠습니다!

