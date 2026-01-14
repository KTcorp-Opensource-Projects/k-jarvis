---
trigger: always_on
---

한국어로 대답해주고, 우리는 jarivs 플랫폼 개발팀이야.

## [K-Jarvis Ecosystem Collaboration Protocol]
이 프로젝트는 3개의 전문 팀(K-Arc, K-Auth, K-Jarvis)이 협업하는 구조입니다.
작업을 시작하기 전, **반드시** 아래 3단계 절차를 따르십시오:
1. **소속 파악 (Identify)**: 현재 작업이 어느 팀 영역인지 판단하십시오.
   - **🛡️ K-Auth**: 인증/보안 (`middlewares`, [User](cci:2://file:///Users/jungchihoon/chihoon/kt-opensource-project-jarvis/k-arc-opensource/apps/backend/src/db/entities/User.ts:9:0-132:1), `kauth-*`)
   - **⚡ K-Arc**: MCP 연결/백엔드 (`services/mcp*`, [ArcApiKey](cci:2://file:///Users/jungchihoon/chihoon/kt-opensource-project-jarvis/k-arc-opensource/apps/backend/src/services/arcApiKeyService.ts:13:0-475:1), `serverController`)
   - **🧠 K-Jarvis**: 프론트엔드/UI (`frontend/*`)
2. **규칙 확인 (Sync)**: 프로젝트 루트의 [shared-docs/Collaboration_Rules.md](cci:7://file:///Users/jungchihoon/chihoon/kt-opensource-project-jarvis/shared-docs/Collaboration_Rules.md:0:0-0:0)와 [HQ_Announcements.md](cci:7://file:///Users/jungchihoon/chihoon/kt-opensource-project-jarvis/shared-docs/HQ_Announcements.md:0:0-0:0)를 먼저 읽으십시오.
3. **로그 작성 (Log)**: 코드를 건드리기 전에, `shared-docs/teams/Team_[팀이름]_Log.md` 파일에 작업 계획을 `[IN-PROGRESS]` 상태로 기록하십시오.