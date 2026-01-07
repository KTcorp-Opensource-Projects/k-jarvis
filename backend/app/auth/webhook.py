"""
K-Auth Webhook Receiver for K-Jarvis Orchestrator
Handles user events from K-Auth (deletion, role changes, etc.)
"""
import os
import json
import hmac
import hashlib
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header
from loguru import logger
from sqlalchemy import text

from ..database import get_db_session

# Webhook secret (must match the one registered in K-Auth)
WEBHOOK_SECRET = os.getenv("KAUTH_WEBHOOK_SECRET", "k-auth-webhook-secret-key")

webhook_router = APIRouter(prefix="/api/webhook/kauth", tags=["K-Auth Webhook"])


def verify_signature(payload: str, signature: str) -> bool:
    """Verify HMAC-SHA256 signature"""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@webhook_router.post("")
async def receive_webhook(
    request: Request,
    x_kauth_event: Optional[str] = Header(None),
    x_kauth_signature: Optional[str] = Header(None),
    x_kauth_timestamp: Optional[str] = Header(None)
):
    """
    Receive webhook events from K-Auth.
    
    Events handled:
    - user.deleted: Remove user's local data
    - user.role_changed: Update user's role
    - user.disabled: Revoke user's sessions
    """
    # Read raw body for signature verification
    body = await request.body()
    payload_str = body.decode()
    
    # Verify signature
    if not x_kauth_signature:
        logger.warning("[Webhook] Missing signature header")
        raise HTTPException(status_code=401, detail="Missing signature")
    
    if not verify_signature(payload_str, x_kauth_signature):
        logger.warning("[Webhook] Invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse payload
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event_type = payload.get("event_type") or x_kauth_event
    user_id = payload.get("user_id")
    data = payload.get("data", {})
    
    logger.info(f"[Webhook] Received event: {event_type} for user {user_id}")
    
    # Handle events
    try:
        if event_type == "user.deleted":
            await handle_user_deleted(user_id, data)
        elif event_type == "user.role_changed":
            await handle_role_changed(user_id, data)
        elif event_type == "user.disabled":
            await handle_user_disabled(user_id, data)
        elif event_type == "user.enabled":
            await handle_user_enabled(user_id, data)
        else:
            logger.debug(f"[Webhook] Unhandled event type: {event_type}")
        
        return {"status": "success", "event": event_type}
        
    except Exception as e:
        logger.error(f"[Webhook] Error handling event {event_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Event handling failed: {str(e)}")


async def handle_user_deleted(user_id: str, data: dict):
    """
    Handle user deletion from K-Auth.
    - Remove user's conversations
    - Remove user's preferences
    - Remove user's MCP tokens
    - Optionally keep user record as inactive
    """
    username = data.get("username", "unknown")
    logger.info(f"[Webhook] Processing user deletion: {username} ({user_id})")
    
    async with get_db_session() as db:
        # Check if user exists by kauth_user_id
        result = await db.execute(
            text("SELECT id FROM users WHERE kauth_user_id = :kauth_id"),
            {"kauth_id": user_id}
        )
        local_user = result.fetchone()
        
        if not local_user:
            logger.warning(f"[Webhook] User not found for kauth_id: {user_id}")
            return
        
        local_user_id = local_user.id
        
        # Option 1: Hard delete - remove all user data
        # Uncomment if you want to completely remove the user
        # await db.execute(
        #     text("DELETE FROM users WHERE id = :id"),
        #     {"id": local_user_id}
        # )
        
        # Option 2: Soft delete - mark as inactive and clear sensitive data
        await db.execute(
            text("""
                UPDATE users 
                SET is_active = false, 
                    kauth_user_id = NULL,
                    auth_provider = 'deleted',
                    updated_at = NOW()
                WHERE id = :id
            """),
            {"id": local_user_id}
        )
        
        # Remove K-Auth refresh token
        await db.execute(
            text("DELETE FROM kauth_refresh_tokens WHERE user_id = :user_id"),
            {"user_id": local_user_id}
        )
        
        # Remove MCP tokens
        await db.execute(
            text("DELETE FROM user_mcp_tokens WHERE user_id = :user_id"),
            {"user_id": local_user_id}
        )
        
        await db.commit()
        logger.info(f"[Webhook] User {username} deleted successfully")


async def handle_role_changed(user_id: str, data: dict):
    """
    Handle role change from K-Auth.
    Update user's role in local database.
    """
    username = data.get("username", "unknown")
    new_role = data.get("new_role")
    
    logger.info(f"[Webhook] Processing role change for {username}: {new_role}")
    
    async with get_db_session() as db:
        # Determine role_id based on new_role
        is_admin = new_role == "admin"
        role_id = 1 if is_admin else 2
        
        await db.execute(
            text("""
                UPDATE users 
                SET role_id = :role_id, updated_at = NOW()
                WHERE kauth_user_id = :kauth_id
            """),
            {"role_id": role_id, "kauth_id": user_id}
        )
        
        await db.commit()
        logger.info(f"[Webhook] Role updated for {username}: {new_role}")


async def handle_user_disabled(user_id: str, data: dict):
    """
    Handle user account disable from K-Auth.
    Revoke all sessions and mark as inactive.
    """
    username = data.get("username", "unknown")
    logger.info(f"[Webhook] Processing user disable: {username}")
    
    async with get_db_session() as db:
        # Get local user ID
        result = await db.execute(
            text("SELECT id FROM users WHERE kauth_user_id = :kauth_id"),
            {"kauth_id": user_id}
        )
        local_user = result.fetchone()
        
        if not local_user:
            return
        
        local_user_id = local_user.id
        
        # Mark user as inactive
        await db.execute(
            text("UPDATE users SET is_active = false, updated_at = NOW() WHERE id = :id"),
            {"id": local_user_id}
        )
        
        # Revoke all sessions
        await db.execute(
            text("DELETE FROM user_sessions WHERE user_id = :user_id"),
            {"user_id": local_user_id}
        )
        
        # Revoke K-Auth refresh token
        await db.execute(
            text("DELETE FROM kauth_refresh_tokens WHERE user_id = :user_id"),
            {"user_id": local_user_id}
        )
        
        await db.commit()
        logger.info(f"[Webhook] User {username} disabled and sessions revoked")


async def handle_user_enabled(user_id: str, data: dict):
    """
    Handle user account enable from K-Auth.
    Mark user as active.
    """
    username = data.get("username", "unknown")
    logger.info(f"[Webhook] Processing user enable: {username}")
    
    async with get_db_session() as db:
        await db.execute(
            text("UPDATE users SET is_active = true, updated_at = NOW() WHERE kauth_user_id = :kauth_id"),
            {"kauth_id": user_id}
        )
        await db.commit()
        logger.info(f"[Webhook] User {username} enabled")



