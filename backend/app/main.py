"""
Agent Orchestrator - Main FastAPI Application
A2A Protocol based intelligent agent routing service
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from .config import get_settings
from .api import chat_router, agent_router, status_router, user_prefs_router, mcp_token_router
from .auth.router import auth_router, users_router
from .auth.kauth import kauth_router
from .auth.webhook import webhook_router
from .registry import registry
from .database import init_db, close_db


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=get_settings().log_level
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Manages startup and shutdown events.
    """
    # Startup
    logger.info("Starting Agent Orchestrator...")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database connection established")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}. Running without persistence.")
    
    await registry.start()
    logger.info("Agent Orchestrator started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agent Orchestrator...")
    await registry.stop()
    await close_db()
    logger.info("Agent Orchestrator shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Agent Orchestrator",
    description="""
    ## A2A Protocol Based Agent Orchestration Service
    
    This service provides intelligent routing of user requests to appropriate AI agents
    using Google's Agent-to-Agent (A2A) protocol.
    
    ### Features
    - **Intelligent Routing**: Uses LLM to analyze user intent and route to appropriate agents
    - **Agent Registry**: Central registry for agent discovery and management
    - **A2A Protocol**: Full support for A2A protocol communication
    - **Streaming**: Real-time streaming responses via Server-Sent Events
    - **Conversation Management**: Persistent conversation state management
    
    ### Quick Start
    1. Register your agents using the `/api/agents/register` endpoint
    2. Send messages via `/api/chat/message` or `/api/chat/message/stream`
    3. The orchestrator will automatically route to the best agent
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS (환경변수 CORS_ORIGINS로 설정 가능)
settings = get_settings()
cors_origins = settings.cors_origins_list
logger.info(f"CORS allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(status_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(chat_router, prefix="/api/chat")  # Chat endpoints
app.include_router(agent_router)
app.include_router(user_prefs_router)  # User preferences endpoints
app.include_router(mcp_token_router)  # MCP Token management endpoints
app.include_router(kauth_router)  # K-Auth OAuth endpoints
app.include_router(webhook_router)  # K-Auth Webhook receiver


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

