"""
Authentication service - business logic
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger
import uuid

from .models import (
    UserCreate, UserLogin, UserResponse, UserInDB,
    TokenResponse, TokenData
)
from .security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    decode_token, get_token_expire_time
)


class AuthService:
    """Authentication service"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> Optional[UserResponse]:
        """Create a new user"""
        try:
            # Check if username or email exists
            result = await db.execute(
                text("SELECT id FROM users WHERE email = :email OR username = :username"),
                {"email": user_data.email, "username": user_data.username}
            )
            if result.fetchone():
                return None  # Username or Email already exists
            
            # Hash password
            password_hash = get_password_hash(user_data.password)
            
            # Insert user (role_id=2 is 'user' by default)
            result = await db.execute(
                text("""
                    INSERT INTO users (username, email, password_hash, name, role_id)
                    VALUES (:username, :email, :password_hash, :name, 2)
                    RETURNING id, username, email, name, role_id, is_active, created_at, last_login
                """),
                {
                    "username": user_data.username,
                    "email": user_data.email,
                    "password_hash": password_hash,
                    "name": user_data.name
                }
            )
            row = result.fetchone()
            await db.commit()
            
            if row:
                return UserResponse(
                    id=row.id,
                    email=row.email,
                    name=row.name,
                    role="user",
                    is_active=row.is_active,
                    created_at=row.created_at,
                    last_login=row.last_login
                )
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            await db.rollback()
        
        return None
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username_or_email: str,
        password: str
    ) -> Optional[UserInDB]:
        """Authenticate user by username or email and password"""
        try:
            result = await db.execute(
                text("""
                    SELECT u.id, u.email, u.password_hash, u.name, u.role_id, 
                           r.name as role_name, u.is_active, u.created_at, u.last_login
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    WHERE (u.email = :identifier OR u.username = :identifier) AND u.is_active = true
                """),
                {"identifier": username_or_email}
            )
            row = result.fetchone()
            
            if row and verify_password(password, row.password_hash):
                # Update last_login
                await db.execute(
                    text("UPDATE users SET last_login = :now WHERE id = :id"),
                    {"now": datetime.utcnow(), "id": row.id}
                )
                await db.commit()
                
                return UserInDB(
                    id=row.id,
                    email=row.email,
                    password_hash=row.password_hash,
                    name=row.name,
                    role_id=row.role_id,
                    role_name=row.role_name,
                    is_active=row.is_active,
                    created_at=row.created_at,
                    last_login=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
        
        return None
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        try:
            result = await db.execute(
                text("""
                    SELECT u.id, u.email, u.password_hash, u.name, u.role_id,
                           r.name as role_name, u.is_active, u.created_at, u.last_login
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    WHERE u.id = :id
                """),
                {"id": user_id}
            )
            row = result.fetchone()
            
            if row:
                return UserInDB(
                    id=row.id,
                    email=row.email,
                    password_hash=row.password_hash,
                    name=row.name,
                    role_id=row.role_id,
                    role_name=row.role_name,
                    is_active=row.is_active,
                    created_at=row.created_at,
                    last_login=row.last_login
                )
                
        except Exception as e:
            logger.error(f"Error getting user: {e}")
        
        return None
    
    @staticmethod
    def create_tokens(user: UserInDB) -> TokenResponse:
        """Create access and refresh tokens for user"""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role_name
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=get_token_expire_time(),
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role_name,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login
            )
        )
    
    @staticmethod
    async def store_refresh_token(
        db: AsyncSession,
        user_id: str,
        refresh_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Store refresh token in database"""
        try:
            from ..config import get_settings
            settings = get_settings()
            from datetime import timedelta
            
            expires_at = datetime.utcnow() + timedelta(
                days=settings.jwt_refresh_token_expire_days
            )
            
            await db.execute(
                text("""
                    INSERT INTO user_sessions (user_id, refresh_token, user_agent, ip_address, expires_at)
                    VALUES (:user_id, :refresh_token, :user_agent, :ip_address, :expires_at)
                """),
                {
                    "user_id": user_id,
                    "refresh_token": refresh_token,
                    "user_agent": user_agent,
                    "ip_address": ip_address,
                    "expires_at": expires_at
                }
            )
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error storing refresh token: {e}")
            await db.rollback()
    
    @staticmethod
    async def revoke_refresh_token(db: AsyncSession, refresh_token: str):
        """Revoke (delete) refresh token"""
        try:
            await db.execute(
                text("DELETE FROM user_sessions WHERE refresh_token = :token"),
                {"token": refresh_token}
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            await db.rollback()
    
    @staticmethod
    async def validate_refresh_token(
        db: AsyncSession,
        refresh_token: str
    ) -> Optional[str]:
        """Validate refresh token and return user_id"""
        try:
            # Check token in database
            result = await db.execute(
                text("""
                    SELECT user_id FROM user_sessions 
                    WHERE refresh_token = :token AND expires_at > :now
                """),
                {"token": refresh_token, "now": datetime.now(timezone.utc)}
            )
            row = result.fetchone()
            
            if row:
                # Also verify JWT
                payload = decode_token(refresh_token)
                if payload and payload.get("type") == "refresh":
                    return str(row.user_id)
            
        except Exception as e:
            logger.error(f"Error validating refresh token: {e}")
        
        return None
    
    @staticmethod
    async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100):
        """Get all users (admin only)"""
        try:
            result = await db.execute(
                text("""
                    SELECT u.id, u.email, u.name, r.name as role_name, 
                           u.is_active, u.created_at, u.last_login
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    ORDER BY u.created_at DESC
                    OFFSET :skip LIMIT :limit
                """),
                {"skip": skip, "limit": limit}
            )
            rows = result.fetchall()
            
            return [
                UserResponse(
                    id=row.id,
                    email=row.email,
                    name=row.name,
                    role=row.role_name,
                    is_active=row.is_active,
                    created_at=row.created_at,
                    last_login=row.last_login
                )
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    @staticmethod
    async def update_user_role(
        db: AsyncSession,
        user_id: str,
        role_id: int
    ) -> bool:
        """Update user role (admin only)"""
        try:
            await db.execute(
                text("UPDATE users SET role_id = :role_id WHERE id = :id"),
                {"role_id": role_id, "id": user_id}
            )
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            await db.rollback()
            return False
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: str) -> bool:
        """Delete user (admin only)"""
        try:
            await db.execute(
                text("DELETE FROM users WHERE id = :id"),
                {"id": user_id}
            )
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            await db.rollback()
            return False


# Singleton instance
auth_service = AuthService()

