"""
MCP Hub Token Management Service

사용자별 MCPHub 토큰을 관리하는 서비스입니다.
토큰은 AES-256-GCM으로 암호화되어 저장됩니다.
"""

import os
import base64
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MCPTokenService:
    """사용자별 MCP Hub 토큰 관리 서비스"""
    
    def __init__(self):
        # 암호화 키 (환경변수에서 가져오거나 기본값 사용)
        # 프로덕션에서는 반드시 안전한 키를 설정해야 함
        key_base64 = os.getenv("MCP_TOKEN_ENCRYPTION_KEY")
        if key_base64:
            self._key = base64.b64decode(key_base64)
        else:
            # 개발용 기본 키 (32바이트 = 256비트)
            logger.warning("Using default encryption key. Set MCP_TOKEN_ENCRYPTION_KEY in production!")
            self._key = b"k-jarvis-dev-key-32-bytes-long!!"
        
        self._aesgcm = AESGCM(self._key)
    
    def _encrypt_token(self, token: str) -> str:
        """토큰을 AES-256-GCM으로 암호화"""
        nonce = os.urandom(12)  # 96비트 nonce
        encrypted = self._aesgcm.encrypt(nonce, token.encode('utf-8'), None)
        # nonce + encrypted를 base64로 인코딩
        return base64.b64encode(nonce + encrypted).decode('utf-8')
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """암호화된 토큰을 복호화"""
        data = base64.b64decode(encrypted_token)
        nonce = data[:12]
        ciphertext = data[12:]
        decrypted = self._aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode('utf-8')
    
    async def save_token(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        token: str,
        token_name: str = "default",
        expires_at: Optional[datetime] = None
    ) -> dict:
        """
        사용자의 MCP Hub 토큰을 저장합니다.
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            token: MCPHub 토큰 (평문)
            token_name: 토큰 별칭
            expires_at: 만료 시각
            
        Returns:
            저장된 토큰 정보 (토큰 자체는 포함되지 않음)
        """
        encrypted = self._encrypt_token(token)
        
        # 기존 토큰이 있으면 업데이트, 없으면 생성
        query = """
            INSERT INTO user_mcp_tokens (user_id, encrypted_token, token_name, expires_at, is_active)
            VALUES (:user_id, :encrypted_token, :token_name, :expires_at, true)
            ON CONFLICT (user_id, token_name) DO UPDATE SET
                encrypted_token = :encrypted_token,
                expires_at = :expires_at,
                is_active = true,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, token_name, is_active, expires_at, created_at, updated_at
        """
        
        from sqlalchemy import text
        result = await db.execute(
            text(query),
            {
                "user_id": str(user_id),
                "encrypted_token": encrypted,
                "token_name": token_name,
                "expires_at": expires_at
            }
        )
        await db.commit()
        
        row = result.fetchone()
        logger.info(f"MCP token saved for user {user_id} (name: {token_name})")
        
        return {
            "id": str(row.id),
            "token_name": row.token_name,
            "is_active": row.is_active,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat()
        }
    
    async def get_token(
        self, 
        db: AsyncSession, 
        user_id: UUID,
        token_name: str = "default"
    ) -> Optional[str]:
        """
        사용자의 MCP Hub 토큰을 가져옵니다.
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            token_name: 토큰 별칭
            
        Returns:
            복호화된 토큰 또는 None
        """
        from sqlalchemy import text
        
        query = """
            SELECT encrypted_token, expires_at
            FROM user_mcp_tokens
            WHERE user_id = :user_id 
              AND token_name = :token_name 
              AND is_active = true
        """
        
        result = await db.execute(
            text(query),
            {"user_id": str(user_id), "token_name": token_name}
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        # 만료 확인
        if row.expires_at and row.expires_at < datetime.now(timezone.utc):
            logger.warning(f"MCP token expired for user {user_id}")
            return None
        
        # 마지막 사용 시각 업데이트
        await db.execute(
            text("""
                UPDATE user_mcp_tokens 
                SET last_used_at = CURRENT_TIMESTAMP 
                WHERE user_id = :user_id AND token_name = :token_name
            """),
            {"user_id": str(user_id), "token_name": token_name}
        )
        await db.commit()
        
        return self._decrypt_token(row.encrypted_token)
    
    async def get_token_status(
        self, 
        db: AsyncSession, 
        user_id: UUID,
        token_name: str = "default"
    ) -> Optional[dict]:
        """
        토큰 상태를 확인합니다.
        
        Returns:
            토큰 상태 정보 또는 None
        """
        from sqlalchemy import text
        
        query = """
            SELECT id, token_name, is_active, last_used_at, expires_at, created_at, updated_at
            FROM user_mcp_tokens
            WHERE user_id = :user_id AND token_name = :token_name
        """
        
        result = await db.execute(
            text(query),
            {"user_id": str(user_id), "token_name": token_name}
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        is_expired = row.expires_at and row.expires_at < datetime.now(timezone.utc)
        
        return {
            "id": str(row.id),
            "token_name": row.token_name,
            "is_active": row.is_active,
            "is_expired": is_expired,
            "is_valid": row.is_active and not is_expired,
            "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat()
        }
    
    async def delete_token(
        self, 
        db: AsyncSession, 
        user_id: UUID,
        token_name: str = "default"
    ) -> bool:
        """
        토큰을 삭제합니다.
        
        Returns:
            삭제 성공 여부
        """
        from sqlalchemy import text
        
        result = await db.execute(
            text("""
                DELETE FROM user_mcp_tokens
                WHERE user_id = :user_id AND token_name = :token_name
            """),
            {"user_id": str(user_id), "token_name": token_name}
        )
        await db.commit()
        
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"MCP token deleted for user {user_id} (name: {token_name})")
        
        return deleted
    
    async def deactivate_token(
        self, 
        db: AsyncSession, 
        user_id: UUID,
        token_name: str = "default"
    ) -> bool:
        """
        토큰을 비활성화합니다 (삭제하지 않고).
        
        Returns:
            비활성화 성공 여부
        """
        from sqlalchemy import text
        
        result = await db.execute(
            text("""
                UPDATE user_mcp_tokens
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = :user_id AND token_name = :token_name
            """),
            {"user_id": str(user_id), "token_name": token_name}
        )
        await db.commit()
        
        return result.rowcount > 0
    
    async def list_user_tokens(
        self, 
        db: AsyncSession, 
        user_id: UUID
    ) -> list[dict]:
        """
        사용자의 모든 토큰 목록을 가져옵니다.
        """
        from sqlalchemy import text
        
        result = await db.execute(
            text("""
                SELECT id, token_name, is_active, last_used_at, expires_at, created_at, updated_at
                FROM user_mcp_tokens
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {"user_id": str(user_id)}
        )
        
        tokens = []
        for row in result.fetchall():
            is_expired = row.expires_at and row.expires_at < datetime.now(timezone.utc)
            tokens.append({
                "id": str(row.id),
                "token_name": row.token_name,
                "is_active": row.is_active,
                "is_expired": is_expired,
                "is_valid": row.is_active and not is_expired,
                "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None,
                "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat()
            })
        
        return tokens


# 싱글톤 인스턴스
_mcp_token_service: Optional[MCPTokenService] = None


def get_mcp_token_service() -> MCPTokenService:
    """MCPTokenService 싱글톤 인스턴스를 반환합니다."""
    global _mcp_token_service
    if _mcp_token_service is None:
        _mcp_token_service = MCPTokenService()
    return _mcp_token_service

