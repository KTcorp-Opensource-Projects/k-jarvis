"""
Data models for Agent Orchestrator
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AgentStatus(str, Enum):
    """Agent health status"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


class TaskState(str, Enum):
    """A2A Task states"""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


# =============================================================================
# Agent Models
# =============================================================================

class AgentSkill(BaseModel):
    """Agent skill definition - A2A Spec compliant"""
    id: str = ""  # Skill identifier
    name: str
    description: str
    tags: List[str] = []
    examples: List[str] = []
    inputModes: List[str] = ["text/plain"]
    outputModes: List[str] = ["text/plain"]


class AgentRequirements(BaseModel):
    """Agent requirements - MCPHub 토큰 등 필요 사항"""
    mcpHubToken: bool = False  # MCPHub 토큰 필요 여부
    mcpServers: List[str] = []  # 필요한 MCP 서버 목록


class AgentInfo(BaseModel):
    """Agent information model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    skills: List[AgentSkill] = []
    capabilities: Dict[str, Any] = {}
    requirements: AgentRequirements = Field(default_factory=AgentRequirements)
    status: AgentStatus = AgentStatus.OFFLINE
    last_seen: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class AgentRegistration(BaseModel):
    """Model for agent registration request"""
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    skills: List[AgentSkill] = []
    capabilities: Dict[str, Any] = {}


class AgentURLRegistration(BaseModel):
    """Model for URL-based agent registration (A2A discovery)"""
    url: str  # Base URL of the A2A agent server


class AgentRoutingInfo(BaseModel):
    """Agent routing metadata for intelligent routing"""
    domain: str = "general"  # 도메인: project_management, documentation, communication 등
    category: str = ""  # 카테고리: jira, confluence, slack 등
    keywords: List[str] = []  # 라우팅 키워드 (한/영)
    capabilities: List[str] = []  # 지원 기능: search, create, update 등


class AgentCard(BaseModel):
    """A2A Agent Card - describes agent capabilities"""
    protocolVersion: str = "0.3.0"
    name: str
    description: str
    url: Optional[str] = None  # Optional: LangGraph 에이전트는 url 대신 endpoints 사용
    version: str = "1.0.0"
    skills: List[AgentSkill] = []
    capabilities: Dict[str, Any] = {
        "streaming": True,
        "pushNotifications": False,
        "stateTransitionHistory": False
    }
    requirements: AgentRequirements = Field(default_factory=AgentRequirements)  # MCPHub 토큰 등 요구사항
    routing: Optional[AgentRoutingInfo] = None  # 라우팅 메타데이터
    defaultInputModes: List[str] = ["text/plain"]
    defaultOutputModes: List[str] = ["text/plain"]
    # LangGraph 에이전트 지원
    protocol: Optional[str] = None
    endpoints: Optional[Dict[str, str]] = None
    contact: Optional[Dict[str, str]] = None
    # 라우팅 메타데이터 (A2A 확장)
    routing: Optional[AgentRoutingInfo] = None
    provider: Optional[Dict[str, str]] = None
    preferredTransport: Optional[str] = None


# =============================================================================
# Chat Models
# =============================================================================

class ChatMessage(BaseModel):
    """Chat message model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}
    
    class Config:
        use_enum_values = True


class Conversation(BaseModel):
    """Conversation session"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Chat"
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    conversation_id: Optional[str] = None
    enabled_agent_ids: Optional[List[str]] = None  # 사용자가 활성화한 에이전트 ID 목록


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    content: str
    agent_used: Optional[str] = None
    task_state: TaskState = TaskState.COMPLETED
    artifacts: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    
    class Config:
        use_enum_values = True


# =============================================================================
# Intent Analysis Models
# =============================================================================

class Intent(BaseModel):
    """Analyzed intent from user message"""
    category: str  # weather, search, travel, general, etc.
    confidence: float
    entities: Dict[str, Any] = {}
    suggested_agent: Optional[str] = None


class RoutingDecision(BaseModel):
    """Agent routing decision"""
    agent_id: str
    agent_name: str
    agent_url: str
    confidence: float
    reasoning: str


# =============================================================================
# Stream Models
# =============================================================================

class StreamEvent(BaseModel):
    """Server-Sent Event model"""
    event: str = "message"
    data: Dict[str, Any]
    id: Optional[str] = None

