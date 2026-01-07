"""
Hybrid Agent Router - 키워드 매칭 + pgvector RAG 기반 라우팅
"""
import json
from typing import Optional, List, Dict, Any
from loguru import logger

from .config import get_settings
from .models import AgentInfo, RoutingDecision
from .registry import registry
from .llm_client import get_llm_client, BaseLLMClient
from .agent_vector_store import (
    AgentVectorStore, 
    AgentRoutingMetadata,
    get_vector_store
)


class HybridRouter:
    """
    하이브리드 에이전트 라우터
    
    라우팅 우선순위:
    1. 명시적 에이전트 이름 매칭 (메시지에 "jira", "confluence" 등 포함)
    2. 벡터 유사도 검색 (pgvector RAG)
    3. 키워드 기반 매칭 (fallback)
    4. LLM 기반 라우팅 (최종 fallback)
    """
    
    # 명시적 에이전트 키워드 매핑
    EXPLICIT_KEYWORDS = {
        "jira": ["jira", "지라", "이슈", "issue", "티켓", "ticket", "스프린트", "sprint"],
        "confluence": ["confluence", "컨플루언스", "문서", "wiki", "페이지", "page"],
        "slack": ["slack", "슬랙", "메시지", "채널", "channel"],
        "github": ["github", "깃헙", "pr", "커밋", "commit", "리포", "repo"],
        "notion": ["notion", "노션"],
        "asana": ["asana", "아사나"],
    }
    
    # 도메인 키워드 매핑
    DOMAIN_KEYWORDS = {
        "project_management": ["프로젝트", "이슈", "태스크", "할일", "스프린트", "진행", "상태"],
        "documentation": ["문서", "보고서", "회의록", "작성", "기록", "위키"],
        "communication": ["알림", "공유", "전달", "메시지", "채널"],
        "development": ["코드", "배포", "빌드", "테스트", "개발"],
    }
    
    def __init__(self):
        self.settings = get_settings()
        self.llm_client: Optional[BaseLLMClient] = get_llm_client()
        self.use_llm = self.llm_client is not None and self.llm_client.is_available()
        self._vector_store: Optional[AgentVectorStore] = None
    
    async def _get_vector_store(self) -> AgentVectorStore:
        """벡터 저장소 인스턴스 반환"""
        if self._vector_store is None:
            self._vector_store = await get_vector_store()
        return self._vector_store
    
    async def route(
        self,
        message: str,
        enabled_agent_ids: Optional[List[str]] = None
    ) -> Optional[RoutingDecision]:
        """
        메시지를 분석하여 최적의 에이전트로 라우팅
        
        Args:
            message: 사용자 메시지
            enabled_agent_ids: 활성화된 에이전트 ID 목록 (선택적)
        
        Returns:
            RoutingDecision 또는 None
        """
        # 레지스트리에서 에이전트 목록 조회
        all_agents = registry.list_agents()
        
        # 활성화된 에이전트만 필터링
        if enabled_agent_ids is not None:
            agents = [a for a in all_agents if a.id in enabled_agent_ids]
            logger.info(f"Filtering to {len(agents)} enabled agents out of {len(all_agents)} total")
        else:
            agents = all_agents
        
        if not agents:
            logger.warning("No agents available for routing")
            return None
        
        message_lower = message.lower()
        
        # ========================================
        # Step 1: 명시적 에이전트 이름 매칭
        # ========================================
        explicit_match = self._explicit_agent_match(message_lower, agents)
        if explicit_match:
            logger.info(f"[HybridRouter] Explicit match: {explicit_match.agent_name}")
            return explicit_match
        
        # ========================================
        # Step 2: pgvector RAG 기반 검색
        # ========================================
        try:
            vector_store = await self._get_vector_store()
            
            # 도메인 추론
            inferred_domain = self._infer_domain(message_lower)
            
            # 벡터 검색
            vector_results = await vector_store.search_similar(
                query=message,
                limit=3,
                domain_filter=inferred_domain if inferred_domain else None,
                threshold=0.5
            )
            
            if vector_results:
                best_match = vector_results[0]
                
                # 레지스트리에서 에이전트 찾기
                matched_agent = None
                for agent in agents:
                    if agent.name == best_match["agent_name"]:
                        matched_agent = agent
                        break
                
                if matched_agent:
                    logger.info(
                        f"[HybridRouter] Vector search match: {matched_agent.name} "
                        f"(similarity: {best_match['similarity']:.3f})"
                    )
                    return RoutingDecision(
                        agent_id=matched_agent.id,
                        agent_name=matched_agent.name,
                        agent_url=matched_agent.url,
                        confidence=best_match["similarity"],
                        reasoning=f"Vector similarity search (domain: {best_match['domain']})"
                    )
        
        except Exception as e:
            logger.warning(f"[HybridRouter] Vector search failed: {e}")
        
        # ========================================
        # Step 3: 키워드 기반 매칭 (Fallback)
        # ========================================
        keyword_match = self._keyword_match(message_lower, agents)
        if keyword_match:
            logger.info(f"[HybridRouter] Keyword match: {keyword_match.agent_name}")
            return keyword_match
        
        # ========================================
        # Step 4: LLM 기반 라우팅 (최종 Fallback)
        # ========================================
        if self.use_llm:
            llm_match = await self._llm_route(message, agents)
            if llm_match:
                logger.info(f"[HybridRouter] LLM match: {llm_match.agent_name}")
                return llm_match
        
        logger.warning(f"[HybridRouter] No suitable agent found for: {message[:50]}...")
        return None
    
    def _explicit_agent_match(
        self,
        message_lower: str,
        agents: List[AgentInfo]
    ) -> Optional[RoutingDecision]:
        """명시적 에이전트 이름 매칭"""
        for agent_type, keywords in self.EXPLICIT_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                # 해당 타입의 에이전트 찾기
                for agent in agents:
                    if agent_type in agent.name.lower():
                        return RoutingDecision(
                            agent_id=agent.id,
                            agent_name=agent.name,
                            agent_url=agent.url,
                            confidence=0.95,
                            reasoning=f"Explicit keyword match: '{agent_type}'"
                        )
        return None
    
    def _infer_domain(self, message_lower: str) -> Optional[str]:
        """메시지에서 도메인 추론"""
        domain_scores = {}
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return None
    
    def _keyword_match(
        self,
        message_lower: str,
        agents: List[AgentInfo]
    ) -> Optional[RoutingDecision]:
        """키워드 기반 에이전트 매칭"""
        best_match = None
        best_score = 0
        
        for agent in agents:
            score = 0
            
            # 에이전트 이름/설명에서 키워드 매칭
            agent_text = f"{agent.name} {agent.description}".lower()
            
            for word in message_lower.split():
                if len(word) > 2 and word in agent_text:
                    score += 1
            
            # 스킬 태그 매칭
            for skill in agent.skills:
                if skill.tags:
                    for tag in skill.tags:
                        if tag.lower() in message_lower:
                            score += 2
            
            if score > best_score:
                best_score = score
                best_match = agent
        
        if best_match and best_score >= 2:
            return RoutingDecision(
                agent_id=best_match.id,
                agent_name=best_match.name,
                agent_url=best_match.url,
                confidence=min(0.7, 0.5 + (best_score * 0.1)),
                reasoning=f"Keyword match (score: {best_score})"
            )
        
        return None
    
    async def _llm_route(
        self,
        message: str,
        agents: List[AgentInfo]
    ) -> Optional[RoutingDecision]:
        """LLM 기반 라우팅"""
        if not self.use_llm:
            return None
        
        agents_info = "\n".join([
            f"- {a.name}: {a.description}"
            for a in agents
        ])
        
        prompt = f"""당신은 에이전트 라우팅 시스템입니다.
사용자 메시지를 분석하여 가장 적합한 에이전트를 선택하세요.

사용자 메시지: {message}

사용 가능한 에이전트:
{agents_info}

JSON 형식으로 응답하세요:
{{
    "agent_name": "선택한 에이전트 이름",
    "confidence": 0.0~1.0 사이 신뢰도,
    "reasoning": "선택 이유"
}}

적합한 에이전트가 없으면 agent_name: null로 응답하세요."""
        
        try:
            response = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            if not result.get("agent_name"):
                return None
            
            # 에이전트 찾기
            for agent in agents:
                if agent.name == result["agent_name"]:
                    return RoutingDecision(
                        agent_id=agent.id,
                        agent_name=agent.name,
                        agent_url=agent.url,
                        confidence=result.get("confidence", 0.6),
                        reasoning=result.get("reasoning", "LLM routing")
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"[HybridRouter] LLM routing failed: {e}")
            return None
    
    async def sync_agents_to_vector_store(self):
        """레지스트리의 에이전트를 벡터 저장소에 동기화"""
        vector_store = await self._get_vector_store()
        agents = registry.list_agents()
        
        synced_count = 0
        for agent in agents:
            try:
                # AgentInfo에서 메타데이터 생성
                metadata = AgentRoutingMetadata(
                    agent_name=agent.name,
                    agent_url=agent.url,
                    domain=self._infer_agent_domain(agent),
                    category=self._infer_agent_category(agent),
                    description=agent.description or f"{agent.name} agent",
                    keywords=self._extract_keywords(agent),
                    capabilities=[s.name for s in agent.skills] if agent.skills else [],
                    is_active=True
                )
                
                success = await vector_store.upsert_agent(metadata)
                if success:
                    synced_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to sync agent {agent.name}: {e}")
        
        logger.info(f"[HybridRouter] Synced {synced_count}/{len(agents)} agents to vector store")
        return synced_count
    
    def _infer_agent_domain(self, agent: AgentInfo) -> str:
        """에이전트의 도메인 추론"""
        name_lower = agent.name.lower()
        desc_lower = (agent.description or "").lower()
        text = f"{name_lower} {desc_lower}"
        
        if any(k in text for k in ["jira", "asana", "monday", "이슈", "프로젝트"]):
            return "project_management"
        elif any(k in text for k in ["confluence", "notion", "wiki", "문서"]):
            return "documentation"
        elif any(k in text for k in ["slack", "teams", "email", "메시지"]):
            return "communication"
        elif any(k in text for k in ["github", "gitlab", "jenkins", "코드"]):
            return "development"
        else:
            return "general"
    
    def _infer_agent_category(self, agent: AgentInfo) -> str:
        """에이전트의 카테고리 추론"""
        name_lower = agent.name.lower()
        
        for category in ["jira", "confluence", "slack", "github", "gitlab", "notion", "asana"]:
            if category in name_lower:
                return category
        
        # 이름에서 카테고리 추출
        return name_lower.replace(" ai agent", "").replace(" agent", "").replace(" ", "_").strip()
    
    def _extract_keywords(self, agent: AgentInfo) -> List[str]:
        """에이전트에서 키워드 추출"""
        keywords = set()
        
        # 이름에서 추출
        name_lower = agent.name.lower()
        for agent_type, kws in self.EXPLICIT_KEYWORDS.items():
            if agent_type in name_lower:
                keywords.update(kws)
        
        # 스킬 태그에서 추출
        for skill in agent.skills:
            if skill.tags:
                keywords.update([t.lower() for t in skill.tags])
        
        return list(keywords)


# 싱글톤 인스턴스
_hybrid_router: Optional[HybridRouter] = None


def get_hybrid_router() -> HybridRouter:
    """하이브리드 라우터 싱글톤 인스턴스 반환"""
    global _hybrid_router
    if _hybrid_router is None:
        _hybrid_router = HybridRouter()
    return _hybrid_router



