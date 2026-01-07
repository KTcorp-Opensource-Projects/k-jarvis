"""
Agent Registry Service
Manages agent registration, discovery, and health monitoring
"""
import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import httpx
import time

from .models import AgentInfo, AgentRegistration, AgentStatus, AgentSkill, AgentCard, AgentRoutingInfo, AgentRequirements
from .agent_vector_store import AgentRoutingMetadata, get_vector_store


@dataclass
class AgentMetrics:
    """Metrics for monitoring agent performance"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time_ms: float = 0
    last_response_time_ms: float = 0
    consecutive_failures: int = 0
    circuit_breaker_open: bool = False
    circuit_breaker_until: Optional[datetime] = None
    health_check_failures: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    # Recent response times (last 100)
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def avg_response_time_ms(self) -> float:
        """Calculate average response time"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time_ms / self.successful_requests
    
    @property
    def p95_response_time_ms(self) -> float:
        """Calculate P95 response time from recent requests"""
        if len(self.recent_response_times) == 0:
            return 0.0
        sorted_times = sorted(self.recent_response_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]
    
    def record_success(self, response_time_ms: float):
        """Record a successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_response_time_ms += response_time_ms
        self.last_response_time_ms = response_time_ms
        self.recent_response_times.append(response_time_ms)
        self.consecutive_failures = 0
        
        # Reset circuit breaker on success
        if self.circuit_breaker_open:
            self.circuit_breaker_open = False
            self.circuit_breaker_until = None
            logger.info(f"Circuit breaker closed after successful request")
    
    def record_failure(self, error: str):
        """Record a failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.last_error = error
        self.last_error_time = datetime.utcnow()
        
        # Open circuit breaker after 3 consecutive failures
        if self.consecutive_failures >= 3 and not self.circuit_breaker_open:
            self.circuit_breaker_open = True
            self.circuit_breaker_until = datetime.utcnow() + timedelta(seconds=60)
            logger.warning(f"Circuit breaker opened due to {self.consecutive_failures} consecutive failures")
    
    def is_available(self) -> bool:
        """Check if agent is available (circuit breaker not open)"""
        if not self.circuit_breaker_open:
            return True
        
        # Check if circuit breaker timeout has passed
        if self.circuit_breaker_until and datetime.utcnow() > self.circuit_breaker_until:
            # Allow one test request (half-open state)
            return True
        
        return False
    
    def to_dict(self) -> dict:
        """Convert metrics to dictionary"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.success_rate, 2),
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "p95_response_time_ms": round(self.p95_response_time_ms, 2),
            "last_response_time_ms": round(self.last_response_time_ms, 2),
            "consecutive_failures": self.consecutive_failures,
            "circuit_breaker_open": self.circuit_breaker_open,
            "health_check_failures": self.health_check_failures,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None
        }


class AgentRegistry:
    """
    Central registry for managing A2A agents.
    Handles registration, discovery, and health monitoring.
    """
    
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._metrics: Dict[str, AgentMetrics] = {}  # agent_id -> metrics
        self._health_check_interval = 30  # seconds
        self._agent_timeout = 120  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the registry background tasks"""
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Agent Registry started")
    
    async def stop(self):
        """Stop the registry background tasks"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Agent Registry stopped")
    
    async def register_agent(self, registration: AgentRegistration) -> AgentInfo:
        """
        Register a new agent or update existing registration.
        """
        # Check if agent already exists by URL
        existing_agent = self.get_agent_by_url(registration.url)
        
        if existing_agent:
            # Update existing agent
            existing_agent.name = registration.name
            existing_agent.description = registration.description
            existing_agent.version = registration.version
            existing_agent.skills = registration.skills
            existing_agent.capabilities = registration.capabilities
            existing_agent.last_seen = datetime.utcnow()
            existing_agent.status = AgentStatus.ONLINE
            
            logger.info(f"Updated agent registration: {registration.name} at {registration.url}")
            return existing_agent
        
        # Create new agent
        agent = AgentInfo(
            name=registration.name,
            description=registration.description,
            url=registration.url,
            version=registration.version,
            skills=registration.skills,
            capabilities=registration.capabilities,
            status=AgentStatus.ONLINE,
            last_seen=datetime.utcnow()
        )
        
        self._agents[agent.id] = agent
        self._metrics[agent.id] = AgentMetrics()  # Initialize metrics
        logger.info(f"Registered new agent: {registration.name} (ID: {agent.id}) at {registration.url}")
        
        return agent
    
    async def register_agent_by_url(self, url: str) -> AgentInfo:
        """
        Register an agent by fetching its Agent Card from URL (A2A Discovery).
        This is the A2A standard way to discover and register agents.
        """
        # Check if agent already exists by URL
        existing_agent = self.get_agent_by_url(url)
        if existing_agent:
            # Refresh agent card
            card = await self._fetch_agent_card(url)
            if card:
                existing_agent.name = card.name
                existing_agent.description = card.description
                existing_agent.version = card.version
                existing_agent.skills = card.skills
                existing_agent.capabilities = card.capabilities
                existing_agent.last_seen = datetime.utcnow()
                existing_agent.status = AgentStatus.ONLINE
                logger.info(f"Refreshed agent: {card.name} at {url}")
                return existing_agent
            raise Exception(f"Failed to fetch Agent Card from {url}")
        
        # Fetch Agent Card from URL
        card = await self._fetch_agent_card(url)
        if not card:
            raise Exception(f"Failed to fetch Agent Card from {url}. Make sure the agent is running and accessible.")
        
        # Create new agent from card
        agent = AgentInfo(
            name=card.name,
            description=card.description,
            url=url,
            version=card.version,
            skills=card.skills,
            capabilities=card.capabilities,
            requirements=card.requirements,  # MCPHub 토큰 요구사항
            status=AgentStatus.ONLINE,
            last_seen=datetime.utcnow()
        )
        
        self._agents[agent.id] = agent
        self._metrics[agent.id] = AgentMetrics()  # Initialize metrics
        logger.info(f"Registered agent via A2A discovery: {card.name} (ID: {agent.id}) at {url}")
        
        # Sync to vector store for RAG-based routing
        asyncio.create_task(self._sync_to_vector_store(agent, card))
        
        return agent
    
    async def _fetch_agent_card(self, url: str) -> Optional[AgentCard]:
        """
        Fetch Agent Card from A2A agent URL.
        Tries multiple standard paths according to A2A spec.
        """
        paths_to_try = [
            "/.well-known/agent-card.json",  # A2A Spec standard
            "/.well-known/agent.json",       # Legacy
            "/agent-card",                   # Alternative
        ]
        
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            for path in paths_to_try:
                try:
                    full_url = f"{url.rstrip('/')}{path}"
                    response = await client.get(full_url)
                    if response.status_code == 200:
                        data = response.json()
                        # Convert skills if needed
                        if 'skills' in data:
                            skills = []
                            for s in data.get('skills', []):
                                skill = AgentSkill(
                                    id=s.get('id', ''),
                                    name=s.get('name', ''),
                                    description=s.get('description', ''),
                                    tags=s.get('tags', []),
                                    examples=s.get('examples', []),
                                    inputModes=s.get('inputModes', ['text/plain']),
                                    outputModes=s.get('outputModes', ['text/plain'])
                                )
                                skills.append(skill)
                            data['skills'] = skills
                        
                        # LangGraph 에이전트 호환: url 필드가 없으면 요청 URL 사용
                        if 'url' not in data or not data['url']:
                            data['url'] = url
                        
                        # routing 필드 변환 (에이전트 팀 제공)
                        if 'routing' in data and isinstance(data['routing'], dict):
                            routing_data = data['routing']
                            data['routing'] = AgentRoutingInfo(
                                domain=routing_data.get('domain', 'general'),
                                category=routing_data.get('category', ''),
                                keywords=routing_data.get('keywords', []),
                                capabilities=routing_data.get('capabilities', [])
                            )
                            logger.info(f"[Registry] Loaded routing info: domain={data['routing'].domain}, keywords={len(data['routing'].keywords)}")
                        
                        # requirements 필드 변환 (MCPHub 토큰 등)
                        if 'requirements' in data and isinstance(data['requirements'], dict):
                            req_data = data['requirements']
                            data['requirements'] = AgentRequirements(
                                mcpHubToken=req_data.get('mcpHubToken', False),
                                mcpServers=req_data.get('mcpServers', [])
                            )
                            logger.info(f"[Registry] Loaded requirements: mcpHubToken={data['requirements'].mcpHubToken}, mcpServers={data['requirements'].mcpServers}")
                        else:
                            data['requirements'] = AgentRequirements()
                        
                        return AgentCard(**data)
                except Exception as e:
                    logger.error(f"Failed to fetch from {full_url}: {type(e).__name__}: {e}")
                    continue
        
        logger.error(f"All paths failed for {url}")
        return None
    
    async def _sync_to_vector_store(self, agent: AgentInfo, card: Optional[AgentCard] = None):
        """Sync agent to vector store for RAG-based routing"""
        try:
            vector_store = await get_vector_store()
            
            # Extract routing info from card if available (에이전트 팀 제공)
            routing = {}
            if card and card.routing:
                routing = {
                    "domain": card.routing.domain,
                    "category": card.routing.category,
                    "keywords": card.routing.keywords,
                    "capabilities": card.routing.capabilities
                }
                logger.info(f"[VectorStore] Using agent-provided routing: {card.routing.domain}/{card.routing.category}")
            
            # Create metadata from agent info
            metadata = AgentRoutingMetadata.from_agent_card(
                agent_card={
                    "name": agent.name,
                    "description": agent.description or f"{agent.name} AI Agent",
                    "skills": [{"id": s.id, "name": s.name, "tags": s.tags} for s in agent.skills],
                    "routing": routing
                },
                url=agent.url
            )
            
            await vector_store.upsert_agent(metadata)
            logger.info(f"[VectorStore] Synced agent: {agent.name} (domain: {metadata.domain}, keywords: {len(metadata.keywords)})")
            
        except Exception as e:
            logger.warning(f"[VectorStore] Failed to sync agent {agent.name}: {e}")
    
    async def _remove_from_vector_store(self, agent_name: str):
        """Remove agent from vector store"""
        try:
            vector_store = await get_vector_store()
            await vector_store.remove_agent(agent_name)
            logger.info(f"[VectorStore] Removed agent: {agent_name}")
        except Exception as e:
            logger.warning(f"[VectorStore] Failed to remove agent {agent_name}: {e}")
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Remove an agent from the registry"""
        if agent_id in self._agents:
            agent = self._agents.pop(agent_id)
            self._metrics.pop(agent_id, None)  # Remove metrics too
            logger.info(f"Unregistered agent: {agent.name} (ID: {agent_id})")
            
            # Remove from vector store
            asyncio.create_task(self._remove_from_vector_store(agent.name))
            
            return True
        return False
    
    # =========================================================================
    # Metrics & Monitoring
    # =========================================================================
    
    def get_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get metrics for a specific agent"""
        return self._metrics.get(agent_id)
    
    def record_request_success(self, agent_id: str, response_time_ms: float):
        """Record a successful request to an agent"""
        if agent_id in self._metrics:
            self._metrics[agent_id].record_success(response_time_ms)
    
    def record_request_failure(self, agent_id: str, error: str):
        """Record a failed request to an agent"""
        if agent_id in self._metrics:
            self._metrics[agent_id].record_failure(error)
    
    def is_agent_available(self, agent_id: str) -> bool:
        """Check if agent is available (not circuit-broken and online)"""
        agent = self._agents.get(agent_id)
        if not agent or agent.status != AgentStatus.ONLINE:
            return False
        
        metrics = self._metrics.get(agent_id)
        if metrics and not metrics.is_available():
            return False
        
        return True
    
    def get_all_metrics(self) -> Dict[str, dict]:
        """Get metrics for all agents"""
        return {
            agent_id: metrics.to_dict()
            for agent_id, metrics in self._metrics.items()
        }
    
    def get_monitoring_status(self) -> dict:
        """Get comprehensive monitoring status for all agents"""
        agents_status = []
        
        for agent_id, agent in self._agents.items():
            metrics = self._metrics.get(agent_id, AgentMetrics())
            
            # Determine health status
            if agent.status == AgentStatus.OFFLINE:
                health = "critical"
            elif metrics.circuit_breaker_open:
                health = "warning"
            elif metrics.consecutive_failures > 0:
                health = "degraded"
            else:
                health = "healthy"
            
            agents_status.append({
                "id": agent_id,
                "name": agent.name,
                "url": agent.url,
                "version": agent.version,
                "status": agent.status.value,
                "health": health,
                "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
                "metrics": metrics.to_dict(),
                "skills_count": len(agent.skills)
            })
        
        # Summary statistics
        total = len(agents_status)
        online = sum(1 for a in agents_status if a["status"] == "online")
        healthy = sum(1 for a in agents_status if a["health"] == "healthy")
        
        return {
            "summary": {
                "total_agents": total,
                "online_agents": online,
                "healthy_agents": healthy,
                "offline_agents": total - online,
                "degraded_agents": sum(1 for a in agents_status if a["health"] in ["degraded", "warning"]),
                "overall_health": "healthy" if healthy == total else ("degraded" if online > 0 else "critical")
            },
            "agents": agents_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent by ID"""
        return self._agents.get(agent_id)
    
    def get_agent_by_url(self, url: str) -> Optional[AgentInfo]:
        """Get agent by URL"""
        for agent in self._agents.values():
            if agent.url == url:
                return agent
        return None
    
    def get_agent_by_name(self, name: str) -> Optional[AgentInfo]:
        """Get agent by name (case-insensitive)"""
        name_lower = name.lower()
        for agent in self._agents.values():
            if agent.name.lower() == name_lower:
                return agent
        return None
    
    def list_agents(self, include_offline: bool = False) -> List[AgentInfo]:
        """List all registered agents"""
        agents = list(self._agents.values())
        if not include_offline:
            agents = [a for a in agents if a.status == AgentStatus.ONLINE]
        return agents
    
    def search_agents(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skill: Optional[str] = None
    ) -> List[AgentInfo]:
        """
        Search agents by query, tags, or skill.
        """
        results = self.list_agents()
        
        if query:
            query_lower = query.lower()
            results = [
                a for a in results
                if query_lower in a.name.lower() or query_lower in a.description.lower()
            ]
        
        if tags:
            tag_set = set(t.lower() for t in tags)
            filtered = []
            for agent in results:
                agent_tags = set()
                for skill_obj in agent.skills:
                    agent_tags.update(t.lower() for t in skill_obj.tags)
                if agent_tags & tag_set:
                    filtered.append(agent)
            results = filtered
        
        if skill:
            skill_lower = skill.lower()
            results = [
                a for a in results
                if any(skill_lower in s.name.lower() for s in a.skills)
            ]
        
        return results
    
    def heartbeat(self, agent_id: str) -> bool:
        """Update agent last seen timestamp"""
        agent = self._agents.get(agent_id)
        if agent:
            agent.last_seen = datetime.utcnow()
            agent.status = AgentStatus.ONLINE
            return True
        return False
    
    async def check_agent_health(self, agent: AgentInfo) -> bool:
        """Check if an agent is healthy by attempting to fetch its agent card (A2A spec)"""
        start_time = time.time()
        metrics = self._metrics.get(agent.id, AgentMetrics())
        
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                # A2A Spec: Try well-known location first (official spec path)
                response = await client.get(f"{agent.url}/.well-known/agent-card.json")
                if response.status_code == 200:
                    agent.status = AgentStatus.ONLINE
                    agent.last_seen = datetime.utcnow()
                    metrics.health_check_failures = 0
                    return True
                
                # Fallback: Try legacy path
                response = await client.get(f"{agent.url}/.well-known/agent.json")
                if response.status_code == 200:
                    agent.status = AgentStatus.ONLINE
                    agent.last_seen = datetime.utcnow()
                    metrics.health_check_failures = 0
                    return True
                
                # Fallback: Try alternative endpoint
                response = await client.get(f"{agent.url}/agent-card")
                if response.status_code == 200:
                    agent.status = AgentStatus.ONLINE
                    agent.last_seen = datetime.utcnow()
                    metrics.health_check_failures = 0
                    return True
                
                # Fallback: Health endpoint
                response = await client.get(f"{agent.url}/health")
                if response.status_code == 200:
                    agent.status = AgentStatus.ONLINE
                    agent.last_seen = datetime.utcnow()
                    metrics.health_check_failures = 0
                    return True
                    
        except Exception as e:
            logger.debug(f"Health check failed for {agent.name}: {e}")
            metrics.health_check_failures += 1
            metrics.last_error = str(e)
            metrics.last_error_time = datetime.utcnow()
        
        # Check if agent has timed out
        if agent.last_seen:
            timeout = datetime.utcnow() - timedelta(seconds=self._agent_timeout)
            if agent.last_seen < timeout:
                agent.status = AgentStatus.OFFLINE
        else:
            agent.status = AgentStatus.OFFLINE
        
        return False
    
    async def _health_check_loop(self):
        """Background task to periodically check agent health"""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                
                for agent in list(self._agents.values()):
                    await self.check_agent_health(agent)
                
                # Log status
                online = sum(1 for a in self._agents.values() if a.status == AgentStatus.ONLINE)
                total = len(self._agents)
                logger.debug(f"Health check complete: {online}/{total} agents online")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")


# Global registry instance
registry = AgentRegistry()

