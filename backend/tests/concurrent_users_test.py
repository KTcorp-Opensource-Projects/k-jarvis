"""
동시 다중 사용자 테스트 스크립트
여러 사용자가 동시에 채팅을 요청하는 시나리오를 테스트합니다.
"""
import asyncio
import time
import httpx
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestUser:
    """테스트 사용자"""
    username: str
    password: str
    display_name: str = ""  # 결과 출력용 이름
    token: str = ""
    conversation_id: str = ""


@dataclass
class TestResult:
    """테스트 결과"""
    user: str
    query: str
    agent_used: str
    response_time: float
    success: bool
    error: str = ""
    response_preview: str = ""


class ConcurrentUsersTest:
    """동시 다중 사용자 테스트"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results: List[TestResult] = []
    
    async def login(self, client: httpx.AsyncClient, username: str, password: str) -> str:
        """사용자 로그인"""
        response = await client.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token", "")
        return ""
    
    async def send_chat(
        self,
        client: httpx.AsyncClient,
        token: str,
        message: str,
        conversation_id: str = None
    ) -> Dict[str, Any]:
        """채팅 메시지 전송"""
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        response = await client.post(
            f"{self.base_url}/api/chat/message",
            json=payload,
            headers=headers,
            timeout=120.0  # 긴 타임아웃 설정
        )
        
        if response.status_code == 200:
            return response.json()
        return {"error": response.text}
    
    async def user_session(
        self,
        user: TestUser,
        queries: List[str]
    ) -> List[TestResult]:
        """단일 사용자 세션 시뮬레이션"""
        results = []
        display = user.display_name or user.username
        
        async with httpx.AsyncClient() as client:
            # 로그인
            user.token = await self.login(client, user.username, user.password)
            if not user.token:
                return [TestResult(
                    user=display,
                    query="login",
                    agent_used="",
                    response_time=0,
                    success=False,
                    error="Login failed"
                )]
            
            # 각 쿼리 실행
            for query in queries:
                start_time = time.time()
                
                try:
                    response = await self.send_chat(
                        client,
                        user.token,
                        query,
                        user.conversation_id
                    )
                    
                    elapsed = time.time() - start_time
                    
                    if "error" in response:
                        results.append(TestResult(
                            user=display,
                            query=query,
                            agent_used="",
                            response_time=elapsed,
                            success=False,
                            error=str(response.get("error", "Unknown error"))
                        ))
                    else:
                        # 대화 ID 저장 (연속 대화용)
                        user.conversation_id = response.get("conversation_id", "")
                        content = response.get("content", "")
                        
                        results.append(TestResult(
                            user=display,
                            query=query,
                            agent_used=response.get("agent_used", "Unknown"),
                            response_time=elapsed,
                            success=True,
                            response_preview=content[:100] + "..." if len(content) > 100 else content
                        ))
                        
                except Exception as e:
                    elapsed = time.time() - start_time
                    results.append(TestResult(
                        user=display,
                        query=query,
                        agent_used="",
                        response_time=elapsed,
                        success=False,
                        error=str(e)
                    ))
        
        return results
    
    async def run_concurrent_test(
        self,
        users: List[TestUser],
        user_queries: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """동시 다중 사용자 테스트 실행"""
        print(f"\n{'='*60}")
        print(f"🚀 동시 다중 사용자 테스트 시작")
        print(f"   사용자 수: {len(users)}")
        print(f"   시작 시간: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # 모든 사용자 세션을 동시에 실행
        tasks = [
            self.user_session(user, user_queries.get(user.display_name or user.username, []))
            for user in users
        ]
        
        all_results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # 결과 집계
        all_test_results = []
        for results in all_results:
            all_test_results.extend(results)
        
        self.results = all_test_results
        
        # 통계 계산
        successful = [r for r in all_test_results if r.success]
        failed = [r for r in all_test_results if not r.success]
        
        avg_response_time = sum(r.response_time for r in successful) / len(successful) if successful else 0
        
        return {
            "total_requests": len(all_test_results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(all_test_results) * 100 if all_test_results else 0,
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "results": all_test_results
        }
    
    def print_results(self, stats: Dict[str, Any]):
        """결과 출력"""
        print(f"\n{'='*60}")
        print(f"📊 테스트 결과 요약")
        print(f"{'='*60}")
        print(f"  총 요청 수: {stats['total_requests']}")
        print(f"  성공: {stats['successful']}")
        print(f"  실패: {stats['failed']}")
        print(f"  성공률: {stats['success_rate']:.1f}%")
        print(f"  총 소요 시간: {stats['total_time']:.2f}초")
        print(f"  평균 응답 시간: {stats['avg_response_time']:.2f}초")
        print(f"{'='*60}\n")
        
        # 사용자별 상세 결과
        print("📋 사용자별 상세 결과:")
        print("-" * 60)
        
        for result in self.results:
            status = "✅" if result.success else "❌"
            print(f"{status} [{result.user}] {result.query[:30]}...")
            print(f"   에이전트: {result.agent_used}")
            print(f"   응답시간: {result.response_time:.2f}초")
            if result.error:
                print(f"   오류: {result.error}")
            if result.response_preview:
                print(f"   응답: {result.response_preview[:50]}...")
            print()


async def main():
    """메인 테스트 실행 - 10명 동시 사용자 + 체이닝 테스트"""
    tester = ConcurrentUsersTest()
    
    # 동시 실행을 위한 쿼리들 (다양한 시나리오)
    # 단일 에이전트 호출 + 체이닝 혼합
    different_queries = [
        # 단일 에이전트 호출 (6명)
        ["CNCORE 스페이스에서 API 관련 문서를 검색해줘"],  # User 1 - Confluence
        ["CNCORE 프로젝트의 이슈 현황을 보여줘"],  # User 2 - Jira
        ["langchain-ai/langchain 저장소의 최근 PR을 보여줘"],  # User 3 - GitHub
        ["CNCORE에서 오케스트레이터 문서를 찾아줘"],  # User 4 - Confluence
        ["langchain-ai/langchain의 PR 현황을 분석해줘"],  # User 5 - GitHub
        ["CNCORE에서 MCP Hub 관련 문서를 검색해줘"],  # User 6 - Confluence
        
        # 체이닝 요청 (4명) - 멀티 에이전트 워크플로우
        ["langchain-ai/langchain 저장소의 PR 현황을 분석하고, 그 결과를 CNCORE 스페이스에 동시성 테스트 보고서 1이라는 제목으로 문서 작성해줘"],  # User 7 - GitHub → Confluence
        ["langchain-ai/langchain 저장소의 최근 PR을 분석하고, CNCORE에 동시성 테스트 보고서 2라는 문서로 정리해줘"],  # User 8 - GitHub → Confluence
        ["langchain-ai/langchain PR 현황을 분석해서 CNCORE 스페이스에 동시성 테스트 보고서 3으로 작성해줘"],  # User 9 - GitHub → Confluence
        ["GitHub langchain-ai/langchain의 PR을 분석하고 CNCORE에 동시성 테스트 보고서 4라는 문서로 만들어줘"],  # User 10 - GitHub → Confluence
    ]
    
    # 테스트 사용자들 (10명)
    users = []
    user_specific_queries = {}
    
    for i in range(10):
        username = f"test{i+1}"
        user = TestUser(
            username=username,
            password="test123",
            display_name=username
        )
        users.append(user)
        user_specific_queries[username] = different_queries[i]
    
    print("\n" + "="*60)
    print("🏢 엔터프라이즈급 동시성 테스트")
    print("="*60)
    print(f"  👥 동시 사용자: 10명")
    print(f"  📝 단일 에이전트 요청: 6개")
    print(f"  🔗 체이닝 요청 (GitHub → Confluence): 4개")
    print("="*60 + "\n")
    
    # 테스트 실행
    stats = await tester.run_concurrent_test(users, user_specific_queries)
    
    # 결과 출력
    tester.print_results(stats)
    
    # 체이닝 결과 별도 분석
    chaining_results = [r for r in tester.results if r.agent_used and "→" in r.agent_used]
    single_results = [r for r in tester.results if r.agent_used and "→" not in r.agent_used and r.agent_used not in ["None", "Unknown"]]
    
    print("\n" + "="*60)
    print("📊 요청 유형별 분석")
    print("="*60)
    
    if single_results:
        single_success = [r for r in single_results if r.success]
        single_avg_time = sum(r.response_time for r in single_success) / len(single_success) if single_success else 0
        print(f"\n🔹 단일 에이전트 요청:")
        print(f"   성공: {len(single_success)}/{len(single_results)}")
        print(f"   평균 응답시간: {single_avg_time:.2f}초")
    
    if chaining_results:
        chaining_success = [r for r in chaining_results if r.success]
        chaining_avg_time = sum(r.response_time for r in chaining_success) / len(chaining_success) if chaining_success else 0
        print(f"\n🔗 체이닝 요청:")
        print(f"   성공: {len(chaining_success)}/{len(chaining_results)}")
        print(f"   평균 응답시간: {chaining_avg_time:.2f}초")
    
    print("\n" + "="*60)
    
    return stats


if __name__ == "__main__":
    asyncio.run(main())

