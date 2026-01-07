"""
Agent Catalog Service - Redis Cache Layer
Implements Cache-Aside Pattern for performance optimization
"""
import os
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import redis.asyncio as redis
from loguru import logger


class CacheManager:
    """
    Redis Cache Manager
    
    Cache Strategy:
    - Agent Cards: Cached with 5 min TTL, invalidated on update/delete
    - Health History: Only recent 100 records cached per agent
    - Dashboard: Cached with 30 sec TTL (frequently accessed)
    - Stats: Cached with 1 min TTL
    """
    
    # Cache Key Prefixes
    PREFIX_AGENT = "agent:"           # agent:{id}
    PREFIX_AGENT_LIST = "agents:"     # agents:online, agents:all
    PREFIX_HEALTH = "health:"         # health:{agent_id}
    PREFIX_DASHBOARD = "dashboard"    # dashboard
    PREFIX_STATS = "stats"            # stats
    
    # TTL Settings (seconds)
    TTL_AGENT = 300          # 5 minutes
    TTL_AGENT_LIST = 60      # 1 minute
    TTL_HEALTH = 120         # 2 minutes
    TTL_DASHBOARD = 30       # 30 seconds (frequently changing)
    TTL_STATS = 60           # 1 minute
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._url = os.getenv(
            "REDIS_URL",
            "redis://kjarvis-redis:6379/1"  # DB 1 for agent-catalog
        )
        self._enabled = True
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self._client = redis.from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._client.ping()
            logger.info(f"Redis cache connected: {self._url}")
        except Exception as e:
            logger.warning(f"Redis connection failed, cache disabled: {e}")
            self._enabled = False
            self._client = None
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            logger.info("Redis cache disconnected")
    
    def is_enabled(self) -> bool:
        """Check if cache is available"""
        return self._enabled and self._client is not None
    
    # =========================================================================
    # Generic Cache Operations
    # =========================================================================
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_enabled():
            return None
        
        try:
            data = await self._client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug(f"Cache get error for {key}: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        if not self.is_enabled():
            return False
        
        try:
            await self._client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.debug(f"Cache set error for {key}: {e}")
        return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_enabled():
            return False
        
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error for {key}: {e}")
        return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.is_enabled():
            return 0
        
        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self._client.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.debug(f"Cache delete pattern error for {pattern}: {e}")
        return 0
    
    # =========================================================================
    # Agent Card Cache
    # =========================================================================
    
    async def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get cached agent"""
        return await self.get(f"{self.PREFIX_AGENT}{agent_id}")
    
    async def set_agent(self, agent_id: str, agent_data: Dict) -> bool:
        """Cache agent data"""
        return await self.set(
            f"{self.PREFIX_AGENT}{agent_id}",
            agent_data,
            self.TTL_AGENT
        )
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Invalidate agent cache"""
        await self.delete(f"{self.PREFIX_AGENT}{agent_id}")
        # Also invalidate list caches
        await self.delete(f"{self.PREFIX_AGENT_LIST}online")
        await self.delete(f"{self.PREFIX_AGENT_LIST}all")
        return True
    
    async def get_agent_list(self, include_offline: bool = False) -> Optional[List[Dict]]:
        """Get cached agent list"""
        key = f"{self.PREFIX_AGENT_LIST}{'all' if include_offline else 'online'}"
        return await self.get(key)
    
    async def set_agent_list(self, agents: List[Dict], include_offline: bool = False) -> bool:
        """Cache agent list"""
        key = f"{self.PREFIX_AGENT_LIST}{'all' if include_offline else 'online'}"
        return await self.set(key, agents, self.TTL_AGENT_LIST)
    
    # =========================================================================
    # Health History Cache
    # =========================================================================
    
    async def get_health_history(
        self, 
        agent_id: Optional[str] = None, 
        limit: int = 100
    ) -> Optional[List[Dict]]:
        """Get cached health history"""
        key = f"{self.PREFIX_HEALTH}{agent_id or 'all'}"
        data = await self.get(key)
        if data:
            return data[:limit]
        return None
    
    async def set_health_history(
        self, 
        history: List[Dict], 
        agent_id: Optional[str] = None
    ) -> bool:
        """Cache health history (max 100 records)"""
        key = f"{self.PREFIX_HEALTH}{agent_id or 'all'}"
        # Only cache up to 100 records
        return await self.set(key, history[:100], self.TTL_HEALTH)
    
    async def append_health_record(
        self, 
        agent_id: str, 
        record: Dict
    ) -> bool:
        """Append a health record to cache (LIFO, max 100)"""
        if not self.is_enabled():
            return False
        
        try:
            # Get existing records
            key = f"{self.PREFIX_HEALTH}{agent_id}"
            existing = await self.get(key) or []
            
            # Prepend new record (most recent first)
            existing.insert(0, record)
            
            # Keep only last 100
            existing = existing[:100]
            
            await self.set(key, existing, self.TTL_HEALTH)
            
            # Also update 'all' cache
            all_key = f"{self.PREFIX_HEALTH}all"
            all_existing = await self.get(all_key) or []
            all_existing.insert(0, record)
            all_existing = all_existing[:100]
            await self.set(all_key, all_existing, self.TTL_HEALTH)
            
            return True
        except Exception as e:
            logger.debug(f"Cache append health record error: {e}")
        return False
    
    async def invalidate_health_cache(self, agent_id: Optional[str] = None):
        """Invalidate health cache"""
        if agent_id:
            await self.delete(f"{self.PREFIX_HEALTH}{agent_id}")
        await self.delete(f"{self.PREFIX_HEALTH}all")
    
    # =========================================================================
    # Dashboard Cache
    # =========================================================================
    
    async def get_dashboard(self) -> Optional[List[Dict]]:
        """Get cached dashboard"""
        return await self.get(self.PREFIX_DASHBOARD)
    
    async def set_dashboard(self, dashboard: List[Dict]) -> bool:
        """Cache dashboard (short TTL)"""
        return await self.set(self.PREFIX_DASHBOARD, dashboard, self.TTL_DASHBOARD)
    
    async def invalidate_dashboard(self):
        """Invalidate dashboard cache"""
        await self.delete(self.PREFIX_DASHBOARD)
    
    # =========================================================================
    # Stats Cache
    # =========================================================================
    
    async def get_stats(self) -> Optional[Dict]:
        """Get cached stats"""
        return await self.get(self.PREFIX_STATS)
    
    async def set_stats(self, stats: Dict) -> bool:
        """Cache stats"""
        return await self.set(self.PREFIX_STATS, stats, self.TTL_STATS)
    
    async def invalidate_stats(self):
        """Invalidate stats cache"""
        await self.delete(self.PREFIX_STATS)
    
    # =========================================================================
    # Bulk Invalidation
    # =========================================================================
    
    async def invalidate_all(self):
        """Invalidate all agent-catalog caches"""
        patterns = [
            f"{self.PREFIX_AGENT}*",
            f"{self.PREFIX_AGENT_LIST}*",
            f"{self.PREFIX_HEALTH}*",
            self.PREFIX_DASHBOARD,
            self.PREFIX_STATS
        ]
        
        total = 0
        for pattern in patterns:
            count = await self.delete_pattern(pattern)
            total += count
        
        logger.info(f"Invalidated {total} cache keys")
        return total
    
    # =========================================================================
    # Real-time Agent Status (using Redis Pub/Sub or simple key)
    # =========================================================================
    
    async def update_agent_status(self, agent_id: str, status: str, last_seen: str):
        """Update agent status in real-time (short TTL)"""
        if not self.is_enabled():
            return
        
        key = f"{self.PREFIX_AGENT}{agent_id}:status"
        await self.set(key, {
            "status": status,
            "last_seen": last_seen
        }, ttl=120)  # 2 minutes
        
        # Invalidate dashboard and agent cache for fresh data
        await self.invalidate_dashboard()
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get real-time agent status"""
        return await self.get(f"{self.PREFIX_AGENT}{agent_id}:status")


# Global cache instance
cache = CacheManager()

