"""
Hybrid Router 테스트 - 다중 에이전트 라우팅 검증
"""
import asyncio
import sys
import os

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agent_vector_store import AgentVectorStore, AgentRoutingMetadata, get_vector_store
from app.hybrid_router import HybridRouter, get_hybrid_router
from app.config import get_settings

# 테스트용 에이전트 메타데이터
TEST_AGENTS = [
    AgentRoutingMetadata(
        agent_name="Jira AI Agent",
        agent_url="http://localhost:5011",
        domain="project_management",
        category="jira",
        description="Jira 프로젝트의 이슈 검색, 생성, 분석을 수행하는 AI 에이전트입니다. 스프린트 관리, 이슈 추적, 프로젝트 현황 분석 등을 지원합니다.",
        keywords=["jira", "지라", "이슈", "issue", "프로젝트", "project", "스프린트", "sprint", "태스크", "task"],
        capabilities=["search_issues", "create_issue", "update_issue", "analyze"]
    ),
    AgentRoutingMetadata(
        agent_name="Confluence AI Agent",
        agent_url="http://localhost:5010",
        domain="documentation",
        category="confluence",
        description="Confluence 페이지 검색, 생성, 수정을 수행하는 AI 에이전트입니다. 문서 관리, 지식 베이스 구축, 회의록 작성을 지원합니다.",
        keywords=["confluence", "컨플루언스", "문서", "document", "페이지", "page", "위키", "wiki", "보고서", "report"],
        capabilities=["search_pages", "create_page", "update_page"]
    ),
    AgentRoutingMetadata(
        agent_name="Slack Agent",
        agent_url="http://localhost:5020",
        domain="communication",
        category="slack",
        description="Slack 채널에 메시지를 전송하고, 채널 관리 및 알림 설정을 지원하는 AI 에이전트입니다.",
        keywords=["slack", "슬랙", "메시지", "message", "채널", "channel", "알림", "notification"],
        capabilities=["send_message", "create_channel", "manage_notifications"]
    ),
    AgentRoutingMetadata(
        agent_name="GitHub Agent",
        agent_url="http://localhost:5021",
        domain="development",
        category="github",
        description="GitHub 리포지토리 관리, PR 생성 및 리뷰, 이슈 관리를 수행하는 AI 에이전트입니다.",
        keywords=["github", "깃헙", "pr", "pull request", "커밋", "commit", "리포", "repo", "코드리뷰"],
        capabilities=["create_pr", "review_pr", "manage_issues", "search_code"]
    ),
    AgentRoutingMetadata(
        agent_name="Notion Agent",
        agent_url="http://localhost:5022",
        domain="documentation",
        category="notion",
        description="Notion 페이지와 데이터베이스를 관리하고, 팀 위키를 구축하는 AI 에이전트입니다.",
        keywords=["notion", "노션", "페이지", "page", "데이터베이스", "database", "위키", "wiki"],
        capabilities=["create_page", "update_page", "search_pages", "manage_database"]
    ),
]

# 테스트 케이스
TEST_CASES = [
    # 명시적 에이전트 매칭
    ("Jira에서 AUT 프로젝트 이슈 검색해줘", "Jira AI Agent", "explicit"),
    ("Confluence 문서 만들어줘", "Confluence AI Agent", "explicit"),
    ("슬랙 채널에 메시지 보내줘", "Slack Agent", "explicit"),
    ("GitHub PR 생성해줘", "GitHub Agent", "explicit"),
    ("노션에 페이지 만들어줘", "Notion Agent", "explicit"),
    
    # 도메인 기반 매칭 (RAG)
    ("프로젝트 이슈 현황 분석해줘", "Jira AI Agent", "domain"),
    ("회의록 작성해줘", "Confluence AI Agent", "domain"),
    ("팀에 알림 보내줘", "Slack Agent", "domain"),
    ("코드 리뷰 해줘", "GitHub Agent", "domain"),
    
    # 모호한 케이스
    ("스프린트 진행 상황 확인해줘", "Jira AI Agent", "ambiguous"),
    ("문서 검색해줘", None, "ambiguous"),  # Confluence or Notion
    ("보고서 만들어줘", "Confluence AI Agent", "ambiguous"),
]


async def setup_test_data():
    """테스트 데이터 설정"""
    print("\n📦 Setting up test data...")
    
    vector_store = await get_vector_store()
    
    for agent in TEST_AGENTS:
        success = await vector_store.upsert_agent(agent)
        if success:
            print(f"  ✅ {agent.agent_name}")
        else:
            print(f"  ❌ {agent.agent_name}")
    
    print()


async def test_vector_search():
    """벡터 검색 테스트"""
    print("\n🔍 Testing Vector Search...")
    print("=" * 60)
    
    vector_store = await get_vector_store()
    
    test_queries = [
        "이슈 현황 분석",
        "문서 작성",
        "메시지 전송",
        "코드 리뷰",
    ]
    
    for query in test_queries:
        results = await vector_store.search_similar(query, limit=3)
        print(f"\nQuery: '{query}'")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['agent_name']} ({r['domain']}) - similarity: {r['similarity']:.3f}")
    
    print()


async def test_hybrid_router():
    """하이브리드 라우터 테스트"""
    print("\n🚀 Testing Hybrid Router...")
    print("=" * 60)
    
    # Note: 실제 라우터 테스트는 레지스트리에 에이전트가 등록되어 있어야 함
    # 여기서는 벡터 검색만 테스트
    
    vector_store = await get_vector_store()
    
    passed = 0
    failed = 0
    
    for message, expected_agent, case_type in TEST_CASES:
        results = await vector_store.search_similar(message, limit=1, threshold=0.3)
        
        actual_agent = results[0]["agent_name"] if results else None
        
        # 모호한 케이스는 도메인만 확인
        if case_type == "ambiguous" and expected_agent is None:
            print(f"  ⚠️  '{message[:30]}...' -> {actual_agent} (ambiguous)")
            continue
        
        if actual_agent == expected_agent:
            print(f"  ✅ '{message[:30]}...' -> {actual_agent}")
            passed += 1
        else:
            print(f"  ❌ '{message[:30]}...' -> {actual_agent} (expected: {expected_agent})")
            failed += 1
    
    print()
    print(f"Results: {passed} passed, {failed} failed")
    print()


async def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("🧪 Multi-Agent Routing Test Suite")
    print("=" * 60)
    
    settings = get_settings()
    print(f"\nDatabase: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    
    try:
        # 테스트 데이터 설정
        await setup_test_data()
        
        # 벡터 검색 테스트
        await test_vector_search()
        
        # 하이브리드 라우터 테스트
        await test_hybrid_router()
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())





