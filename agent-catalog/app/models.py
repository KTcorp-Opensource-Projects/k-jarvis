"""
Agent Catalog Service - Models
A2A Protocol compliant Agent models
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class AgentStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class AgentSkill(BaseModel):
    """Agent skill definition - A2A Spec compliant"""
    id: str = ""
    name: str
    description: str
    tags: List[str] = []
    examples: List[str] = []
    inputModes: List[str] = ["text/plain"]
    outputModes: List[str] = ["text/plain"]


class AgentRequirements(BaseModel):
    """Agent requirements - MCPHub 토큰 등 필요 사항"""
    mcpHubToken: bool = False
    mcpServers: List[str] = []


class AgentRoutingInfo(BaseModel):
    """Agent routing metadata for intelligent routing"""
    domain: str = "general"
    category: str = ""
    keywords: List[str] = []
    capabilities: List[str] = []


class AgentCard(BaseModel):
    """A2A Agent Card - describes agent capabilities"""
    protocolVersion: str = "0.3.0"
    name: str
    description: str
    url: Optional[str] = None
    version: str = "1.0.0"
    skills: List[AgentSkill] = []
    capabilities: Dict[str, Any] = {
        "streaming": True,
        "pushNotifications": False,
        "stateTransitionHistory": False
    }
    requirements: AgentRequirements = Field(default_factory=AgentRequirements)
    routing: Optional[AgentRoutingInfo] = None
    defaultInputModes: List[str] = ["text/plain"]
    defaultOutputModes: List[str] = ["text/plain"]


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
    routing: Optional[AgentRoutingInfo] = None
    status: AgentStatus = AgentStatus.UNKNOWN
    last_seen: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
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
    url: str

