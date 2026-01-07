#!/usr/bin/env python3
"""
엔터프라이즈급 통합 테스트 스크립트
- 동시 다중 사용자
- 대화 컨텍스트 유지 (conversation_id)
- 이전 대화 참조
- 체이닝 워크플로우
"""
import asyncio
import time
import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TestUser:
    username: str
    password: str
    token: str = ""
    conversation_id: str = ""


@dataclass
class TestResult:
    test_case: str
    user: str
    query: str
    agent_used: str
    response_time: float
    success: bool
    error: str = ""
    response_preview: str = ""
    conversation_id: str = ""


class EnterpriseTest:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results: List[TestResult] = []
    
    async def login(self, client: httpx.AsyncClient, username: str, password: str) -> str:
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
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        response = await client.post(
            f"{self.base_url}/api/chat/message",
            json=payload,
            headers=headers,
            timeout=180.0
        )
        
        if response.status_code == 200:
            return response.json()
        return {"error": response.text}
    
    async def get_conversations(
        self,
        client: httpx.AsyncClient,
        token: str
    ) -> List[Dict]:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            f"{self.base_url}/api/chat/conversations",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        return []

    # ========================================
    # 테스트 케이스 1: 대화 컨텍스트 유지 테스트
    # ========================================
    async def test_conversation_context(self, user: TestUser) -> List[TestResult]:
        results = []
        
        async with httpx.AsyncClient() as client:
            user.token = await self.login(client, user.username, user.password)
            if not user.token:
                return [TestResult(
                    test_case="context",
                    user=user.username,
                    query="login",
                    agent_used="",
                    response_time=0,
                    success=False,
                    error="Login failed"
                )]
            
            # 첫 번째 대화: 문서 검색
            print(f"  [{user.username}] 1단계: 첫 번째 질문...")
            start = time.time()
            resp1 = await self.send_chat(
                client, user.token,
                "CNCORE 스페이스에서 MCP Hub 관련 문서를 검색해줘"
            )
            elapsed1 = time.time() - start
            
            conv_id = resp1.get("conversation_id", "")
            user.conversation_id = conv_id
            
            results.append(TestResult(
                test_case="context_step1",
                user=user.username,
                query="첫 번째 질문 (문서 검색)",
                agent_used=resp1.get("agent_used", "Unknown"),
                response_time=elapsed1,
                success="error" not in resp1,
                response_preview=resp1.get("content", "")[:100],
                conversation_id=conv_id
            ))
            
            # 두 번째 대화: 이전 대화 참조 (같은 conversation_id 사용)
            print(f"  [{user.username}] 2단계: 이전 대화 참조 질문...")
            start = time.time()
            resp2 = await self.send_chat(
                client, user.token,
                "방금 검색한 문서 중에서 첫 번째 문서의 내용을 요약해줘",
                conversation_id=conv_id
            )
            elapsed2 = time.time() - start
            
            results.append(TestResult(
                test_case="context_step2",
                user=user.username,
                query="이전 대화 참조 (요약 요청)",
                agent_used=resp2.get("agent_used", "Unknown"),
                response_time=elapsed2,
                success="error" not in resp2,
                response_preview=resp2.get("content", "")[:100],
                conversation_id=resp2.get("conversation_id", "")
            ))
            
            # 세 번째 대화: 연속 대화 (같은 conversation_id)
            print(f"  [{user.username}] 3단계: 연속 대화...")
            start = time.time()
            resp3 = await self.send_chat(
                client, user.token,
                "이 내용을 간단히 한 줄로 정리해줘",
                conversation_id=conv_id
            )
            elapsed3 = time.time() - start
            
            results.append(TestResult(
                test_case="context_step3",
                user=user.username,
                query="연속 대화 (한 줄 정리)",
                agent_used=resp3.get("agent_used", "Unknown"),
                response_time=elapsed3,
                success="error" not in resp3,
                response_preview=resp3.get("content", "")[:100],
                conversation_id=resp3.get("conversation_id", "")
            ))
        
        return results

    # ========================================
    # 테스트 케이스 2: 동시 다중 대화 테스트
    # ========================================
    async def test_concurrent_conversations(self, users: List[TestUser]) -> List[TestResult]:
        async def user_multi_turn(user: TestUser, queries: List[str]) -> List[TestResult]:
            results = []
            async with httpx.AsyncClient() as client:
                user.token = await self.login(client, user.username, user.password)
                if not user.token:
                    return [TestResult(
                        test_case="concurrent",
                        user=user.username,
                        query="login",
                        agent_used="",
                        response_time=0,
                        success=False,
                        error="Login failed"
                    )]
                
                for i, query in enumerate(queries):
                    start = time.time()
                    resp = await self.send_chat(
                        client, user.token, query,
                        conversation_id=user.conversation_id if user.conversation_id else None
                    )
                    elapsed = time.time() - start
                    
                    user.conversation_id = resp.get("conversation_id", "")
                    
                    results.append(TestResult(
                        test_case=f"concurrent_turn{i+1}",
                        user=user.username,
                        query=query[:40] + "...",
                        agent_used=resp.get("agent_used", "Unknown"),
                        response_time=elapsed,
                        success="error" not in resp,
                        response_preview=resp.get("content", "")[:80],
                        conversation_id=user.conversation_id
                    ))
            return results
        
        # 각 사용자별 다른 대화 시나리오
        user_scenarios = [
            # 사용자 1: Confluence 연속 대화
            [
                "CNCORE에서 API 문서를 검색해줘",
                "그 중에서 가장 최근 문서는 뭐야?"
            ],
            # 사용자 2: Jira 연속 대화  
            [
                "CNCORE 프로젝트의 이슈를 보여줘",
                "진행 중인 이슈만 필터링해서 보여줘"
            ],
            # 사용자 3: GitHub 연속 대화
            [
                "langchain-ai/langchain의 최근 PR을 보여줘",
                "그 중 리뷰가 필요한 PR은 뭐야?"
            ],
        ]
        
        tasks = []
        for i, user in enumerate(users[:3]):
            tasks.append(user_multi_turn(user, user_scenarios[i % len(user_scenarios)]))
        
        all_results = await asyncio.gather(*tasks)
        return [r for results in all_results for r in results]

    # ========================================
    # 테스트 케이스 3: 체이닝 + 컨텍스트 테스트
    # ========================================
    async def test_chaining_with_context(self, user: TestUser) -> List[TestResult]:
        results = []
        
        async with httpx.AsyncClient() as client:
            user.token = await self.login(client, user.username, user.password)
            if not user.token:
                return [TestResult(
                    test_case="chaining_context",
                    user=user.username,
                    query="login",
                    agent_used="",
                    response_time=0,
                    success=False,
                    error="Login failed"
                )]
            
            # 체이닝 실행
            print(f"  [{user.username}] 체이닝 실행 중...")
            start = time.time()
            resp = await self.send_chat(
                client, user.token,
                "langchain-ai/langchain 저장소의 PR 현황을 분석하고, CNCORE 스페이스에 체이닝 컨텍스트 테스트라는 제목으로 문서를 작성해줘"
            )
            elapsed = time.time() - start
            
            conv_id = resp.get("conversation_id", "")
            user.conversation_id = conv_id
            
            results.append(TestResult(
                test_case="chaining_execute",
                user=user.username,
                query="체이닝 (GitHub -> Confluence)",
                agent_used=resp.get("agent_used", "Unknown"),
                response_time=elapsed,
                success="error" not in resp and "WORKFLOW" in resp.get("content", ""),
                response_preview=resp.get("content", "")[:100],
                conversation_id=conv_id
            ))
            
            # 체이닝 결과 참조
            print(f"  [{user.username}] 체이닝 결과 참조 중...")
            start = time.time()
            resp2 = await self.send_chat(
                client, user.token,
                "방금 작성한 문서의 URL을 알려줘",
                conversation_id=conv_id
            )
            elapsed2 = time.time() - start
            
            results.append(TestResult(
                test_case="chaining_reference",
                user=user.username,
                query="체이닝 결과 참조",
                agent_used=resp2.get("agent_used", "Unknown"),
                response_time=elapsed2,
                success="error" not in resp2,
                response_preview=resp2.get("content", "")[:100],
                conversation_id=resp2.get("conversation_id", "")
            ))
        
        return results

    # ========================================
    # 메인 실행
    # ========================================
    async def run_all_tests(self):
        print("\n" + "=" * 70)
        print("🏢 엔터프라이즈급 통합 테스트")
        print("=" * 70)
        print(f"시작 시간: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 70)
        
        all_results = []
        
        # 테스트 사용자들
        users = [
            TestUser(username="test1", password="test123"),
            TestUser(username="test2", password="test123"),
            TestUser(username="test3", password="test123"),
            TestUser(username="test4", password="test123"),
            TestUser(username="test5", password="test123"),
        ]
        
        # ========================================
        # 테스트 1: 대화 컨텍스트 유지
        # ========================================
        print("\n" + "-" * 70)
        print("📝 테스트 1: 대화 컨텍스트 유지 (conversation_id)")
        print("-" * 70)
        
        context_results = await self.test_conversation_context(users[0])
        all_results.extend(context_results)
        
        for r in context_results:
            status = "✅" if r.success else "❌"
            print(f"  {status} {r.test_case}: {r.response_time:.2f}초")
            print(f"     conv_id: {r.conversation_id[:20]}..." if r.conversation_id else "     conv_id: N/A")
        
        # ========================================
        # 테스트 2: 동시 다중 대화
        # ========================================
        print("\n" + "-" * 70)
        print("👥 테스트 2: 동시 다중 사용자 대화 (3명)")
        print("-" * 70)
        
        concurrent_results = await self.test_concurrent_conversations(users[1:4])
        all_results.extend(concurrent_results)
        
        for r in concurrent_results:
            status = "✅" if r.success else "❌"
            print(f"  {status} [{r.user}] {r.test_case}: {r.agent_used} ({r.response_time:.2f}초)")
        
        # ========================================
        # 테스트 3: 체이닝 + 컨텍스트
        # ========================================
        print("\n" + "-" * 70)
        print("🔗 테스트 3: 체이닝 + 컨텍스트 참조")
        print("-" * 70)
        
        chaining_results = await self.test_chaining_with_context(users[4])
        all_results.extend(chaining_results)
        
        for r in chaining_results:
            status = "✅" if r.success else "❌"
            print(f"  {status} {r.test_case}: {r.agent_used} ({r.response_time:.2f}초)")
        
        # ========================================
        # 최종 결과 요약
        # ========================================
        self.results = all_results
        self.print_summary()
        
        return all_results
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("📊 최종 테스트 결과 요약")
        print("=" * 70)
        
        total = len(self.results)
        success = len([r for r in self.results if r.success])
        failed = total - success
        
        print(f"  총 테스트: {total}")
        print(f"  성공: {success}")
        print(f"  실패: {failed}")
        print(f"  성공률: {success/total*100:.1f}%" if total > 0 else "  성공률: N/A")
        
        # 테스트 케이스별 분석
        test_cases = {}
        for r in self.results:
            case = r.test_case.split("_")[0]
            if case not in test_cases:
                test_cases[case] = {"success": 0, "total": 0, "times": []}
            test_cases[case]["total"] += 1
            if r.success:
                test_cases[case]["success"] += 1
                test_cases[case]["times"].append(r.response_time)
        
        print("\n  테스트 케이스별:")
        for case, data in test_cases.items():
            avg_time = sum(data["times"]) / len(data["times"]) if data["times"] else 0
            print(f"    - {case}: {data['success']}/{data['total']} (평균 {avg_time:.2f}초)")
        
        # 대화 격리 검증
        conv_ids = [r.conversation_id for r in self.results if r.conversation_id]
        unique_convs = len(set(conv_ids))
        print(f"\n  대화 격리 검증:")
        print(f"    - 생성된 대화 수: {unique_convs}")
        print(f"    - 대화 ID 사용: {len(conv_ids)}")
        
        print("\n" + "=" * 70)
        
        # 상세 결과
        if failed > 0:
            print("\n❌ 실패한 테스트:")
            for r in self.results:
                if not r.success:
                    print(f"  - [{r.user}] {r.test_case}: {r.error}")


async def main():
    tester = EnterpriseTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())



