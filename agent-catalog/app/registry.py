"""
Agent Catalog Service - Registry
Manages agent registration, discovery, and health monitoring
PostgreSQL persistence + Redis Cache (Cache-Aside Pattern)
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from loguru import logger
import httpx
import uuid

from .models import (
    AgentInfo, AgentRegistration, AgentStatus, AgentSkill, 
    AgentCard, AgentRoutingInfo, AgentRequirements
)
from .database import db
from .cache import cache


class AgentCatalogRegistry:
    """
    Agent Catalog Registry with PostgreSQL persistence and Redis Cache
    
    Cache Strategy (Cache-Aside Pattern):
    - READ: Check cache first → If miss, read from DB → Store in cache
    - WRITE: Write to DB → Invalidate cache (or update cache)
    - DELETE: Delete from DB → Invalidate cache
    """
    
    def __init__(self):
        self._health_check_interval = 60  # seconds
        self._agent_timeout = 180  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        # Batch health records to reduce DB writes
        self._health_batch: List[Dict] = []
        self._health_batch_size = 10  # Flush to DB every 10 records
    
    async def start(self):
        """Start the registry, database, and cache connections"""
        await db.connect()
        await cache.connect()
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Agent Catalog Registry started (PostgreSQL + Redis Cache)")
    
    async def stop(self):
        """Stop the registry and close connections"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining health records
        await self._flush_health_batch()
        
        await cache.disconnect()
        await db.disconnect()
        logger.info("Agent Catalog Registry stopped")
    
    # =========================================================================
    # Agent Registration (Write Operations)
    # =========================================================================
    
    async def register_agent(self, registration: AgentRegistration) -> AgentInfo:
        """Register a new agent or update existing registration"""
        existing = await db.get_agent_by_url(registration.url)
        
        if existing:
            # Update existing agent
            updated = await db.update_agent(existing['id'], {
                'name': registration.name,
                'description': registration.description,
                'version': registration.version,
                'skills': [s.dict() for s in registration.skills],
                'capabilities': registration.capabilities,
                'status': 'online',
                'last_seen': datetime.utcnow()
            })
            
            # Invalidate cache
            await cache.delete_agent(existing['id'])
            
            logger.info(f"Updated agent: {registration.name} at {registration.url}")
            return self._dict_to_agent_info(updated)
        
        # Create new agent
        agent_id = str(uuid.uuid4())
        agent_data = {
            'id': agent_id,
            'name': registration.name,
            'description': registration.description,
            'url': registration.url,
            'version': registration.version,
            'skills': [s.dict() for s in registration.skills],
            'capabilities': registration.capabilities,
            'extensions': {},
            'status': 'online',
            'last_seen': datetime.utcnow()
        }
        
        created = await db.create_agent(agent_data)
        
        # Invalidate list cache (new agent added)
        await cache.delete_agent(agent_id)
        await cache.invalidate_stats()
        
        logger.info(f"Registered new agent: {registration.name} (ID: {agent_id})")
        
        return self._dict_to_agent_info(created)
    
    async def register_agent_by_url(self, url: str) -> AgentInfo:
        """Register an agent by fetching its Agent Card from URL (A2A Discovery)"""
        existing = await db.get_agent_by_url(url)
        
        if existing:
            # Refresh agent card
            card = await self._fetch_agent_card(url)
            if card:
                extensions = {
                    'requirements': card.requirements.dict() if card.requirements else {},
                    'routing': card.routing.dict() if card.routing else {}
                }
                
                updated = await db.update_agent(existing['id'], {
                    'name': card.name,
                    'description': card.description,
                    'version': card.version,
                    'skills': [s.dict() for s in card.skills],
                    'capabilities': card.capabilities,
                    'extensions': extensions,
                    'status': 'online',
                    'last_seen': datetime.utcnow()
                })
                
                # Invalidate cache
                await cache.delete_agent(existing['id'])
                
                logger.info(f"Refreshed agent: {card.name} at {url}")
                return self._dict_to_agent_info(updated)
            raise Exception(f"Failed to fetch Agent Card from {url}")
        
        # Fetch Agent Card from URL
        card = await self._fetch_agent_card(url)
        if not card:
            raise Exception(f"Failed to fetch Agent Card from {url}")
        
        # Create new agent from card
        agent_id = str(uuid.uuid4())
        extensions = {
            'requirements': card.requirements.dict() if card.requirements else {},
            'routing': card.routing.dict() if card.routing else {}
        }
        
        agent_data = {
            'id': agent_id,
            'name': card.name,
            'description': card.description,
            'url': url,
            'version': card.version,
            'protocol_version': card.protocolVersion,
            'skills': [s.dict() for s in card.skills],
            'capabilities': card.capabilities,
            'default_input_modes': card.defaultInputModes,
            'default_output_modes': card.defaultOutputModes,
            'extensions': extensions,
            'status': 'online',
            'last_seen': datetime.utcnow()
        }
        
        created = await db.create_agent(agent_data)
        
        # Invalidate caches
        await cache.delete_agent(agent_id)
        await cache.invalidate_stats()
        
        logger.info(f"Registered agent via A2A discovery: {card.name} (ID: {agent_id})")
        
        return self._dict_to_agent_info(created)
    
    async def _fetch_agent_card(self, url: str) -> Optional[AgentCard]:
        """Fetch Agent Card from A2A agent URL"""
        paths_to_try = [
            "/.well-known/agent-card.json",
            "/.well-known/agent.json",
            "/agent-card",
        ]
        
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            for path in paths_to_try:
                try:
                    full_url = f"{url.rstrip('/')}{path}"
                    response = await client.get(full_url)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Convert skills
                        if 'skills' in data:
                            skills = []
                            for s in data.get('skills', []):
                                skill = AgentSkill(
                                    id=s.get('id', str(uuid.uuid4())),
                                    name=s.get('name', ''),
                                    description=s.get('description', ''),
                                    tags=s.get('tags', []),
                                    examples=s.get('examples', [])
                                )
                                skills.append(skill)
                            data['skills'] = skills
                        
                        if 'url' not in data or not data['url']:
                            data['url'] = url
                        
                        # Convert routing
                        if 'routing' in data and isinstance(data['routing'], dict):
                            routing_data = data['routing']
                            data['routing'] = AgentRoutingInfo(
                                domain=routing_data.get('domain', 'general'),
                                category=routing_data.get('category', ''),
                                keywords=routing_data.get('keywords', []),
                                capabilities=routing_data.get('capabilities', [])
                            )
                        
                        # Convert requirements
                        if 'requirements' in data and isinstance(data['requirements'], dict):
                            req_data = data['requirements']
                            data['requirements'] = AgentRequirements(
                                mcpHubToken=req_data.get('mcpHubToken', False),
                                mcpServers=req_data.get('mcpServers', [])
                            )
                        else:
                            data['requirements'] = AgentRequirements()
                        
                        return AgentCard(**data)
                except Exception as e:
                    logger.debug(f"Failed to fetch from {full_url}: {e}")
                    continue
        
        return None
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Remove an agent from the registry"""
        agent = await db.get_agent_by_id(agent_id)
        if agent:
            success = await db.delete_agent(agent_id)
            if success:
                # Invalidate cache
                await cache.delete_agent(agent_id)
                await cache.invalidate_stats()
                logger.info(f"Unregistered agent: {agent['name']} (ID: {agent_id})")
            return success
        return False
    
    # =========================================================================
    # Agent Retrieval (Read Operations with Cache)
    # =========================================================================
    
    async def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent by ID (cache-aside)"""
        # Try cache first
        cached = await cache.get_agent(agent_id)
        if cached:
            logger.debug(f"Cache HIT: agent {agent_id}")
            return self._dict_to_agent_info(cached)
        
        # Cache miss - read from DB
        logger.debug(f"Cache MISS: agent {agent_id}")
        data = await db.get_agent_by_id(agent_id)
        
        if data:
            # Store in cache
            await cache.set_agent(agent_id, data)
        
        return self._dict_to_agent_info(data) if data else None
    
    async def get_agent_by_url(self, url: str) -> Optional[AgentInfo]:
        """Get agent by URL"""
        data = await db.get_agent_by_url(url)
        return self._dict_to_agent_info(data) if data else None
    
    async def get_agent_by_name(self, name: str) -> Optional[AgentInfo]:
        """Get agent by name (case-insensitive)"""
        data = await db.get_agent_by_name(name)
        return self._dict_to_agent_info(data) if data else None
    
    async def list_agents(self, include_offline: bool = False) -> List[AgentInfo]:
        """List all registered agents (cache-aside)"""
        # Try cache first
        cached = await cache.get_agent_list(include_offline)
        if cached:
            logger.debug(f"Cache HIT: agent list (offline={include_offline})")
            return [self._dict_to_agent_info(a) for a in cached]
        
        # Cache miss - read from DB
        logger.debug(f"Cache MISS: agent list (offline={include_offline})")
        agents_data = await db.list_agents(include_offline=include_offline)
        
        # Store in cache
        await cache.set_agent_list(agents_data, include_offline)
        
        return [self._dict_to_agent_info(a) for a in agents_data]
    
    async def search_agents(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skill: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[AgentInfo]:
        """Search agents by query, tags, skill, or domain (no cache - dynamic)"""
        agents_data = await db.search_agents(
            query=query,
            tags=tags,
            skill=skill,
            domain=domain
        )
        return [self._dict_to_agent_info(a) for a in agents_data]
    
    # =========================================================================
    # Health Check (Optimized with batching and caching)
    # =========================================================================
    
    async def check_agent_health(self, agent: AgentInfo) -> bool:
        """Check if an agent is healthy (with batched DB writes)"""
        start_time = time.time()
        is_healthy = False
        error_msg = None
        
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                # Try well-known location
                response = await client.get(f"{agent.url}/.well-known/agent.json")
                if response.status_code == 200:
                    is_healthy = True
                else:
                    # Try health endpoint
                    response = await client.get(f"{agent.url}/health")
                    if response.status_code == 200:
                        is_healthy = True
                        
        except Exception as e:
            error_msg = str(e)
            logger.debug(f"Health check failed for {agent.name}: {e}")
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Update status in DB
        new_status = 'online' if is_healthy else 'offline'
        now = datetime.utcnow()
        
        if is_healthy:
            await db.update_agent_status(agent.id, new_status, now)
        else:
            # Check timeout
            agent_data = await db.get_agent_by_id(agent.id)
            if agent_data and agent_data.get('last_seen'):
                last_seen = agent_data['last_seen']
                if isinstance(last_seen, str):
                    last_seen = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                
                timeout = datetime.utcnow() - timedelta(seconds=self._agent_timeout)
                if last_seen.replace(tzinfo=None) < timeout:
                    await db.update_agent_status(agent.id, 'offline')
        
        # Update cache with real-time status
        await cache.update_agent_status(agent.id, new_status, now.isoformat())
        
        # Create health record
        health_record = {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "agent_url": agent.url,
            "status": new_status,
            "response_time_ms": response_time_ms,
            "error_message": error_msg,
            "checked_at": now.isoformat()
        }
        
        # Add to Redis cache immediately (for real-time queries)
        await cache.append_health_record(agent.id, health_record)
        
        # Batch DB writes
        self._health_batch.append({
            "agent_id": agent.id,
            "status": new_status,
            "response_time_ms": response_time_ms,
            "error_message": error_msg
        })
        
        # Flush batch if full
        if len(self._health_batch) >= self._health_batch_size:
            await self._flush_health_batch()
        
        return is_healthy
    
    async def _flush_health_batch(self):
        """Flush batched health records to DB"""
        if not self._health_batch:
            return
        
        batch = self._health_batch.copy()
        self._health_batch.clear()
        
        for record in batch:
            try:
                await db.record_health_check(
                    record["agent_id"],
                    record["status"],
                    record["response_time_ms"],
                    record["error_message"]
                )
            except Exception as e:
                logger.error(f"Failed to flush health record: {e}")
    
    # =========================================================================
    # Statistics and Dashboard (Cached)
    # =========================================================================
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get catalog statistics (cached)"""
        # Try cache first
        cached = await cache.get_stats()
        if cached:
            logger.debug("Cache HIT: stats")
            return cached
        
        # Cache miss - read from DB
        logger.debug("Cache MISS: stats")
        stats = await db.get_stats()
        
        # Store in cache
        await cache.set_stats(stats)
        
        return stats
    
    async def get_dashboard(self) -> List[Dict[str, Any]]:
        """Get health dashboard (cached with short TTL)"""
        # Try cache first
        cached = await cache.get_dashboard()
        if cached:
            logger.debug("Cache HIT: dashboard")
            return cached
        
        # Cache miss - read from DB
        logger.debug("Cache MISS: dashboard")
        dashboard = await db.get_agent_health_summary()
        
        # Store in cache
        await cache.set_dashboard(dashboard)
        
        return dashboard
    
    async def get_health_history(
        self, 
        agent_id: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get health history (cache-aside)"""
        # Try cache first
        cached = await cache.get_health_history(agent_id, limit)
        if cached:
            logger.debug(f"Cache HIT: health history (agent={agent_id})")
            return cached
        
        # Cache miss - read from DB
        logger.debug(f"Cache MISS: health history (agent={agent_id})")
        history = await db.get_health_history(agent_id, limit)
        
        # Store in cache
        await cache.set_health_history(history, agent_id)
        
        return history
    
    # =========================================================================
    # Background Tasks
    # =========================================================================
    
    async def _health_check_loop(self):
        """Background task to periodically check agent health"""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                
                # Get agents from cache first if available
                agents = await self.list_agents(include_offline=True)
                
                for agent in agents:
                    await self.check_agent_health(agent)
                
                # Flush remaining health records
                await self._flush_health_batch()
                
                # Invalidate dashboard cache after health check
                await cache.invalidate_dashboard()
                
                stats = await self.get_stats()
                logger.debug(f"Health check: {stats['online_agents']}/{stats['total_agents']} agents online")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _dict_to_agent_info(self, data: Dict[str, Any]) -> AgentInfo:
        """Convert database dict to AgentInfo model"""
        if not data:
            return None
        
        # Parse skills
        skills = []
        for s in data.get('skills', []):
            if isinstance(s, dict):
                skills.append(AgentSkill(**s))
            elif isinstance(s, AgentSkill):
                skills.append(s)
        
        # Parse extensions
        extensions = data.get('extensions', {})
        requirements = None
        routing = None
        
        if extensions:
            if 'requirements' in extensions and extensions['requirements']:
                requirements = AgentRequirements(**extensions['requirements'])
            if 'routing' in extensions and extensions['routing']:
                routing = AgentRoutingInfo(**extensions['routing'])
        
        # Parse last_seen
        last_seen = data.get('last_seen')
        if isinstance(last_seen, str):
            last_seen = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
        
        # Parse created_at
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        return AgentInfo(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description', ''),
            url=data.get('url'),
            version=data.get('version', '1.0.0'),
            skills=skills,
            capabilities=data.get('capabilities', {}),
            requirements=requirements or AgentRequirements(),
            routing=routing,
            status=AgentStatus(data.get('status', 'unknown')),
            last_seen=last_seen,
            created_at=created_at or datetime.utcnow()
        )


# Global registry instance
registry = AgentCatalogRegistry()
