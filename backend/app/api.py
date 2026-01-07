"""
FastAPI REST API endpoints for Agent Orchestrator
"""
import json
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from loguru import logger
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import text

from .models import (
    ChatRequest, ChatResponse, AgentInfo, AgentRegistration, AgentURLRegistration,
    Conversation
)
from .registry import registry
from .orchestrator import orchestrator
from .conversation_service import conversation_service
from .hybrid_router import get_hybrid_router
from .agent_vector_store import get_vector_store
from .auth.dependencies import get_current_user, get_current_admin_user, get_current_user_optional
from .auth.models import UserInDB
from .database import get_db_session
from .mcp_token_service import get_mcp_token_service


# =============================================================================
# Chat Router
# =============================================================================

chat_router = APIRouter(tags=["Chat"])


@chat_router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    """
    Send a message and get a response from the appropriate agent.
    Authenticated users get their conversations saved to DB.
    """
    try:
        # 인증된 사용자는 DB에 대화 저장
        user_id = str(current_user.id) if current_user else None
        # Option C: Pass kauth_user_id for MCPHub token lookup
        kauth_user_id = current_user.kauth_user_id if current_user else None
        logger.info(f"[API] user_id={user_id}, kauth_user_id={kauth_user_id}")  # DEBUG
        response = await orchestrator.process_message(request, user_id, kauth_user_id)
        return response
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/message/stream")
async def send_message_stream(
    request: ChatRequest,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    """
    Send a message and get a streaming response.
    """
    user_id = str(current_user.id) if current_user else None
    # Option C: Pass kauth_user_id for MCPHub token lookup
    kauth_user_id = current_user.kauth_user_id if current_user else None
    
    async def event_generator():
        try:
            async for event in orchestrator.process_message_stream(request, user_id, kauth_user_id):
                yield {
                    "event": event.event,
                    "data": json.dumps(event.data)
                }
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())


@chat_router.get("/conversations", response_model=List[Conversation])
async def list_conversations(
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    """
    List all conversations for the current user.
    """
    if current_user:
        # DB에서 사용자별 대화 목록 조회
        return await conversation_service.list_conversations(str(current_user.id))
    else:
        # 비인증 사용자는 메모리에서 조회 (임시)
        return orchestrator.list_conversations()


@chat_router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    """
    Get a specific conversation by ID.
    """
    if current_user:
        conversation = await conversation_service.get_conversation(
            conversation_id, 
            str(current_user.id)
        )
    else:
        conversation = orchestrator.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@chat_router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    """
    Delete a conversation.
    """
    if current_user:
        deleted = await conversation_service.delete_conversation(
            conversation_id,
            str(current_user.id)
        )
    else:
        deleted = orchestrator.delete_conversation(conversation_id)
    
    if deleted:
        return {"status": "deleted", "conversation_id": conversation_id}
    raise HTTPException(status_code=404, detail="Conversation not found")


@chat_router.post("/test-routing")
async def test_routing(
    request: ChatRequest
):
    """
    Test routing decision for a message (without actually sending to agent).
    Returns the routing decision based on HybridRouter.
    """
    try:
        hybrid_router = get_hybrid_router()
        
        # Get all agent IDs if not specified
        if request.enabled_agent_ids is None:
            agents = registry.list_agents()
            enabled_ids = [a.id for a in agents]
        else:
            enabled_ids = request.enabled_agent_ids
        
        # Get routing decision
        routing = await hybrid_router.route(request.message, enabled_ids)
        
        if routing:
            return {
                "success": True,
                "routing": {
                    "agent_id": routing.agent_id,
                    "agent_name": routing.agent_name,
                    "agent_url": routing.agent_url,
                    "confidence": routing.confidence,
                    "reasoning": routing.reasoning
                }
            }
        else:
            return {
                "success": False,
                "routing": None,
                "message": "No suitable agent found for the given message"
            }
    except Exception as e:
        logger.error(f"Routing test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.get("/vector-search")
async def vector_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, description="Maximum results"),
    domain: Optional[str] = Query(None, description="Domain filter")
):
    """
    Test vector similarity search in agent vector store.
    """
    try:
        vector_store = await get_vector_store()
        results = await vector_store.search_similar(
            query=query,
            limit=limit,
            domain_filter=domain,
            threshold=0.3
        )
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Agent Registry Router
# =============================================================================

agent_router = APIRouter(prefix="/api/agents", tags=["Agents"])


@agent_router.get("", response_model=List[AgentInfo])
async def list_agents(
    include_offline: bool = Query(False, description="Include offline agents")
):
    """
    List all registered agents.
    """
    return registry.list_agents(include_offline=include_offline)


@agent_router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str):
    """
    Get a specific agent by ID.
    """
    agent = registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@agent_router.post("/register", response_model=AgentInfo)
async def register_agent(
    registration: AgentRegistration,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """
    Register a new agent with the orchestrator (Admin only).
    External agents can use this endpoint to register themselves.
    """
    try:
        agent = await registry.register_agent(registration)
        return agent
    except Exception as e:
        logger.error(f"Agent registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@agent_router.post("/register/url", response_model=AgentInfo)
async def register_agent_by_url(
    registration: AgentURLRegistration,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """
    Register an agent by URL using A2A discovery (Admin only).
    Automatically fetches the Agent Card from the provided URL.
    This is the recommended A2A-compliant way to register agents.
    """
    try:
        agent = await registry.register_agent_by_url(registration.url)
        return agent
    except Exception as e:
        logger.error(f"Agent URL registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@agent_router.delete("/{agent_id}")
async def unregister_agent(
    agent_id: str,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """
    Unregister an agent (Admin only).
    """
    if registry.unregister_agent(agent_id):
        return {"status": "unregistered", "agent_id": agent_id}
    raise HTTPException(status_code=404, detail="Agent not found")


@agent_router.post("/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str):
    """
    Agent heartbeat to indicate it's still alive.
    """
    if registry.heartbeat(agent_id):
        return {"status": "ok", "agent_id": agent_id}
    raise HTTPException(status_code=404, detail="Agent not found")


@agent_router.get("/search/query")
async def search_agents(
    q: Optional[str] = Query(None, description="Search query"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    skill: Optional[str] = Query(None, description="Skill name")
):
    """
    Search agents by query, tags, or skill.
    """
    tag_list = tags.split(",") if tags else None
    return registry.search_agents(query=q, tags=tag_list, skill=skill)


@agent_router.get("/monitoring/status")
async def get_monitoring_status(
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """
    Get comprehensive monitoring status for all agents (Admin only).
    Includes health status, metrics, and circuit breaker state.
    """
    return registry.get_monitoring_status()


@agent_router.get("/{agent_id}/metrics")
async def get_agent_metrics(
    agent_id: str,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """
    Get detailed metrics for a specific agent (Admin only).
    """
    metrics = registry.get_metrics(agent_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = registry.get_agent(agent_id)
    return {
        "agent_id": agent_id,
        "agent_name": agent.name if agent else "Unknown",
        "metrics": metrics.to_dict()
    }


@agent_router.post("/{agent_id}/health-check")
async def trigger_health_check(
    agent_id: str,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """
    Manually trigger a health check for a specific agent (Admin only).
    """
    agent = registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    is_healthy = await registry.check_agent_health(agent)
    metrics = registry.get_metrics(agent_id)
    
    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "status": agent.status.value,
        "is_healthy": is_healthy,
        "metrics": metrics.to_dict() if metrics else None
    }


# =============================================================================
# Health & Status Router
# =============================================================================

status_router = APIRouter(tags=["Status"])


@status_router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    agents = registry.list_agents()
    return {
        "status": "healthy",
        "agents_online": len(agents),
        "version": "0.1.0"
    }


@status_router.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": "Agent Orchestrator",
        "version": "0.1.0",
        "description": "A2A Protocol based intelligent agent routing service",
        "endpoints": {
            "chat": "/api/chat/message",
            "chat_stream": "/api/chat/message/stream",
            "agents": "/api/agents",
            "health": "/health"
        }
    }


# =============================================================================
# User Preferences Router
# =============================================================================

user_prefs_router = APIRouter(prefix="/api/user/preferences", tags=["User Preferences"])


class AgentPreferenceUpdate(BaseModel):
    enabled: bool


class AgentPreference(BaseModel):
    agent_id: str
    enabled: bool


@user_prefs_router.get("/agents", response_model=Dict[str, bool])
async def get_agent_preferences(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get user's agent activation preferences.
    Returns a dictionary of agent_id -> enabled status.
    """
    try:
        async with get_db_session() as session:
            result = await session.execute(
                text("""
                    SELECT agent_id, enabled 
                    FROM user_agent_preferences 
                    WHERE user_id = :user_id
                """),
                {"user_id": str(current_user.id)}
            )
            rows = result.fetchall()
            
            # Return as dictionary
            preferences = {row[0]: row[1] for row in rows}
            return preferences
            
    except Exception as e:
        logger.error(f"Failed to get agent preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent preferences")


@user_prefs_router.put("/agents/{agent_id}")
async def update_agent_preference(
    agent_id: str,
    preference: AgentPreferenceUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Update user's preference for a specific agent.
    """
    try:
        async with get_db_session() as session:
            # Upsert preference
            await session.execute(
                text("""
                    INSERT INTO user_agent_preferences (user_id, agent_id, enabled)
                    VALUES (:user_id, :agent_id, :enabled)
                    ON CONFLICT (user_id, agent_id) 
                    DO UPDATE SET enabled = :enabled, updated_at = CURRENT_TIMESTAMP
                """),
                {
                    "user_id": str(current_user.id),
                    "agent_id": agent_id,
                    "enabled": preference.enabled
                }
            )
            await session.commit()
            
            return {"status": "success", "agent_id": agent_id, "enabled": preference.enabled}
            
    except Exception as e:
        logger.error(f"Failed to update agent preference: {e}")
        raise HTTPException(status_code=500, detail="Failed to update agent preference")


@user_prefs_router.post("/agents/bulk")
async def bulk_update_agent_preferences(
    preferences: Dict[str, bool],
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Bulk update user's agent preferences.
    """
    try:
        async with get_db_session() as session:
            for agent_id, enabled in preferences.items():
                await session.execute(
                    text("""
                        INSERT INTO user_agent_preferences (user_id, agent_id, enabled)
                        VALUES (:user_id, :agent_id, :enabled)
                        ON CONFLICT (user_id, agent_id) 
                        DO UPDATE SET enabled = :enabled, updated_at = CURRENT_TIMESTAMP
                    """),
                    {
                        "user_id": str(current_user.id),
                        "agent_id": agent_id,
                        "enabled": enabled
                    }
                )
            await session.commit()
            
            return {"status": "success", "updated_count": len(preferences)}
            
    except Exception as e:
        logger.error(f"Failed to bulk update agent preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update agent preferences")


# =============================================================================
# MCP Token Router (사용자별 MCPHub 토큰 관리)
# =============================================================================

mcp_token_router = APIRouter(prefix="/api/user/mcp-token", tags=["MCP Token"])


class MCPTokenRegister(BaseModel):
    """MCP Token 등록 요청"""
    token: str
    token_name: str = "default"
    expires_in_days: Optional[int] = None  # None이면 무기한


class MCPTokenResponse(BaseModel):
    """MCP Token 응답"""
    id: str
    token_name: str
    is_active: bool
    is_valid: bool
    is_expired: bool = False
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: str
    updated_at: str


@mcp_token_router.post("", response_model=dict)
async def register_mcp_token(
    request: MCPTokenRegister,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    MCPHub 토큰을 등록합니다.
    토큰은 암호화되어 저장됩니다.
    """
    try:
        from datetime import datetime, timedelta, timezone
        
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)
        
        async with get_db_session() as session:
            service = get_mcp_token_service()
            result = await service.save_token(
                db=session,
                user_id=current_user.id,
                token=request.token,
                token_name=request.token_name,
                expires_at=expires_at
            )
            return {"status": "success", "token_info": result}
            
    except Exception as e:
        logger.error(f"Failed to register MCP token: {e}")
        raise HTTPException(status_code=500, detail="Failed to register MCP token")


@mcp_token_router.get("/status")
async def get_mcp_token_status(
    token_name: str = Query("default", description="Token name"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    MCP 토큰 상태를 확인합니다.
    """
    try:
        async with get_db_session() as session:
            service = get_mcp_token_service()
            status = await service.get_token_status(
                db=session,
                user_id=current_user.id,
                token_name=token_name
            )
            
            if not status:
                return {
                    "has_token": False,
                    "message": "No MCP token registered"
                }
            
            return {
                "has_token": True,
                "token_info": status
            }
            
    except Exception as e:
        logger.error(f"Failed to get MCP token status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get MCP token status")


@mcp_token_router.get("/list")
async def list_mcp_tokens(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    사용자의 모든 MCP 토큰 목록을 조회합니다.
    """
    try:
        async with get_db_session() as session:
            service = get_mcp_token_service()
            tokens = await service.list_user_tokens(
                db=session,
                user_id=current_user.id
            )
            return {"tokens": tokens, "count": len(tokens)}
            
    except Exception as e:
        logger.error(f"Failed to list MCP tokens: {e}")
        raise HTTPException(status_code=500, detail="Failed to list MCP tokens")


@mcp_token_router.delete("")
async def delete_mcp_token(
    token_name: str = Query("default", description="Token name to delete"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    MCP 토큰을 삭제합니다.
    """
    try:
        async with get_db_session() as session:
            service = get_mcp_token_service()
            deleted = await service.delete_token(
                db=session,
                user_id=current_user.id,
                token_name=token_name
            )
            
            if deleted:
                return {"status": "success", "message": "Token deleted"}
            else:
                raise HTTPException(status_code=404, detail="Token not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete MCP token: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete MCP token")


@mcp_token_router.post("/deactivate")
async def deactivate_mcp_token(
    token_name: str = Query("default", description="Token name to deactivate"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    MCP 토큰을 비활성화합니다 (삭제하지 않고).
    """
    try:
        async with get_db_session() as session:
            service = get_mcp_token_service()
            deactivated = await service.deactivate_token(
                db=session,
                user_id=current_user.id,
                token_name=token_name
            )
            
            if deactivated:
                return {"status": "success", "message": "Token deactivated"}
            else:
                raise HTTPException(status_code=404, detail="Token not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate MCP token: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate MCP token")

