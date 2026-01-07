"""
Mock Agents - 다중 에이전트 라우팅 테스트용 Mock 에이전트
"""
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import random
import string

# Mock 에이전트 정의
MOCK_AGENT_DEFINITIONS = [
    {
        "name": "Slack Agent",
        "port": 5020,
        "description": "Slack 채널에 메시지를 전송하고, 채널 관리 및 알림 설정을 지원하는 AI 에이전트입니다.",
        "domain": "communication",
        "category": "slack",
        "keywords": ["slack", "슬랙", "메시지", "message", "채널", "channel", "알림", "notification"],
        "skills": ["send_message", "create_channel", "manage_notifications"]
    },
    {
        "name": "GitHub Agent",
        "port": 5021,
        "description": "GitHub 리포지토리 관리, PR 생성 및 리뷰, 이슈 관리를 수행하는 AI 에이전트입니다.",
        "domain": "development",
        "category": "github",
        "keywords": ["github", "깃헙", "pr", "pull request", "커밋", "commit", "리포", "repo", "이슈", "코드리뷰"],
        "skills": ["create_pr", "review_pr", "manage_issues", "search_code"]
    },
    {
        "name": "Notion Agent",
        "port": 5022,
        "description": "Notion 페이지와 데이터베이스를 관리하고, 팀 위키를 구축하는 AI 에이전트입니다.",
        "domain": "documentation",
        "category": "notion",
        "keywords": ["notion", "노션", "페이지", "page", "데이터베이스", "database", "위키", "wiki"],
        "skills": ["create_page", "update_page", "search_pages", "manage_database"]
    },
    {
        "name": "Asana Agent",
        "port": 5023,
        "description": "Asana 프로젝트와 태스크를 관리하고, 팀 협업을 지원하는 AI 에이전트입니다.",
        "domain": "project_management",
        "category": "asana",
        "keywords": ["asana", "아사나", "태스크", "task", "프로젝트", "project", "팀", "협업"],
        "skills": ["create_task", "update_task", "search_tasks", "manage_projects"]
    },
    {
        "name": "Google Calendar Agent",
        "port": 5024,
        "description": "Google Calendar에서 일정 관리, 미팅 예약, 리마인더 설정을 수행하는 AI 에이전트입니다.",
        "domain": "productivity",
        "category": "google_calendar",
        "keywords": ["calendar", "캘린더", "일정", "schedule", "미팅", "meeting", "예약", "booking"],
        "skills": ["create_event", "update_event", "search_events", "set_reminder"]
    },
    {
        "name": "Email Agent",
        "port": 5025,
        "description": "이메일 전송, 수신함 관리, 메일 검색 및 자동 응답을 지원하는 AI 에이전트입니다.",
        "domain": "communication",
        "category": "email",
        "keywords": ["email", "이메일", "메일", "mail", "전송", "send", "수신", "receive", "답장"],
        "skills": ["send_email", "search_emails", "manage_inbox", "auto_reply"]
    },
    {
        "name": "AWS Agent",
        "port": 5026,
        "description": "AWS 클라우드 리소스 관리, EC2 인스턴스 제어, S3 버킷 관리를 수행하는 AI 에이전트입니다.",
        "domain": "infrastructure",
        "category": "aws",
        "keywords": ["aws", "cloud", "클라우드", "ec2", "s3", "lambda", "인프라", "infrastructure"],
        "skills": ["manage_ec2", "manage_s3", "deploy_lambda", "monitor_resources"]
    },
    {
        "name": "Database Agent",
        "port": 5027,
        "description": "데이터베이스 쿼리 실행, 스키마 관리, 데이터 마이그레이션을 지원하는 AI 에이전트입니다.",
        "domain": "development",
        "category": "database",
        "keywords": ["database", "데이터베이스", "db", "쿼리", "query", "sql", "스키마", "schema"],
        "skills": ["execute_query", "manage_schema", "migrate_data", "backup_restore"]
    },
]


def create_mock_agent_app(definition: Dict[str, Any]) -> FastAPI:
    """Mock 에이전트 FastAPI 앱 생성"""
    app = FastAPI(title=definition["name"])
    
    @app.get("/.well-known/agent.json")
    async def agent_card():
        """A2A 호환 agent.json 반환"""
        return {
            "name": definition["name"],
            "description": definition["description"],
            "version": "1.0.0",
            "url": f"http://localhost:{definition['port']}",
            "capabilities": {
                "streaming": False,
                "pushNotifications": False
            },
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "skills": [
                {
                    "id": skill,
                    "name": skill.replace("_", " ").title(),
                    "description": f"{skill} functionality",
                    "tags": definition["keywords"][:3]
                }
                for skill in definition["skills"]
            ],
            # 라우팅 확장 필드
            "routing": {
                "domain": definition["domain"],
                "category": definition["category"],
                "keywords": definition["keywords"],
                "capabilities": definition["skills"]
            }
        }
    
    @app.post("/a2a")
    async def handle_a2a(request: Dict[str, Any]):
        """A2A 메시지 처리 (Mock 응답)"""
        request_id = request.get("id", "1")
        message = request.get("params", {}).get("message", {})
        message_text = ""
        
        if isinstance(message, dict):
            parts = message.get("parts", [])
            for part in parts:
                if isinstance(part, dict) and part.get("kind") == "text":
                    message_text = part.get("text", "")
                    break
        
        # Mock 응답 생성
        response_text = f"[{definition['name']}] 요청을 처리했습니다: {message_text[:50]}..."
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "status": "completed",
                "artifacts": [{
                    "artifactId": ''.join(random.choices(string.ascii_lowercase, k=8)),
                    "parts": [{"kind": "text", "text": response_text}]
                }]
            }
        })
    
    return app


async def run_mock_agent(definition: Dict[str, Any]):
    """단일 Mock 에이전트 실행"""
    app = create_mock_agent_app(definition)
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=definition["port"],
        log_level="warning"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_all_mock_agents():
    """모든 Mock 에이전트 동시 실행"""
    print("=" * 60)
    print("🚀 Mock Agents Starting...")
    print("=" * 60)
    
    for defn in MOCK_AGENT_DEFINITIONS:
        print(f"  - {defn['name']}: http://localhost:{defn['port']}")
    
    print("=" * 60)
    
    tasks = [run_mock_agent(defn) for defn in MOCK_AGENT_DEFINITIONS]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    print("\n🤖 Starting Mock Agents for Multi-Agent Routing Test\n")
    asyncio.run(run_all_mock_agents())





