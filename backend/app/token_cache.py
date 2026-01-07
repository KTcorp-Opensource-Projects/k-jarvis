"""
Token Cache Service using Redis

MCPHub 토큰을 Redis에 캐싱하여 성능을 개선합니다.
TTL: 5분 (합의된 시간)
"""

import os
import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# Redis 연결 정보
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TOKEN_CACHE_TTL = int(os.getenv("TOKEN_CACHE_TTL", 300))  # 5분 = 300초


class TokenCacheService:
    """Redis 기반 토큰 캐시 서비스"""
    
    def __init__(self):
        self._redis = None
        self._enabled = False
        self._initialize()
    
    def _initialize(self):
        """Redis 연결 초기화"""
        try:
            import redis.asyncio as redis
            self._redis = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            self._enabled = True
            logger.info(f"[TokenCache] Redis cache enabled (TTL: {TOKEN_CACHE_TTL}s)")
        except ImportError:
            logger.warning("[TokenCache] redis library not installed, caching disabled")
            self._enabled = False
        except Exception as e:
            logger.warning(f"[TokenCache] Failed to connect to Redis: {e}, caching disabled")
            self._enabled = False
    
    def _get_cache_key(self, user_id: str, token_name: str = "default") -> str:
        """캐시 키 생성"""
        return f"mcp_token:{user_id}:{token_name}"
    
    async def get(self, user_id: UUID, token_name: str = "default") -> Optional[str]:
        """
        캐시에서 토큰 조회
        
        Args:
            user_id: 사용자 ID
            token_name: 토큰 별칭
            
        Returns:
            캐시된 토큰 또는 None
        """
        if not self._enabled or not self._redis:
            return None
        
        try:
            key = self._get_cache_key(str(user_id), token_name)
            token = await self._redis.get(key)
            if token:
                logger.debug(f"[TokenCache] Cache HIT for user {str(user_id)[:8]}...")
                return token
            logger.debug(f"[TokenCache] Cache MISS for user {str(user_id)[:8]}...")
            return None
        except Exception as e:
            logger.warning(f"[TokenCache] Get failed: {e}")
            return None
    
    async def set(
        self, 
        user_id: UUID, 
        token: str, 
        token_name: str = "default",
        ttl: int = None
    ) -> bool:
        """
        캐시에 토큰 저장
        
        Args:
            user_id: 사용자 ID
            token: 저장할 토큰
            token_name: 토큰 별칭
            ttl: TTL (초), None이면 기본값 사용
            
        Returns:
            저장 성공 여부
        """
        if not self._enabled or not self._redis:
            return False
        
        try:
            key = self._get_cache_key(str(user_id), token_name)
            await self._redis.setex(key, ttl or TOKEN_CACHE_TTL, token)
            logger.debug(f"[TokenCache] Cached token for user {str(user_id)[:8]}... (TTL: {ttl or TOKEN_CACHE_TTL}s)")
            return True
        except Exception as e:
            logger.warning(f"[TokenCache] Set failed: {e}")
            return False
    
    async def delete(self, user_id: UUID, token_name: str = "default") -> bool:
        """
        캐시에서 토큰 삭제
        
        Args:
            user_id: 사용자 ID
            token_name: 토큰 별칭
            
        Returns:
            삭제 성공 여부
        """
        if not self._enabled or not self._redis:
            return False
        
        try:
            key = self._get_cache_key(str(user_id), token_name)
            await self._redis.delete(key)
            logger.debug(f"[TokenCache] Deleted cache for user {str(user_id)[:8]}...")
            return True
        except Exception as e:
            logger.warning(f"[TokenCache] Delete failed: {e}")
            return False
    
    async def clear_user_tokens(self, user_id: UUID) -> int:
        """
        특정 사용자의 모든 캐시된 토큰 삭제
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            삭제된 키 개수
        """
        if not self._enabled or not self._redis:
            return 0
        
        try:
            pattern = f"mcp_token:{str(user_id)}:*"
            keys = []
            async for key in self._redis.scan_iter(pattern):
                keys.append(key)
            
            if keys:
                deleted = await self._redis.delete(*keys)
                logger.info(f"[TokenCache] Cleared {deleted} tokens for user {str(user_id)[:8]}...")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"[TokenCache] Clear failed: {e}")
            return 0
    
    @property
    def is_enabled(self) -> bool:
        """캐시 활성화 여부"""
        return self._enabled
    
    async def health_check(self) -> dict:
        """Redis 상태 확인"""
        if not self._enabled or not self._redis:
            return {"status": "disabled", "message": "Redis not configured"}
        
        try:
            await self._redis.ping()
            info = await self._redis.info("memory")
            return {
                "status": "healthy",
                "used_memory": info.get("used_memory_human", "unknown"),
                "ttl": TOKEN_CACHE_TTL
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# 싱글톤 인스턴스
_token_cache: Optional[TokenCacheService] = None


def get_token_cache() -> TokenCacheService:
    """TokenCacheService 싱글톤 인스턴스를 반환합니다."""
    global _token_cache
    if _token_cache is None:
        _token_cache = TokenCacheService()
    return _token_cache



