"""
K-Auth OAuth 2.1 Integration for K-Jarvis Orchestrator
PKCE (Proof Key for Code Exchange) 지원 - RFC 7636
"""
import os
import json
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
import httpx
import redis.asyncio as redis
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..database import get_db_session
from .service import create_access_token, get_password_hash


# ==================== PKCE Helper Functions ====================

def generate_pkce_pair() -> tuple[str, str]:
    """
    PKCE code_verifier 및 code_challenge 생성
    
    Returns:
        tuple: (code_verifier, code_challenge)
    """
    # code_verifier: 43-128자의 랜덤 문자열 (RFC 7636)
    code_verifier = secrets.token_urlsafe(43)
    
    # code_challenge: SHA-256 해시 후 Base64URL 인코딩
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    
    return code_verifier, code_challenge

# K-Auth Configuration
# ⚠️ SECURITY: 프로덕션에서는 반드시 환경변수로 설정하세요
# KAUTH_URL: Backend-to-Backend 통신용 (Docker 내부)
# KAUTH_PUBLIC_URL: 브라우저 리다이렉트용 (외부 접근)
KAUTH_URL = os.getenv("KAUTH_URL", "http://localhost:4002")
KAUTH_PUBLIC_URL = os.getenv("KAUTH_PUBLIC_URL", "http://localhost:4002")
# 개발환경 기본값 (프로덕션에서는 환경변수 필수)
_DEFAULT_CLIENT_ID = "kauth_QXYNxQOYcpdny_2tkjONjA"  # Dev only
_DEFAULT_CLIENT_SECRET = "1DkIkrW2o4NppSSh8IIjXVAVhKVXyVbCQeUorjVyUqc"  # Dev only
KAUTH_CLIENT_ID = os.getenv("KAUTH_CLIENT_ID", _DEFAULT_CLIENT_ID)
KAUTH_CLIENT_SECRET = os.getenv("KAUTH_CLIENT_SECRET", _DEFAULT_CLIENT_SECRET)
KAUTH_CALLBACK_URL = os.getenv("KAUTH_CALLBACK_URL", "http://localhost:4001/auth/kauth/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4000")

# 보안 경고 (개발환경 기본값 사용 시)
if KAUTH_CLIENT_ID == _DEFAULT_CLIENT_ID:
    logger.warning("⚠️ Using default KAUTH_CLIENT_ID - set environment variable for production!")
if KAUTH_CLIENT_SECRET == _DEFAULT_CLIENT_SECRET:
    logger.warning("⚠️ Using default KAUTH_CLIENT_SECRET - set environment variable for production!")

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Redis client (production-ready state storage)
_redis_client: Optional[redis.Redis] = None

async def get_redis_client() -> redis.Redis:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        logger.info(f"[Redis] Connected to {REDIS_URL}")
    return _redis_client

# Fallback in-memory state storage (for development without Redis)
oauth_states_fallback: dict = {}

kauth_router = APIRouter(prefix="/auth/kauth", tags=["K-Auth OAuth"])


@kauth_router.get("")
async def kauth_login():
    """
    Start K-Auth OAuth 2.1 flow with PKCE.
    Redirects to K-Auth authorize endpoint with code_challenge.
    """
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Generate PKCE pair
    code_verifier, code_challenge = generate_pkce_pair()
    
    state_data = {
        "created_at": datetime.utcnow().isoformat(),
        "code_verifier": code_verifier  # PKCE: 콜백에서 사용할 code_verifier 저장
    }
    
    try:
        redis_client = await get_redis_client()
        # Store state with 10 minute TTL
        await redis_client.setex(
            f"oauth_state:{state}",
            600,  # 10 minutes
            json.dumps(state_data)
        )
        logger.debug(f"[Redis] Stored OAuth state with PKCE code_verifier")
    except Exception as e:
        # Fallback to in-memory if Redis fails
        logger.warning(f"[Redis] Failed to store state, using fallback: {e}")
        state_data["expires_at"] = datetime.utcnow() + timedelta(minutes=10)
        oauth_states_fallback[state] = state_data
    
    # Build authorize URL with PKCE (브라우저 리다이렉트용으로 PUBLIC_URL 사용)
    authorize_url = (
        f"{KAUTH_PUBLIC_URL}/oauth/authorize"
        f"?response_type=code"
        f"&client_id={KAUTH_CLIENT_ID}"
        f"&redirect_uri={KAUTH_CALLBACK_URL}"
        f"&scope=openid%20profile%20email"
        f"&state={state}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    
    logger.info(f"[K-Auth] Redirecting to K-Auth authorize (with PKCE): {authorize_url[:100]}...")
    return RedirectResponse(url=authorize_url, status_code=302)


@kauth_router.get("/callback")
async def kauth_callback(
    code: str = Query(...),
    state: str = Query(...)
):
    """
    Handle K-Auth OAuth 2.1 callback with PKCE.
    Exchange code for tokens (with code_verifier) and create/update user.
    """
    # Verify state and retrieve code_verifier (Redis-based with fallback)
    state_valid = False
    code_verifier = None
    state_data_parsed = None
    
    try:
        redis_client = await get_redis_client()
        state_data = await redis_client.get(f"oauth_state:{state}")
        
        if state_data:
            # Delete state after retrieval (one-time use)
            await redis_client.delete(f"oauth_state:{state}")
            state_data_parsed = json.loads(state_data)
            code_verifier = state_data_parsed.get("code_verifier")
            state_valid = True
            logger.debug("[Redis] Retrieved and deleted OAuth state (with PKCE)")
    except Exception as e:
        logger.warning(f"[Redis] Failed to get state, checking fallback: {e}")
        # Fallback to in-memory
        state_data_parsed = oauth_states_fallback.pop(state, None)
        if state_data_parsed:
            # Check expiration for fallback
            if "expires_at" in state_data_parsed and datetime.utcnow() < state_data_parsed["expires_at"]:
                state_valid = True
                code_verifier = state_data_parsed.get("code_verifier")
            elif "expires_at" not in state_data_parsed:
                # Redis fallback data format
                state_valid = True
                code_verifier = state_data_parsed.get("code_verifier")
    
    if not state_valid:
        logger.warning("[K-Auth] Invalid or expired state")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=invalid_state",
            status_code=302
        )
    
    try:
        # Exchange code for tokens (with PKCE code_verifier)
        token_request_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": KAUTH_CALLBACK_URL,
            "client_id": KAUTH_CLIENT_ID,
            "client_secret": KAUTH_CLIENT_SECRET
        }
        
        # PKCE: code_verifier 추가
        if code_verifier:
            token_request_data["code_verifier"] = code_verifier
            logger.debug("[PKCE] Including code_verifier in token request")
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                f"{KAUTH_URL}/oauth/token",
                data=token_request_data
            )
            
            if token_response.status_code != 200:
                logger.error(f"[K-Auth] Token exchange failed: {token_response.text}")
                return RedirectResponse(
                    url=f"{FRONTEND_URL}/login?error=token_exchange_failed",
                    status_code=302
                )
            
            tokens = token_response.json()
            access_token = tokens["access_token"]
            
            # Get user info from K-Auth
            userinfo_response = await client.get(
                f"{KAUTH_URL}/oauth/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if userinfo_response.status_code != 200:
                logger.error(f"[K-Auth] UserInfo failed: {userinfo_response.text}")
                return RedirectResponse(
                    url=f"{FRONTEND_URL}/login?error=userinfo_failed",
                    status_code=302
                )
            
            kauth_user = userinfo_response.json()
            kauth_refresh_token = tokens.get("refresh_token")
            logger.info(f"[K-Auth] Got user info: {kauth_user.get('username')}")
        
        # Find or create user in Orchestrator DB and save K-Auth refresh token
        async with get_db_session() as db:
            user = await find_or_create_user(db, kauth_user)
            
            # Save K-Auth refresh token for later use
            if kauth_refresh_token:
                await save_kauth_refresh_token(db, user["id"], kauth_refresh_token)
        
        # Generate Orchestrator JWT token with kauth_user_id for Option C
        orchestrator_token = create_access_token(
            data={
                "sub": user["username"],
                "user_id": str(user["id"]),
                "is_admin": user["is_admin"],
                "kauth_user_id": user["kauth_user_id"]  # For MCPHub token lookup
            }
        )
        
        logger.info(f"[K-Auth] User logged in: {user['username']}")
        
        # Redirect to frontend with token (include refresh token for frontend storage)
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/callback?token={orchestrator_token}",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"[K-Auth] Callback error: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=callback_failed",
            status_code=302
        )


async def find_or_create_user(db: AsyncSession, kauth_user: dict) -> dict:
    """
    Find existing user by kauth_user_id or email, or create new user.
    Updates user info from K-Auth on each login.
    Returns a dict with user info for token creation.
    """
    kauth_user_id = kauth_user["sub"]
    email = kauth_user["email"]
    username = kauth_user["username"]
    full_name = kauth_user.get("name", username)
    is_admin = kauth_user.get("is_admin", False)
    
    # Try to find by kauth_user_id first
    result = await db.execute(
        text("SELECT * FROM users WHERE kauth_user_id = :kauth_id"),
        {"kauth_id": kauth_user_id}
    )
    user_row = result.fetchone()
    
    if user_row:
        # Update user info from K-Auth
        role_id = 1 if is_admin else 2
        await db.execute(
            text("""
                UPDATE users 
                SET email = :email, name = :name, role_id = :role_id, updated_at = NOW()
                WHERE kauth_user_id = :kauth_id
            """),
            {"email": email, "name": full_name, "role_id": role_id, "kauth_id": kauth_user_id}
        )
        await db.commit()
        
        return {
            "id": user_row.id,
            "username": user_row.username,
            "email": email,
            "is_admin": is_admin,
            "name": full_name,
            "kauth_user_id": kauth_user_id  # Add for MCPHub token lookup
        }
    
    # Try to find by email (for existing local accounts)
    result = await db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": email}
    )
    user_row = result.fetchone()
    
    if user_row:
        # Link existing account to K-Auth
        role_id = 1 if is_admin else 2
        await db.execute(
            text("""
                UPDATE users 
                SET kauth_user_id = :kauth_id, auth_provider = 'kauth', role_id = :role_id, updated_at = NOW()
                WHERE email = :email
            """),
            {"kauth_id": kauth_user_id, "role_id": role_id, "email": email}
        )
        await db.commit()
        
        return {
            "id": user_row.id,
            "username": user_row.username,
            "email": user_row.email,
            "is_admin": is_admin,
            "name": user_row.name,
            "kauth_user_id": kauth_user_id  # Add for MCPHub token lookup
        }
    
    # Try to find by username (for existing local accounts with different email)
    result = await db.execute(
        text("SELECT * FROM users WHERE username = :username"),
        {"username": username}
    )
    user_row = result.fetchone()
    
    if user_row:
        # Link existing account to K-Auth and update email
        role_id = 1 if is_admin else 2
        await db.execute(
            text("""
                UPDATE users 
                SET kauth_user_id = :kauth_id, auth_provider = 'kauth', 
                    email = :email, role_id = :role_id, updated_at = NOW()
                WHERE username = :username
            """),
            {"kauth_id": kauth_user_id, "email": email, "role_id": role_id, "username": username}
        )
        await db.commit()
        
        return {
            "id": user_row.id,
            "username": user_row.username,
            "email": email,
            "is_admin": is_admin,
            "name": user_row.name,
            "kauth_user_id": kauth_user_id  # Add for MCPHub token lookup
        }
    
    # Create new user
    import uuid
    new_user_id = uuid.uuid4()
    
    # Get role_id (1 for admin, 2 for user)
    role_id = 1 if is_admin else 2
    
    await db.execute(
        text("""
            INSERT INTO users (id, username, email, password_hash, name, role_id, is_active, kauth_user_id, auth_provider, created_at, updated_at)
            VALUES (:id, :username, :email, :password, :name, :role_id, true, :kauth_id, 'kauth', NOW(), NOW())
        """),
        {
            "id": new_user_id,
            "username": username,
            "email": email,
            "password": get_password_hash(secrets.token_urlsafe(32)),  # Random password for K-Auth users
            "name": full_name,
            "role_id": role_id,
            "kauth_id": kauth_user_id
        }
    )
    await db.commit()
    
    logger.info(f"[K-Auth] Created new user: {username} ({email})")
    
    return {
        "id": new_user_id,
        "username": username,
        "email": email,
        "is_admin": is_admin,
        "name": full_name,
        "kauth_user_id": kauth_user_id  # Add for MCPHub token lookup
    }


async def save_kauth_refresh_token(db: AsyncSession, user_id, refresh_token: str):
    """
    Save K-Auth refresh token for user.
    Upsert: update if exists, insert if not.
    """
    # K-Auth default refresh token TTL is 7 days
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    # Try to update existing token
    result = await db.execute(
        text("SELECT id FROM kauth_refresh_tokens WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    existing = result.fetchone()
    
    if existing:
        await db.execute(
            text("""
                UPDATE kauth_refresh_tokens 
                SET refresh_token = :token, expires_at = :expires_at, updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {"token": refresh_token, "expires_at": expires_at, "user_id": user_id}
        )
    else:
        await db.execute(
            text("""
                INSERT INTO kauth_refresh_tokens (user_id, refresh_token, expires_at)
                VALUES (:user_id, :token, :expires_at)
            """),
            {"user_id": user_id, "token": refresh_token, "expires_at": expires_at}
        )
    
    await db.commit()
    logger.debug(f"[K-Auth] Saved refresh token for user {user_id}")


async def get_kauth_refresh_token(db: AsyncSession, user_id) -> Optional[str]:
    """Get K-Auth refresh token for user."""
    result = await db.execute(
        text("""
            SELECT refresh_token FROM kauth_refresh_tokens 
            WHERE user_id = :user_id AND expires_at > NOW()
        """),
        {"user_id": user_id}
    )
    row = result.fetchone()
    return row.refresh_token if row else None


@kauth_router.post("/refresh")
async def kauth_refresh_token(request: Request):
    """
    Refresh Orchestrator access token using K-Auth refresh token.
    Requires Authorization header with current (potentially expired) token.
    """
    from .service import decode_token
    
    # Get current token from header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization token")
    
    current_token = auth_header.split(" ")[1]
    
    # Decode token (allow expired tokens for refresh)
    try:
        from jose import jwt, ExpiredSignatureError
        payload = jwt.decode(
            current_token,
            options={"verify_exp": False}  # Allow expired tokens
        )
        user_id = payload.get("user_id")
    except Exception as e:
        logger.error(f"[K-Auth] Token decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: no user_id")
    
    try:
        async with get_db_session() as db:
            # Get stored K-Auth refresh token
            kauth_refresh = await get_kauth_refresh_token(db, user_id)
            
            if not kauth_refresh:
                logger.warning(f"[K-Auth] No refresh token found for user {user_id}")
                raise HTTPException(status_code=401, detail="No refresh token available. Please login again.")
            
            # Exchange refresh token for new access token with K-Auth
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    f"{KAUTH_URL}/oauth/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": kauth_refresh,
                        "client_id": KAUTH_CLIENT_ID,
                        "client_secret": KAUTH_CLIENT_SECRET
                    }
                )
                
                if token_response.status_code != 200:
                    logger.error(f"[K-Auth] Refresh failed: {token_response.text}")
                    # Clear invalid refresh token
                    await db.execute(
                        text("DELETE FROM kauth_refresh_tokens WHERE user_id = :user_id"),
                        {"user_id": user_id}
                    )
                    await db.commit()
                    raise HTTPException(status_code=401, detail="Refresh token expired. Please login again.")
                
                tokens = token_response.json()
                new_access_token = tokens["access_token"]
                new_refresh_token = tokens.get("refresh_token")
                
                # Get updated user info
                userinfo_response = await client.get(
                    f"{KAUTH_URL}/oauth/userinfo",
                    headers={"Authorization": f"Bearer {new_access_token}"}
                )
                
                if userinfo_response.status_code != 200:
                    raise HTTPException(status_code=500, detail="Failed to get user info")
                
                kauth_user = userinfo_response.json()
            
            # Update refresh token if a new one was issued
            if new_refresh_token:
                await save_kauth_refresh_token(db, user_id, new_refresh_token)
            
            # Generate new Orchestrator JWT token
            orchestrator_token = create_access_token(
                data={
                    "sub": kauth_user["username"],
                    "user_id": user_id,
                    "is_admin": kauth_user.get("is_admin", False)
                }
            )
            
            logger.info(f"[K-Auth] Token refreshed for user {kauth_user['username']}")
            
            return {
                "access_token": orchestrator_token,
                "token_type": "Bearer"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[K-Auth] Refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

