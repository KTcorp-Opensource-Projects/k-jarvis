"""
Agent Vector Store - pgvector 기반 에이전트 벡터 검색
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import asyncpg
from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class AgentRoutingMetadata:
    """에이전트 라우팅 메타데이터"""
    agent_name: str
    agent_url: str
    domain: str
    category: str
    description: str
    keywords: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    is_active: bool = True
    
    @classmethod
    def from_agent_card(cls, agent_card: Dict[str, Any], url: str) -> "AgentRoutingMetadata":
        """AgentCard에서 메타데이터 추출"""
        # routing 확장 필드 확인
        routing = agent_card.get("routing", {})
        
        # 기본값 추론
        name = agent_card.get("name", "Unknown Agent")
        description = agent_card.get("description", "")
        
        # 도메인/카테고리 추론 (routing 필드가 없는 경우)
        domain = routing.get("domain", cls._infer_domain(name, description))
        category = routing.get("category", cls._infer_category(name))
        keywords = routing.get("keywords", cls._infer_keywords(name, description))
        
        # capabilities 추론
        skills = agent_card.get("skills", [])
        capabilities = routing.get("capabilities", [])
        if not capabilities and skills:
            capabilities = [s.get("id", s.get("name", "")) for s in skills if isinstance(s, dict)]
        
        return cls(
            agent_name=name,
            agent_url=url,
            domain=domain,
            category=category,
            description=description,
            keywords=keywords,
            capabilities=capabilities,
            is_active=True
        )
    
    @staticmethod
    def _infer_domain(name: str, description: str) -> str:
        """이름/설명에서 도메인 추론"""
        text = f"{name} {description}".lower()
        
        if any(k in text for k in ["jira", "이슈", "issue", "프로젝트", "스프린트"]):
            return "project_management"
        elif any(k in text for k in ["confluence", "문서", "wiki", "페이지"]):
            return "documentation"
        elif any(k in text for k in ["slack", "메시지", "채널", "알림"]):
            return "communication"
        elif any(k in text for k in ["github", "gitlab", "코드", "pr", "커밋"]):
            return "development"
        else:
            return "general"
    
    @staticmethod
    def _infer_category(name: str) -> str:
        """이름에서 카테고리 추론"""
        name_lower = name.lower()
        
        for category in ["jira", "confluence", "slack", "github", "gitlab", "notion", "asana"]:
            if category in name_lower:
                return category
        
        return name_lower.replace(" ", "_").replace("ai", "").replace("agent", "").strip("_")
    
    @staticmethod
    def _infer_keywords(name: str, description: str) -> List[str]:
        """이름/설명에서 키워드 추론"""
        keywords = []
        text = f"{name} {description}".lower()
        
        # 알려진 키워드 매핑
        keyword_map = {
            "jira": ["jira", "지라", "이슈", "issue", "프로젝트", "스프린트"],
            "confluence": ["confluence", "컨플루언스", "문서", "wiki", "페이지"],
            "slack": ["slack", "슬랙", "메시지", "채널"],
            "github": ["github", "깃헙", "코드", "pr", "커밋"],
        }
        
        for key, words in keyword_map.items():
            if key in text:
                keywords.extend(words)
        
        return list(set(keywords))


class AgentVectorStore:
    """pgvector 기반 에이전트 벡터 저장소"""
    
    EMBEDDING_MODEL = "text-embedding-ada-002"
    EMBEDDING_DIMENSION = 1536
    
    def __init__(self):
        self.settings = get_settings()
        self._pool: Optional[asyncpg.Pool] = None
        self._openai_client: Optional[AsyncOpenAI] = None
    
    async def initialize(self):
        """데이터베이스 연결 풀 초기화"""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.settings.db_host,
                port=self.settings.db_port,
                database=self.settings.db_name,
                user=self.settings.db_user,
                password=self.settings.db_password or "",
                min_size=2,
                max_size=10
            )
            logger.info("AgentVectorStore: Database pool initialized")
        
        if self._openai_client is None and self.settings.openai_api_key:
            self._openai_client = AsyncOpenAI(api_key=self.settings.openai_api_key)
            logger.info("AgentVectorStore: OpenAI client initialized")
    
    async def close(self):
        """연결 풀 종료"""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성"""
        if not self._openai_client:
            raise ValueError("OpenAI client not initialized. Set OPENAI_API_KEY.")
        
        response = await self._openai_client.embeddings.create(
            model=self.EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    
    async def upsert_agent(self, metadata: AgentRoutingMetadata) -> bool:
        """에이전트 메타데이터 추가/업데이트"""
        await self.initialize()
        
        try:
            # 임베딩 생성
            embedding = await self._generate_embedding(metadata.description)
            embedding_str = f"[{','.join(map(str, embedding))}]"
            
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_routing_metadata 
                    (agent_name, agent_url, domain, category, keywords, capabilities, description, description_embedding, is_active, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::vector, $9, CURRENT_TIMESTAMP)
                    ON CONFLICT (agent_name) DO UPDATE SET
                        agent_url = EXCLUDED.agent_url,
                        domain = EXCLUDED.domain,
                        category = EXCLUDED.category,
                        keywords = EXCLUDED.keywords,
                        capabilities = EXCLUDED.capabilities,
                        description = EXCLUDED.description,
                        description_embedding = EXCLUDED.description_embedding,
                        is_active = EXCLUDED.is_active,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    metadata.agent_name,
                    metadata.agent_url,
                    metadata.domain,
                    metadata.category,
                    metadata.keywords,
                    metadata.capabilities,
                    metadata.description,
                    embedding_str,
                    metadata.is_active
                )
            
            logger.info(f"Upserted agent: {metadata.agent_name} (domain: {metadata.domain})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert agent {metadata.agent_name}: {e}")
            return False
    
    async def remove_agent(self, agent_name: str) -> bool:
        """에이전트 제거 (soft delete)"""
        await self.initialize()
        
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "UPDATE agent_routing_metadata SET is_active = false WHERE agent_name = $1",
                    agent_name
                )
            logger.info(f"Removed agent: {agent_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove agent {agent_name}: {e}")
            return False
    
    async def search_similar(
        self,
        query: str,
        limit: int = 5,
        domain_filter: Optional[str] = None,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """유사 에이전트 벡터 검색"""
        await self.initialize()
        
        try:
            # 쿼리 임베딩 생성
            query_embedding = await self._generate_embedding(query)
            embedding_str = f"[{','.join(map(str, query_embedding))}]"
            
            # 도메인 필터 조건
            domain_condition = ""
            params = [embedding_str, threshold, limit]
            
            if domain_filter:
                domain_condition = "AND domain = $4"
                params.append(domain_filter)
            
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(f"""
                    SELECT 
                        agent_name,
                        agent_url,
                        domain,
                        category,
                        keywords,
                        capabilities,
                        description,
                        1 - (description_embedding <=> $1::vector) as similarity
                    FROM agent_routing_metadata
                    WHERE is_active = true
                    AND 1 - (description_embedding <=> $1::vector) > $2
                    {domain_condition}
                    ORDER BY description_embedding <=> $1::vector
                    LIMIT $3
                """, *params)
            
            results = []
            for row in rows:
                results.append({
                    "agent_name": row["agent_name"],
                    "agent_url": row["agent_url"],
                    "domain": row["domain"],
                    "category": row["category"],
                    "keywords": row["keywords"],
                    "capabilities": row["capabilities"],
                    "description": row["description"],
                    "similarity": float(row["similarity"])
                })
            
            logger.info(f"Vector search for '{query[:50]}...' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """키워드 기반 에이전트 검색"""
        await self.initialize()
        
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        agent_name,
                        agent_url,
                        domain,
                        category,
                        keywords,
                        capabilities,
                        description
                    FROM agent_routing_metadata
                    WHERE is_active = true
                    AND keywords && $1
                    LIMIT $2
                """, keywords, limit)
            
            results = []
            for row in rows:
                # 매칭된 키워드 수 계산
                matched = len(set(keywords) & set(row["keywords"]))
                results.append({
                    "agent_name": row["agent_name"],
                    "agent_url": row["agent_url"],
                    "domain": row["domain"],
                    "category": row["category"],
                    "keywords": row["keywords"],
                    "capabilities": row["capabilities"],
                    "description": row["description"],
                    "matched_keywords": matched
                })
            
            # 매칭 키워드 수로 정렬
            results.sort(key=lambda x: x["matched_keywords"], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    async def get_all_agents(self) -> List[Dict[str, Any]]:
        """모든 활성 에이전트 조회"""
        await self.initialize()
        
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        agent_name,
                        agent_url,
                        domain,
                        category,
                        keywords,
                        capabilities,
                        description
                    FROM agent_routing_metadata
                    WHERE is_active = true
                    ORDER BY domain, agent_name
                """)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get all agents: {e}")
            return []
    
    async def get_agents_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """도메인별 에이전트 조회"""
        await self.initialize()
        
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        agent_name,
                        agent_url,
                        domain,
                        category,
                        keywords,
                        capabilities,
                        description
                    FROM agent_routing_metadata
                    WHERE is_active = true AND domain = $1
                    ORDER BY agent_name
                """, domain)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get agents by domain {domain}: {e}")
            return []


# 싱글톤 인스턴스
_vector_store: Optional[AgentVectorStore] = None


async def get_vector_store() -> AgentVectorStore:
    """벡터 저장소 싱글톤 인스턴스 반환"""
    global _vector_store
    if _vector_store is None:
        _vector_store = AgentVectorStore()
        await _vector_store.initialize()
    return _vector_store





