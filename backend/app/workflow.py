"""
Agent Chaining / Multi-Agent Workflow (Phase 3 - Handoff Pattern)

Enables sequential execution of multiple agents where output of one agent
becomes input to the next agent.

Phase 1 Features:
- LLM-based dynamic workflow analysis (no more pattern matching)
- N-step workflow support (removed 2-step limitation)
- Enhanced error logging
- Retry policy support

Phase 2 Features:
- Supervisor LLM for step validation and dynamic routing
- Error recovery mechanisms (retry, fallback, user confirmation)
- Structured context passing (AgentContext)
- Artifact management between steps

Phase 3 Features:
- Handoff Tool for dynamic agent-to-agent delegation
- LLM-based handoff detection in agent responses
- Automatic workflow extension based on handoff requests
- Cross-agent context preservation during handoffs
"""
import json
import uuid
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from loguru import logger

from .llm_client import get_llm_client, BaseLLMClient


# =============================================================================
# Phase 2: Enums and Status
# =============================================================================

class WorkflowStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_RETRY = "needs_retry"
    NEEDS_FALLBACK = "needs_fallback"
    AWAITING_USER = "awaiting_user"


class ErrorRecoveryStrategy(str, Enum):
    """Strategy for handling step failures"""
    RETRY = "retry"              # Retry the same step
    FALLBACK = "fallback"        # Use fallback agent
    SKIP = "skip"                # Skip this step and continue
    ASK_USER = "ask_user"        # Ask user for guidance
    ABORT = "abort"              # Abort entire workflow
    MODIFY_AND_RETRY = "modify"  # LLM modifies the task and retries


class ArtifactType(str, Enum):
    """Types of artifacts that can be passed between agents"""
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    CODE = "code"
    DOCUMENT = "document"
    IMAGE = "image"
    TABLE = "table"
    URL = "url"


class HandoffReason(str, Enum):
    """Reasons for agent-to-agent handoff"""
    OUT_OF_SCOPE = "out_of_scope"       # Request is outside agent's capabilities
    SPECIALIZED = "specialized"          # Another agent is better suited
    FOLLOW_UP = "follow_up"             # Follow-up action needed by another agent
    DEPENDENCY = "dependency"            # Depends on another agent's output
    USER_REQUEST = "user_request"        # User explicitly requested another agent


# =============================================================================
# Phase 3: Handoff Data Classes
# =============================================================================

@dataclass
class HandoffRequest:
    """
    Request from an agent to hand off control to another agent.
    Agents can include this in their response to delegate tasks.
    """
    target_agent_name: str              # Name of agent to hand off to
    task_description: str               # What the target agent should do
    reason: HandoffReason = HandoffReason.SPECIALIZED
    reason_detail: str = ""             # Detailed explanation
    context_data: Dict[str, Any] = field(default_factory=dict)  # Data to pass
    priority: int = 0                   # Higher = more urgent
    preserve_conversation: bool = True  # Keep conversation context


@dataclass
class HandoffResult:
    """Result of a handoff operation"""
    success: bool
    source_agent: str
    target_agent: str
    task_description: str
    result_content: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Phase 2: Structured Context
# =============================================================================

@dataclass
class Artifact:
    """Structured artifact passed between workflow steps"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: ArtifactType = ArtifactType.TEXT
    name: str = ""
    content: str = ""
    mime_type: str = "text/plain"
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "mime_type": self.mime_type,
            "url": self.url,
            "metadata": self.metadata
        }


@dataclass
class AgentContext:
    """
    Structured context passed between agents in a workflow.
    This enables rich, typed communication between agents.
    """
    task_description: str = ""                    # What the agent should do
    original_user_request: str = ""               # The original user request
    previous_results: List[Dict[str, Any]] = field(default_factory=list)  # Results from previous steps
    artifacts: List[Artifact] = field(default_factory=list)               # Artifacts from previous steps
    constraints: List[str] = field(default_factory=list)                  # Constraints to follow
    expected_output_format: Optional[str] = None  # Expected output format (json, yaml, text, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)                # Additional metadata
    workflow_id: Optional[str] = None             # Parent workflow ID
    step_index: int = 0                           # Current step index
    
    def add_artifact(self, artifact: Artifact):
        self.artifacts.append(artifact)
    
    def add_previous_result(self, step_name: str, content: str, success: bool = True):
        self.previous_results.append({
            "step": step_name,
            "content": content,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_summary(self) -> str:
        """Generate a summary for LLM consumption"""
        summary_parts = [f"Task: {self.task_description}"]
        
        if self.previous_results:
            summary_parts.append(f"\nPrevious Results ({len(self.previous_results)}):")
            for i, result in enumerate(self.previous_results[-3:], 1):  # Last 3 results
                summary_parts.append(f"  {i}. [{result['step']}]: {result['content'][:200]}...")
        
        if self.artifacts:
            summary_parts.append(f"\nArtifacts ({len(self.artifacts)}):")
            for artifact in self.artifacts[-3:]:  # Last 3 artifacts
                summary_parts.append(f"  - {artifact.name} ({artifact.type.value})")
        
        if self.constraints:
            summary_parts.append(f"\nConstraints: {', '.join(self.constraints)}")
        
        return "\n".join(summary_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_description": self.task_description,
            "original_request": self.original_user_request,
            "previous_results": self.previous_results,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "constraints": self.constraints,
            "expected_output": self.expected_output_format,
            "metadata": self.metadata
        }


@dataclass
class RetryPolicy:
    """Retry policy for workflow steps"""
    max_retries: int = 3
    backoff_seconds: float = 1.0
    retry_on_errors: List[str] = field(default_factory=lambda: ["timeout", "connection", "rate_limit"])
    fallback_agent_id: Optional[str] = None  # Agent to use if all retries fail
    allow_skip: bool = False  # Whether step can be skipped on failure


@dataclass
class WorkflowStep:
    """Single step in a workflow - Enhanced with Phase 2 features"""
    agent_id: str
    agent_name: str
    action: str  # What this agent should do
    input_prompt: str  # The prompt to send to this agent
    task_description: str = ""  # Detailed task description from LLM
    use_previous_output: bool = False  # Whether to include previous step's output
    output_type: Optional[str] = None  # Expected output type (yaml, json, text, etc.)
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    output: Optional[str] = None
    artifacts: List[Artifact] = field(default_factory=list)  # Phase 2: Typed artifacts
    error: Optional[str] = None
    retry_count: int = 0
    
    # Phase 2: Enhanced fields
    context: Optional[AgentContext] = None  # Structured context for this step
    validation_result: Optional[Dict[str, Any]] = None  # Supervisor validation result
    recovery_strategy: Optional[ErrorRecoveryStrategy] = None  # Strategy if failed
    fallback_agent_id: Optional[str] = None  # Fallback agent if this fails
    is_critical: bool = True  # If False, workflow can continue even if step fails
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def mark_started(self):
        self.started_at = datetime.now().isoformat()
        self.status = WorkflowStepStatus.RUNNING
    
    def mark_completed(self, output: str):
        self.completed_at = datetime.now().isoformat()
        self.status = WorkflowStepStatus.COMPLETED
        self.output = output
    
    def mark_failed(self, error: str):
        self.completed_at = datetime.now().isoformat()
        self.status = WorkflowStepStatus.FAILED
        self.error = error


@dataclass
class SupervisorDecision:
    """Decision made by the Supervisor LLM"""
    action: str  # "continue", "retry", "fallback", "skip", "abort", "modify"
    reasoning: str
    modified_task: Optional[str] = None  # If action is "modify", this is the new task
    fallback_agent_id: Optional[str] = None  # If action is "fallback"
    user_message: Optional[str] = None  # If action requires user input
    confidence: float = 0.0


@dataclass
class Workflow:
    """Multi-agent workflow definition - Enhanced with Phase 2 features"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    current_step_index: int = 0
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    final_output: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_policy: Optional[RetryPolicy] = None
    max_iterations: int = 10  # Safety limit to prevent infinite loops
    reasoning: str = ""  # LLM's reasoning for the workflow
    
    # Phase 2: Enhanced fields
    context: Optional[AgentContext] = None  # Global workflow context
    supervisor_enabled: bool = True  # Whether to use Supervisor LLM
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    total_tokens_used: int = 0
    
    def get_completed_steps(self) -> List[WorkflowStep]:
        return [s for s in self.steps if s.status == WorkflowStepStatus.COMPLETED]
    
    def get_failed_steps(self) -> List[WorkflowStep]:
        return [s for s in self.steps if s.status == WorkflowStepStatus.FAILED]
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None


# =============================================================================
# Phase 3: Handoff Detection
# =============================================================================

class HandoffDetector:
    """
    Detects handoff requests in agent responses using LLM analysis.
    
    Agents can signal handoff requests by:
    1. Explicit JSON format: {"handoff": {"target": "Agent Name", "task": "..."}}
    2. Natural language: "This should be handled by [Agent Name]"
    3. Structured markers in response
    """
    
    # Keywords that may indicate handoff intent
    HANDOFF_KEYWORDS = [
        "should be handled by",
        "better suited for",
        "recommend using",
        "delegate to",
        "hand off to",
        "transfer to",
        "this requires",
        "need to use",
        "다른 에이전트",
        "에게 위임",
        "처리해야",
    ]
    
    def __init__(self):
        self.llm_client: Optional[BaseLLMClient] = get_llm_client()
        self._use_llm = self.llm_client is not None and self.llm_client.is_available()
        
        if self._use_llm:
            logger.info("[HANDOFF] LLM-based handoff detector initialized")
        else:
            logger.info("[HANDOFF] Pattern-based handoff detector initialized (no LLM)")
    
    async def detect(
        self,
        agent_response: str,
        available_agents: List[Dict],
        current_agent_name: str
    ) -> Optional[HandoffRequest]:
        """
        Detect if an agent response contains a handoff request.
        
        Args:
            agent_response: The response from the current agent
            available_agents: List of available agents
            current_agent_name: Name of the agent that produced the response
            
        Returns:
            HandoffRequest if handoff detected, None otherwise
        """
        # First, try to detect explicit JSON handoff format
        explicit = self._detect_explicit_handoff(agent_response)
        if explicit:
            return explicit
        
        # Check for keyword patterns
        if not self._has_handoff_keywords(agent_response):
            return None
        
        # Use LLM for sophisticated detection
        if self._use_llm:
            return await self._llm_detect_handoff(
                agent_response,
                available_agents,
                current_agent_name
            )
        
        # Fallback to pattern detection
        return self._pattern_detect_handoff(
            agent_response,
            available_agents,
            current_agent_name
        )
    
    def _detect_explicit_handoff(self, response: str) -> Optional[HandoffRequest]:
        """Detect explicit JSON handoff format in response"""
        try:
            # Look for JSON block in response
            import re
            json_pattern = r'\{[^{}]*"handoff"[^{}]*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            for match in matches:
                try:
                    data = json.loads(match)
                    if "handoff" in data:
                        handoff = data["handoff"]
                        return HandoffRequest(
                            target_agent_name=handoff.get("target", ""),
                            task_description=handoff.get("task", handoff.get("description", "")),
                            reason=HandoffReason(handoff.get("reason", "specialized")),
                            reason_detail=handoff.get("reason_detail", ""),
                            context_data=handoff.get("context", {})
                        )
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.debug(f"[HANDOFF] Explicit detection error: {e}")
        
        return None
    
    def _has_handoff_keywords(self, response: str) -> bool:
        """Check if response contains handoff-related keywords"""
        response_lower = response.lower()
        return any(kw in response_lower for kw in self.HANDOFF_KEYWORDS)
    
    async def _llm_detect_handoff(
        self,
        response: str,
        available_agents: List[Dict],
        current_agent: str
    ) -> Optional[HandoffRequest]:
        """Use LLM to detect handoff intent"""
        
        agents_info = "\n".join([
            f"- {a.get('name')}: {a.get('description', '')[:100]}"
            for a in available_agents
            if a.get('name') != current_agent
        ])
        
        prompt = f"""Analyze if this agent response suggests handing off to another agent.

Current Agent: {current_agent}

Agent Response:
```
{response[:1500]}
```

Available Agents:
{agents_info}

If the response suggests another agent should handle something, respond with JSON:
{{
    "has_handoff": true,
    "target_agent": "Agent Name",
    "task": "What should be done",
    "reason": "out_of_scope|specialized|follow_up|dependency",
    "confidence": 0.0-1.0
}}

If no handoff is needed:
{{
    "has_handoff": false,
    "reason": "Why no handoff is needed"
}}
"""
        
        try:
            result = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(result)
            
            if data.get("has_handoff") and data.get("confidence", 0) > 0.6:
                logger.info(f"[HANDOFF] LLM detected handoff to {data.get('target_agent')}")
                return HandoffRequest(
                    target_agent_name=data.get("target_agent", ""),
                    task_description=data.get("task", ""),
                    reason=HandoffReason(data.get("reason", "specialized")),
                    reason_detail=f"Confidence: {data.get('confidence', 0):.0%}"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"[HANDOFF] LLM detection error: {e}")
            return None
    
    def _pattern_detect_handoff(
        self,
        response: str,
        available_agents: List[Dict],
        current_agent: str
    ) -> Optional[HandoffRequest]:
        """Pattern-based handoff detection (fallback)"""
        
        response_lower = response.lower()
        
        for agent in available_agents:
            agent_name = agent.get('name', '')
            if agent_name == current_agent:
                continue
            
            # Check if agent name is mentioned with handoff keywords
            if agent_name.lower() in response_lower:
                for keyword in self.HANDOFF_KEYWORDS:
                    if keyword in response_lower:
                        logger.info(f"[HANDOFF] Pattern detected handoff to {agent_name}")
                        return HandoffRequest(
                            target_agent_name=agent_name,
                            task_description=f"Continue task based on: {response[:200]}",
                            reason=HandoffReason.SPECIALIZED,
                            reason_detail=f"Keyword match: {keyword}"
                        )
        
        return None


# Global handoff detector instance
handoff_detector = HandoffDetector()


# =============================================================================
# Phase 3: Long-term Memory Management
# =============================================================================

@dataclass
class MemoryEntry:
    """Single memory entry for long-term storage"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "conversation"  # conversation, workflow, artifact, fact
    content: str = ""
    summary: str = ""  # LLM-generated summary for quick retrieval
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None  # For vector search (optional)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    accessed_at: Optional[str] = None
    relevance_score: float = 0.0  # For search ranking
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content[:500],
            "summary": self.summary,
            "tags": self.tags,
            "created_at": self.created_at
        }


class MemoryStore:
    """
    Abstract memory store interface.
    Supports both in-memory and vector DB backends.
    
    This enables agents to:
    1. Store conversation history and context
    2. Remember past workflow executions
    3. Learn from previous interactions
    4. Provide relevant context to future requests
    """
    
    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self._entries: Dict[str, MemoryEntry] = {}
        self._index_by_type: Dict[str, List[str]] = {}
        self._index_by_tag: Dict[str, List[str]] = {}
        self.llm_client: Optional[BaseLLMClient] = get_llm_client()
        
        logger.info(f"[MEMORY] Memory store initialized (max: {max_entries})")
    
    async def store(
        self,
        content: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        generate_summary: bool = True
    ) -> MemoryEntry:
        """
        Store a new memory entry.
        
        Args:
            content: The content to store
            memory_type: Type of memory (conversation, workflow, artifact, fact)
            metadata: Additional metadata
            tags: Tags for categorization
            generate_summary: Whether to generate LLM summary
            
        Returns:
            The created MemoryEntry
        """
        # Generate summary if LLM available
        summary = ""
        if generate_summary and self.llm_client and self.llm_client.is_available():
            summary = await self._generate_summary(content)
        
        entry = MemoryEntry(
            type=memory_type,
            content=content,
            summary=summary or content[:200],
            metadata=metadata or {},
            tags=tags or []
        )
        
        # Store entry
        self._entries[entry.id] = entry
        
        # Update indices
        if memory_type not in self._index_by_type:
            self._index_by_type[memory_type] = []
        self._index_by_type[memory_type].append(entry.id)
        
        for tag in (tags or []):
            if tag not in self._index_by_tag:
                self._index_by_tag[tag] = []
            self._index_by_tag[tag].append(entry.id)
        
        # Enforce max entries (LRU-style)
        if len(self._entries) > self.max_entries:
            await self._evict_oldest()
        
        logger.debug(f"[MEMORY] Stored entry {entry.id[:8]}... (type: {memory_type})")
        return entry
    
    async def retrieve(
        self,
        query: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[MemoryEntry]:
        """
        Retrieve relevant memories based on query.
        
        Args:
            query: Search query
            memory_type: Filter by type
            tags: Filter by tags
            limit: Maximum results
            
        Returns:
            List of relevant MemoryEntry objects
        """
        candidates = []
        
        # Filter by type if specified
        if memory_type and memory_type in self._index_by_type:
            candidate_ids = self._index_by_type[memory_type]
        else:
            candidate_ids = list(self._entries.keys())
        
        # Filter by tags if specified
        if tags:
            tag_ids = set()
            for tag in tags:
                if tag in self._index_by_tag:
                    tag_ids.update(self._index_by_tag[tag])
            candidate_ids = [cid for cid in candidate_ids if cid in tag_ids]
        
        # Score candidates
        query_lower = query.lower()
        for cid in candidate_ids:
            entry = self._entries.get(cid)
            if not entry:
                continue
            
            # Simple relevance scoring
            score = 0.0
            content_lower = entry.content.lower()
            summary_lower = entry.summary.lower()
            
            # Exact match boost
            if query_lower in content_lower:
                score += 0.5
            if query_lower in summary_lower:
                score += 0.3
            
            # Word match
            query_words = query_lower.split()
            for word in query_words:
                if word in content_lower:
                    score += 0.1
                if word in summary_lower:
                    score += 0.05
            
            # Recency boost (newer = higher)
            try:
                created = datetime.fromisoformat(entry.created_at)
                age_hours = (datetime.now() - created).total_seconds() / 3600
                recency_score = max(0, 1 - (age_hours / 168))  # Decay over 1 week
                score += recency_score * 0.2
            except (ValueError, TypeError) as e:
                logger.debug(f"[MEMORY] Failed to parse created_at: {e}")
            
            entry.relevance_score = score
            if score > 0:
                candidates.append(entry)
        
        # Sort by relevance and return top results
        candidates.sort(key=lambda e: e.relevance_score, reverse=True)
        
        results = candidates[:limit]
        
        # Update access time
        for entry in results:
            entry.accessed_at = datetime.now().isoformat()
        
        logger.debug(f"[MEMORY] Retrieved {len(results)} entries for query: {query[:50]}")
        return results
    
    async def store_workflow_result(self, workflow: 'Workflow') -> MemoryEntry:
        """Store a completed workflow for future reference"""
        
        # Build content from workflow
        content_parts = [
            f"Workflow: {workflow.name}",
            f"Description: {workflow.description}",
            f"Status: {workflow.status.value}",
            f"Steps: {len(workflow.steps)}"
        ]
        
        for i, step in enumerate(workflow.steps):
            content_parts.append(f"  Step {i+1}: {step.agent_name} - {step.action}")
            if step.output:
                content_parts.append(f"    Output: {step.output[:200]}...")
        
        content = "\n".join(content_parts)
        
        # Extract tags
        tags = ["workflow", workflow.name]
        for step in workflow.steps:
            tags.append(step.agent_name.lower().replace(" ", "_"))
        
        return await self.store(
            content=content,
            memory_type="workflow",
            metadata={
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "status": workflow.status.value,
                "steps_count": len(workflow.steps)
            },
            tags=list(set(tags))
        )
    
    async def get_relevant_context(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        limit: int = 3
    ) -> str:
        """
        Get relevant context from memory for a user message.
        Returns formatted context string for LLM consumption.
        """
        memories = await self.retrieve(
            query=user_message,
            limit=limit
        )
        
        if not memories:
            return ""
        
        context_parts = ["## Relevant Context from Memory:"]
        for i, mem in enumerate(memories):
            context_parts.append(f"\n### Memory {i+1} ({mem.type}):")
            context_parts.append(mem.summary or mem.content[:300])
        
        return "\n".join(context_parts)
    
    async def _generate_summary(self, content: str) -> str:
        """Generate a brief summary using LLM"""
        if not self.llm_client or not self.llm_client.is_available():
            return content[:200]
        
        try:
            result = await self.llm_client.chat_completion(
                messages=[{
                    "role": "user",
                    "content": f"Summarize in 1-2 sentences:\n{content[:1000]}"
                }]
            )
            return result[:200]
        except Exception as e:
            logger.debug(f"[MEMORY] Summary generation failed: {e}")
            return content[:200]
    
    async def _evict_oldest(self):
        """Remove oldest entries when max is reached"""
        if len(self._entries) <= self.max_entries:
            return
        
        # Sort by created_at and remove oldest
        sorted_entries = sorted(
            self._entries.items(),
            key=lambda x: x[1].created_at
        )
        
        to_remove = len(self._entries) - self.max_entries
        for entry_id, _ in sorted_entries[:to_remove]:
            del self._entries[entry_id]
            # Clean up indices
            for type_list in self._index_by_type.values():
                if entry_id in type_list:
                    type_list.remove(entry_id)
            for tag_list in self._index_by_tag.values():
                if entry_id in tag_list:
                    tag_list.remove(entry_id)
        
        logger.debug(f"[MEMORY] Evicted {to_remove} old entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics"""
        return {
            "total_entries": len(self._entries),
            "max_entries": self.max_entries,
            "by_type": {k: len(v) for k, v in self._index_by_type.items()},
            "unique_tags": len(self._index_by_tag)
        }


# Global memory store instance
memory_store = MemoryStore(max_entries=1000)


# =============================================================================
# Phase 2: Supervisor LLM
# =============================================================================

class SupervisorLLM:
    """
    Supervisor LLM that validates step results and decides next actions.
    
    This implements the LangGraph Supervisor pattern where a central LLM
    coordinates the workflow execution, validates results, and handles errors.
    """
    
    def __init__(self):
        self.llm_client: Optional[BaseLLMClient] = get_llm_client()
        self._available = self.llm_client is not None and self.llm_client.is_available()
        
        if self._available:
            logger.info("[SUPERVISOR] Supervisor LLM initialized")
        else:
            logger.warning("[WARN] Supervisor LLM not available (no LLM client)")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    async def validate_step_result(
        self,
        step: WorkflowStep,
        workflow: 'Workflow',
        available_agents: List[Dict]
    ) -> SupervisorDecision:
        """
        Validate the result of a completed step and decide next action.
        
        Args:
            step: The completed step to validate
            workflow: The parent workflow
            available_agents: List of available agents for potential fallback
            
        Returns:
            SupervisorDecision with action and reasoning
        """
        if not self._available:
            # Default to continue if supervisor not available
            return SupervisorDecision(
                action="continue",
                reasoning="Supervisor LLM not available, auto-continuing",
                confidence=0.5
            )
        
        # Format agents for fallback options
        agent_names = [a.get('name', '') for a in available_agents]
        
        prompt = f"""당신은 멀티에이전트 워크플로우의 Supervisor입니다. 방금 완료된 스텝의 결과를 검증하고 다음 액션을 결정하세요.

## 워크플로우 정보
- 이름: {workflow.name}
- 설명: {workflow.description}
- 전체 스텝: {len(workflow.steps)}개
- 현재 스텝: {workflow.current_step_index + 1}번째

## 완료된 스텝
- 에이전트: {step.agent_name}
- 작업: {step.action}
- 상태: {step.status.value}
- 에러: {step.error or "없음"}

## 스텝 결과 (처음 1000자):
```
{step.output[:1000] if step.output else "(출력 없음)"}
```

## 사용 가능한 에이전트 (fallback 옵션):
{', '.join(agent_names)}

## 다음 스텝 정보:
{self._format_next_step(workflow)}

## 결정 기준 (중요: continue를 우선 선택하세요!):
1. **continue**: 스텝이 어느 정도 성공적으로 완료됨 -> 다음 스텝으로 진행 (권장)
2. **retry**: 명백한 네트워크/타임아웃 오류인 경우에만
3. **modify**: 완전히 잘못된 작업을 수행한 경우에만 (거의 사용하지 않음)
4. **fallback**: 에이전트가 완전히 실패하고 다른 에이전트가 더 적합한 경우에만
5. **skip**: 비필수 스텝이고 실패해도 워크플로우 진행 가능한 경우
6. **abort**: 복구 불가능한 치명적 오류만

**주의**: 결과가 비어있지 않고 관련 정보를 포함하면 "continue"를 선택하세요.
에이전트가 안내 메시지를 반환해도 작업을 수행한 것으로 간주하고 "continue"하세요.

## 응답 형식 (JSON):
{{
    "action": "continue|retry|modify|fallback|skip|abort",
    "reasoning": "결정 이유",
    "confidence": 0.0-1.0,
    "modified_task": "action이 modify인 경우 수정된 작업 지시",
    "fallback_agent": "action이 fallback인 경우 대체 에이전트 이름",
    "user_message": "사용자에게 전달할 메시지 (선택적)"
}}
"""
        
        try:
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            decision = SupervisorDecision(
                action=result.get("action", "continue"),
                reasoning=result.get("reasoning", "No reasoning provided"),
                confidence=result.get("confidence", 0.5),
                modified_task=result.get("modified_task"),
                fallback_agent_id=self._find_agent_id(result.get("fallback_agent"), available_agents),
                user_message=result.get("user_message")
            )
            
            logger.info(f"[SUPERVISOR] Supervisor decision: {decision.action} (confidence: {decision.confidence:.2f})")
            logger.debug(f"   Reasoning: {decision.reasoning}")
            
            return decision
            
        except Exception as e:
            logger.error(f"Supervisor validation error: {e}")
            # Default to continue on error
            return SupervisorDecision(
                action="continue",
                reasoning=f"Supervisor error: {e}, defaulting to continue",
                confidence=0.3
            )
    
    async def decide_error_recovery(
        self,
        step: WorkflowStep,
        error: str,
        workflow: 'Workflow',
        available_agents: List[Dict]
    ) -> SupervisorDecision:
        """
        Decide how to recover from a step failure.
        
        Args:
            step: The failed step
            error: The error message
            workflow: The parent workflow
            available_agents: Available agents for fallback
            
        Returns:
            SupervisorDecision with recovery action
        """
        if not self._available:
            # Default recovery based on retry count
            if step.retry_count < 2:
                return SupervisorDecision(
                    action="retry",
                    reasoning="Supervisor unavailable, attempting retry",
                    confidence=0.4
                )
            elif not step.is_critical:
                return SupervisorDecision(
                    action="skip",
                    reasoning="Supervisor unavailable, skipping non-critical step",
                    confidence=0.4
                )
            else:
                return SupervisorDecision(
                    action="abort",
                    reasoning="Supervisor unavailable, aborting after max retries",
                    confidence=0.4
                )
        
        # Format available agents
        agents_info = "\n".join([
            f"- {a.get('name')}: {a.get('description', '')[:100]}"
            for a in available_agents
        ])
        
        prompt = f"""당신은 멀티에이전트 워크플로우의 Supervisor입니다. 스텝 실행 중 오류가 발생했습니다. 복구 전략을 결정하세요.

## 실패한 스텝
- 에이전트: {step.agent_name}
- 작업: {step.action}
- 재시도 횟수: {step.retry_count}
- 필수 스텝 여부: {'예' if step.is_critical else '아니오'}

## 오류 내용:
```
{error}
```

## 사용 가능한 대체 에이전트:
{agents_info}

## 복구 전략 옵션:
1. **retry**: 일시적 오류로 보임, 재시도 (최대 3회)
2. **modify**: 작업 지시를 수정하여 재시도 (예: 파라미터 변경)
3. **fallback**: 다른 에이전트로 대체 시도
4. **skip**: 비필수 스텝이므로 건너뛰기
5. **abort**: 복구 불가, 워크플로우 중단

## 응답 형식 (JSON):
{{
    "action": "retry|modify|fallback|skip|abort",
    "reasoning": "결정 이유",
    "confidence": 0.0-1.0,
    "modified_task": "action이 modify인 경우 수정된 작업",
    "fallback_agent": "action이 fallback인 경우 대체 에이전트",
    "user_message": "사용자에게 전달할 복구 상태 메시지"
}}
"""
        
        try:
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            decision = SupervisorDecision(
                action=result.get("action", "abort"),
                reasoning=result.get("reasoning", "Error recovery decision"),
                confidence=result.get("confidence", 0.5),
                modified_task=result.get("modified_task"),
                fallback_agent_id=self._find_agent_id(result.get("fallback_agent"), available_agents),
                user_message=result.get("user_message")
            )
            
            logger.info(f"[RECOVERY] Supervisor recovery decision: {decision.action}")
            logger.debug(f"   Reasoning: {decision.reasoning}")
            
            return decision
            
        except Exception as e:
            logger.error(f"Supervisor recovery error: {e}")
            return SupervisorDecision(
                action="abort",
                reasoning=f"Supervisor error during recovery: {e}",
                confidence=0.2
            )
    
    def _format_next_step(self, workflow: 'Workflow') -> str:
        """Format information about the next step"""
        next_idx = workflow.current_step_index + 1
        if next_idx < len(workflow.steps):
            next_step = workflow.steps[next_idx]
            return f"다음 스텝: {next_step.agent_name} - {next_step.action}"
        return "다음 스텝: 없음 (마지막 스텝)"
    
    def _find_agent_id(self, agent_name: Optional[str], agents: List[Dict]) -> Optional[str]:
        """Find agent ID by name"""
        if not agent_name:
            return None
        
        agent_name_lower = agent_name.lower()
        for agent in agents:
            if agent.get('name', '').lower() == agent_name_lower:
                return agent.get('id')
            # Partial match
            if agent_name_lower in agent.get('name', '').lower():
                return agent.get('id')
        
        return None


# Global supervisor instance
supervisor_llm = SupervisorLLM()


class LLMWorkflowAnalyzer:
    """
    LLM-based workflow analyzer that dynamically determines
    if a request requires multiple agents and what the workflow should be.
    
    This replaces pattern-based matching with intelligent LLM analysis.
    """
    
    def __init__(self):
        self.llm_client: Optional[BaseLLMClient] = get_llm_client()
        self._use_llm = self.llm_client is not None and self.llm_client.is_available()
        
        if self._use_llm:
            logger.info("[LLM] LLM-based workflow analyzer initialized")
        else:
            logger.warning("[WARN] LLM not available, falling back to pattern-based analysis")
    
    def _format_agents_for_llm(self, agents: List[Dict]) -> str:
        """Format agent information for LLM prompt"""
        if not agents:
            return "사용 가능한 에이전트가 없습니다."
        
        lines = []
        for agent in agents:
            name = agent.get('name', 'Unknown')
            desc = agent.get('description', 'No description')
            agent_id = agent.get('id', '')
            
            skills = agent.get('skills', [])
            skill_names = [s.get('name', '') for s in skills if s.get('name')]
            skill_str = ', '.join(skill_names) if skill_names else 'None'
            
            lines.append(f"- **{name}** (ID: {agent_id})")
            lines.append(f"  설명: {desc}")
            lines.append(f"  스킬: {skill_str}")
            lines.append("")
        
        return "\n".join(lines)
    
    async def analyze(
        self, 
        user_message: str, 
        available_agents: List[Dict],
        previous_response: Optional[str] = None
    ) -> Optional['Workflow']:
        """
        Analyze user message using LLM to detect multi-agent workflows.
        
        Args:
            user_message: The user's request
            available_agents: List of available agent information
            previous_response: Optional previous assistant response for chaining
            
        Returns:
            Workflow object if multi-agent workflow detected, None otherwise
        """
        if not self._use_llm:
            logger.debug("LLM not available, skipping LLM analysis")
            return None
        
        if not available_agents:
            logger.debug("No agents available, skipping workflow analysis")
            return None
        
        agents_info = self._format_agents_for_llm(available_agents)
        
        # Build context about previous response if available
        previous_context = ""
        if previous_response:
            # Truncate if too long
            truncated = previous_response[:1000] + "..." if len(previous_response) > 1000 else previous_response
            previous_context = f"""
이전 대화에서 Assistant의 마지막 응답:
```
{truncated}
```
사용자가 "이 결과를", "이거", "방금 결과" 등을 언급하면 위 내용을 참조하는 것입니다.
"""
        
        prompt = f"""당신은 멀티 에이전트 워크플로우 분석기입니다. 사용자 요청을 분석하여 여러 에이전트가 순차적으로 협력해야 하는지 판단하세요.

## 사용 가능한 에이전트:
{agents_info}

{previous_context}

## 사용자 요청:
"{user_message}"

## 분석 지침:
1. 요청이 단일 에이전트로 처리 가능하면 is_multi_step: false
2. 여러 에이전트가 순차적으로 협력해야 하면 is_multi_step: true
3. "이 결과를 저장해줘", "이걸 문서로 만들어줘" 등은 이전 응답을 사용한 체이닝입니다
4. "검색하고 정리해줘", "만들고 저장해줘" 등은 멀티스텝 워크플로우입니다

## 응답 형식 (JSON):
{{
    "is_multi_step": true/false,
    "steps": [
        {{
            "agent_name": "에이전트 이름 (정확히 매칭)",
            "agent_id": "에이전트 ID",
            "action": "수행할 작업 (간단히)",
            "task_description": "에이전트에게 전달할 상세 지시사항",
            "use_previous_output": true/false,
            "output_type": "text/json/yaml/document 등"
        }}
    ],
    "workflow_name": "워크플로우 이름 (예: search_and_save)",
    "workflow_description": "워크플로우 설명",
    "reasoning": "이 워크플로우를 선택한 이유"
}}

단일 에이전트로 충분한 경우:
{{
    "is_multi_step": false,
    "steps": [],
    "reasoning": "단일 에이전트로 처리 가능한 이유"
}}
"""
        
        try:
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            logger.debug(f"LLM workflow analysis result: {result}")
            
            if not result.get("is_multi_step", False):
                logger.info(f"[ANALYZE] Single-agent request detected: {result.get('reasoning', 'N/A')}")
                return None
            
            # Build workflow from LLM response
            workflow = self._build_workflow_from_llm(result, available_agents, previous_response)
            
            if workflow and len(workflow.steps) > 0:
                logger.info(f"[WORKFLOW] LLM detected multi-agent workflow: {workflow.name} ({len(workflow.steps)} steps)")
                logger.info(f"   Reasoning: {workflow.reasoning}")
                return workflow
            
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM workflow analysis error: {e}")
            return None
    
    def _build_workflow_from_llm(
        self,
        llm_result: Dict,
        available_agents: List[Dict],
        previous_response: Optional[str]
    ) -> Optional[Workflow]:
        """Build a Workflow object from LLM analysis result"""
        
        steps_data = llm_result.get("steps", [])
        if not steps_data:
            return None
        
        # Create agent lookup maps
        agent_by_name = {a.get('name', '').lower(): a for a in available_agents}
        agent_by_id = {a.get('id', ''): a for a in available_agents}
        
        workflow_steps = []
        
        for i, step_data in enumerate(steps_data):
            agent_name = step_data.get("agent_name", "")
            agent_id = step_data.get("agent_id", "")
            
            # Try to find agent by ID first, then by name
            agent = agent_by_id.get(agent_id) or agent_by_name.get(agent_name.lower())
            
            if not agent:
                # Try partial match on name
                for name_key, agent_obj in agent_by_name.items():
                    if agent_name.lower() in name_key or name_key in agent_name.lower():
                        agent = agent_obj
                        break
            
            if not agent:
                logger.warning(f"Agent not found: {agent_name} (ID: {agent_id})")
                continue
            
            # Build task description
            task_desc = step_data.get("task_description", step_data.get("action", ""))
            use_previous = step_data.get("use_previous_output", False)
            
            # If first step uses previous and we have previous_response, inject it
            if i == 0 and use_previous and previous_response:
                task_desc = f"""다음 내용을 처리해주세요:

```
{previous_response}
```

작업: {task_desc}"""
                use_previous = False  # Already included in prompt
            
            step = WorkflowStep(
                agent_id=agent.get("id", ""),
                agent_name=agent.get("name", "Unknown Agent"),
                action=step_data.get("action", "process"),
                input_prompt=task_desc,
                task_description=task_desc,
                use_previous_output=use_previous if i > 0 else False,
                output_type=step_data.get("output_type", "text")
            )
            workflow_steps.append(step)
        
        if not workflow_steps:
            return None
        
        return Workflow(
            name=llm_result.get("workflow_name", "dynamic_workflow"),
            description=llm_result.get("workflow_description", "LLM generated workflow"),
            steps=workflow_steps,
            reasoning=llm_result.get("reasoning", ""),
            retry_policy=RetryPolicy()  # Default retry policy
        )


class PatternBasedWorkflowAnalyzer:
    """
    Legacy pattern-based workflow analyzer.
    Used as fallback when LLM is not available.
    """
    
    # Patterns for chaining with previous response
    CHAIN_PATTERNS = [
        {
            "triggers": ["이 결과", "이걸", "이거", "위 내용", "방금 결과", "저장해줘", "문서로 만들어줘"],
            "target_keywords": ["confluence", "컨플루언스", "문서", "저장"],
            "chain_type": "save_previous_to_confluence"
        },
        {
            "triggers": ["이 결과", "이걸", "이거", "위 내용", "방금"],
            "target_keywords": ["요약", "정리", "분석"],
            "chain_type": "analyze_previous"
        }
    ]
    
    # Workflow patterns
    WORKFLOW_PATTERNS = [
        {
            "triggers": ["만들고", "생성하고", "작성하고"],
            "second_actions": ["저장", "문서로", "confluence", "컨플루언스"],
            "workflow_type": "create_and_save",
            "description": "콘텐츠 생성 후 문서 저장"
        },
        {
            "triggers": ["검색하고", "찾고", "조회하고"],
            "second_actions": ["정리", "요약", "문서로", "저장"],
            "workflow_type": "search_and_document",
            "description": "검색 후 결과 문서화"
        },
        {
            "triggers": ["분석하고", "확인하고"],
            "second_actions": ["보고서", "리포트", "문서"],
            "workflow_type": "analyze_and_report",
            "description": "분석 후 보고서 생성"
        }
    ]
    
    def analyze(
        self, 
        user_message: str, 
        available_agents: List[Dict],
        previous_response: Optional[str] = None
    ) -> Optional[Workflow]:
        """Pattern-based analysis (legacy)"""
        message_lower = user_message.lower()
        
        # Check for workflow patterns
        for pattern in self.WORKFLOW_PATTERNS:
            has_trigger = any(t in message_lower for t in pattern["triggers"])
            has_second = any(s in message_lower for s in pattern["second_actions"])
            
            if has_trigger and has_second:
                logger.info(f"[PATTERN] Pattern detected: {pattern['workflow_type']}")
                return self._build_workflow(user_message, pattern, available_agents)
        
        # Check for chaining with previous response
        if previous_response:
            for pattern in self.CHAIN_PATTERNS:
                has_trigger = any(t in message_lower for t in pattern["triggers"])
                has_target = any(t in message_lower for t in pattern["target_keywords"])
                
                if has_trigger and has_target:
                    logger.info(f"[PATTERN] Chain pattern detected: {pattern['chain_type']}")
                    return self._build_chain_workflow(
                        user_message, previous_response, pattern, available_agents
                    )
        
        return None
    
    def _find_agent_by_keywords(self, agents: List[Dict], keywords: List[str]) -> Optional[Dict]:
        """Find an agent that matches given keywords"""
        for agent in agents:
            agent_text = f"{agent.get('name', '')} {agent.get('description', '')}".lower()
            skills = agent.get('skills', [])
            skill_text = " ".join([
                f"{s.get('name', '')} {s.get('description', '')} {' '.join(s.get('tags', []))}"
                for s in skills
            ]).lower()
            
            full_text = f"{agent_text} {skill_text}"
            
            if any(kw in full_text for kw in keywords):
                return agent
        
        return None
    
    def _build_chain_workflow(
        self,
        user_message: str,
        previous_response: str,
        pattern: Dict,
        available_agents: List[Dict]
    ) -> Optional[Workflow]:
        """Build a workflow that uses previous response as input"""
        
        workflow = Workflow(
            name=pattern["chain_type"],
            description=f"이전 응답을 사용한 체이닝: {pattern['chain_type']}",
            reasoning="Pattern-based chain detection"
        )
        
        if pattern["chain_type"] == "save_previous_to_confluence":
            confluence_agent = self._find_agent_by_keywords(
                available_agents,
                ["confluence", "문서", "document", "wiki"]
            )
            
            if confluence_agent:
                workflow.steps = [
                    WorkflowStep(
                        agent_id=confluence_agent.get("id", ""),
                        agent_name=confluence_agent.get("name", "Confluence Agent"),
                        action="save_document",
                        input_prompt=f"""다음 내용을 Confluence 문서로 저장해주세요:

```
{previous_response}
```

문서 제목과 형식은 내용에 맞게 자동으로 결정해주세요.""",
                        task_description="이전 응답을 Confluence 문서로 저장",
                        use_previous_output=False
                    )
                ]
                return workflow
        
        return None
    
    def _build_workflow(
        self, 
        user_message: str, 
        pattern: Dict, 
        available_agents: List[Dict]
    ) -> Optional[Workflow]:
        """Build a workflow based on detected pattern"""
        
        workflow = Workflow(
            name=pattern["workflow_type"],
            description=pattern["description"],
            reasoning="Pattern-based workflow detection"
        )
        
        if pattern["workflow_type"] == "create_and_save":
            content_agent = self._find_agent_by_keywords(
                available_agents, 
                ["yaml", "kubernetes", "k8s", "config", "설정", "생성"]
            )
            
            confluence_agent = self._find_agent_by_keywords(
                available_agents,
                ["confluence", "문서", "document", "wiki"]
            )
            
            if confluence_agent:
                if content_agent:
                    workflow.steps = [
                        WorkflowStep(
                            agent_id=content_agent.get("id", ""),
                            agent_name=content_agent.get("name", "Content Agent"),
                            action="generate",
                            input_prompt=self._extract_first_task(user_message),
                            task_description="콘텐츠 생성",
                            output_type="yaml"
                        ),
                        WorkflowStep(
                            agent_id=confluence_agent.get("id", ""),
                            agent_name=confluence_agent.get("name", "Confluence Agent"),
                            action="save_document",
                            input_prompt="이전 결과를 Confluence 문서로 저장해주세요.",
                            task_description="생성된 콘텐츠를 Confluence에 저장",
                            use_previous_output=True
                        )
                    ]
                else:
                    workflow.steps = [
                        WorkflowStep(
                            agent_id=confluence_agent.get("id", ""),
                            agent_name=confluence_agent.get("name", "Confluence Agent"),
                            action="create_document",
                            input_prompt=user_message,
                            task_description="Confluence 문서 생성"
                        )
                    ]
                return workflow
        
        # ========================================
        # analyze_and_report: Jira 분석 → Confluence 문서 생성
        # 에이전트 팀 피드백 반영: 2단계 분리 체이닝
        # ========================================
        elif pattern["workflow_type"] == "analyze_and_report":
            jira_agent = self._find_agent_by_keywords(
                available_agents,
                ["jira", "이슈", "issue", "project", "프로젝트"]
            )
            
            confluence_agent = self._find_agent_by_keywords(
                available_agents,
                ["confluence", "문서", "document", "wiki", "페이지"]
            )
            
            if jira_agent and confluence_agent:
                # Step 1: Jira에서 이슈 분석만 요청
                jira_prompt = self._extract_analysis_task(user_message)
                
                # Step 2: Confluence에 문서 생성 (이전 결과를 [CONTEXT]+[TASK] 형식으로 전달)
                confluence_task = self._extract_document_task(user_message)
                
                workflow.steps = [
                    WorkflowStep(
                        agent_id=jira_agent.get("id", ""),
                        agent_name=jira_agent.get("name", "Jira Agent"),
                        action="analyze",
                        input_prompt=jira_prompt,
                        task_description="Jira 이슈 현황 분석",
                        output_type="text"
                    ),
                    WorkflowStep(
                        agent_id=confluence_agent.get("id", ""),
                        agent_name=confluence_agent.get("name", "Confluence Agent"),
                        action="create_document",
                        input_prompt=confluence_task,  # Will be enriched with [CONTEXT] in executor
                        task_description="분석 결과를 Confluence 문서로 생성",
                        use_previous_output=True,  # 이전 결과 사용 플래그
                        output_type="url"
                    )
                ]
                
                logger.info(f"[CHAINING] Built 2-step workflow: {jira_agent.get('name')} → {confluence_agent.get('name')}")
                return workflow
            elif jira_agent:
                # Confluence Agent가 없으면 Jira 분석만
                workflow.steps = [
                    WorkflowStep(
                        agent_id=jira_agent.get("id", ""),
                        agent_name=jira_agent.get("name", "Jira Agent"),
                        action="analyze",
                        input_prompt=user_message,
                        task_description="Jira 이슈 현황 분석"
                    )
                ]
                return workflow
        
        # search_and_document: 검색 → 문서화
        elif pattern["workflow_type"] == "search_and_document":
            jira_agent = self._find_agent_by_keywords(
                available_agents,
                ["jira", "이슈", "issue", "search", "검색"]
            )
            
            confluence_agent = self._find_agent_by_keywords(
                available_agents,
                ["confluence", "문서", "document", "wiki"]
            )
            
            if jira_agent and confluence_agent:
                search_prompt = self._extract_first_task(user_message)
                
                workflow.steps = [
                    WorkflowStep(
                        agent_id=jira_agent.get("id", ""),
                        agent_name=jira_agent.get("name", "Jira Agent"),
                        action="search",
                        input_prompt=search_prompt,
                        task_description="이슈 검색",
                        output_type="text"
                    ),
                    WorkflowStep(
                        agent_id=confluence_agent.get("id", ""),
                        agent_name=confluence_agent.get("name", "Confluence Agent"),
                        action="create_document",
                        input_prompt="검색 결과를 문서로 정리해주세요.",
                        task_description="검색 결과 문서화",
                        use_previous_output=True
                    )
                ]
                return workflow
        
        return None
    
    def _extract_analysis_task(self, message: str) -> str:
        """분석 요청 부분만 추출"""
        # "분석하고", "확인하고" 이후의 문서 생성 부분 제거
        connectors = ["그리고", "후에", "다음에", "그 결과", "바탕으로"]
        
        for conn in connectors:
            if conn in message:
                first_part = message.split(conn)[0]
                # "분석해줘", "확인해줘" 형태로 마무리
                if not first_part.endswith("해줘") and not first_part.endswith("해주세요"):
                    first_part = first_part.rstrip("하고확인분석") + " 분석해줘. 통계, 담당자별 현황, 주의가 필요한 이슈를 포함해서 상세하게 분석해줘."
                return first_part
        
        # 기본: 분석 관련 키워드 포함된 요청으로 변환
        if "분석" in message:
            return message.replace("문서 생성", "").replace("보고서 생성", "").replace("Confluence에", "").strip()
        
        return message
    
    def _extract_document_task(self, message: str) -> str:
        """문서 생성 요청 부분 추출 (기본 템플릿)"""
        # 날짜/제목 정보 추출 시도
        import re
        date_match = re.search(r'(\d+월\s*\d+일|\d+/\d+)', message)
        date_str = date_match.group(1) if date_match else "금일"
        
        # 프로젝트 이름 추출
        project_match = re.search(r'([A-Z]+)\s*프로젝트', message)
        project_name = project_match.group(1) if project_match else ""
        
        if project_name:
            return f"'{date_str} {project_name} 프로젝트 주간 보고서' 제목의 Confluence 문서를 생성해줘. 분석적이고 체계적인 보고서로 만들어줘."
        else:
            return "이 분석 결과를 바탕으로 보고서 문서를 Confluence에 생성해줘. 체계적인 보고서로 만들어줘."
    
    def _extract_first_task(self, message: str) -> str:
        """Extract the first task from a multi-task message"""
        connectors = ["하고", "그리고", "후에", "다음에"]
        
        for conn in connectors:
            if conn in message:
                return message.split(conn)[0] + "해줘"
        
        return message


class HybridWorkflowAnalyzer:
    """
    Hybrid workflow analyzer that tries LLM first, falls back to pattern-based.
    This is the main analyzer to use.
    """
    
    def __init__(self):
        self.llm_analyzer = LLMWorkflowAnalyzer()
        self.pattern_analyzer = PatternBasedWorkflowAnalyzer()
        self._use_llm = self.llm_analyzer._use_llm
        
        if self._use_llm:
            logger.info("[HYBRID] Hybrid workflow analyzer: LLM primary, pattern fallback")
        else:
            logger.info("[PATTERN] Hybrid workflow analyzer: Pattern-based only (LLM unavailable)")
    
    async def analyze(
        self,
        user_message: str,
        available_agents: List[Dict],
        previous_response: Optional[str] = None
    ) -> Optional[Workflow]:
        """
        Analyze user message for multi-agent workflow.
        Tries LLM first, falls back to pattern-based if LLM fails.
        """
        
        # Try LLM analysis first
        if self._use_llm:
            try:
                workflow = await self.llm_analyzer.analyze(
                    user_message, 
                    available_agents, 
                    previous_response
                )
                if workflow:
                    workflow.metadata["analyzer"] = "llm"
                    return workflow
            except Exception as e:
                logger.warning(f"LLM analysis failed, falling back to pattern: {e}")
        
        # Fallback to pattern-based
        workflow = self.pattern_analyzer.analyze(
            user_message, 
            available_agents, 
            previous_response
        )
        if workflow:
            workflow.metadata["analyzer"] = "pattern"
        
        return workflow


class WorkflowExecutor:
    """
    Executes multi-agent workflows step by step.
    
    Phase 2 Enhancements:
    - Supervisor LLM integration for step validation
    - Advanced error recovery (retry, fallback, skip)
    - Structured context passing between steps
    - Artifact management
    """
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.supervisor = supervisor_llm
    
    async def execute(
        self, 
        workflow: Workflow, 
        context_id: str,
        user_id: Optional[str] = None,
        available_agents: Optional[List[Dict]] = None
    ) -> Workflow:
        """
        Execute a workflow step by step with supervisor oversight.
        
        Args:
            workflow: The workflow to execute
            context_id: Conversation context ID
            user_id: Optional user ID for DB persistence
            available_agents: Available agents for fallback (Phase 2)
            
        Returns:
            Updated workflow with results
        """
        workflow.status = WorkflowStepStatus.RUNNING
        available_agents = available_agents or []
        
        # Initialize workflow context
        if not workflow.context:
            workflow.context = AgentContext(
                original_user_request=workflow.description,
                workflow_id=workflow.id
            )
        
        # Safety check for max iterations
        if len(workflow.steps) > workflow.max_iterations:
            logger.warning(f"Workflow has {len(workflow.steps)} steps, limiting to {workflow.max_iterations}")
            workflow.steps = workflow.steps[:workflow.max_iterations]
        
        logger.info(f"[START] Starting workflow execution: {workflow.name}")
        logger.info(f"   Steps: {len(workflow.steps)}")
        logger.info(f"   Supervisor: {'enabled' if workflow.supervisor_enabled else 'disabled'}")
        logger.info(f"   Reasoning: {workflow.reasoning}")
        
        i = 0
        while i < len(workflow.steps):
            step = workflow.steps[i]
            workflow.current_step_index = i
            
            # Initialize step context
            step.context = AgentContext(
                task_description=step.task_description,
                original_user_request=workflow.context.original_user_request,
                previous_results=workflow.context.previous_results.copy(),
                artifacts=workflow.context.artifacts.copy(),
                workflow_id=workflow.id,
                step_index=i
            )
            
            step.mark_started()
            
            logger.info(f"[STEP] Step {i+1}/{len(workflow.steps)}: {step.agent_name}")
            logger.info(f"   Action: {step.action}")
            logger.info(f"   Task: {step.task_description[:100]}..." if len(step.task_description) > 100 else f"   Task: {step.task_description}")
            
            # Execute step with recovery support
            success, should_continue = await self._execute_step_with_recovery(
                step=step,
                workflow=workflow,
                context_id=context_id,
                available_agents=available_agents
            )
            
            if not should_continue:
                logger.error(f"[FAIL] Workflow aborted at step {i+1}")
                workflow.status = WorkflowStepStatus.FAILED
                workflow.completed_at = datetime.now().isoformat()
                return workflow
            
            if success:
                # Update workflow context with step result
                workflow.context.add_previous_result(
                    step_name=f"{step.agent_name}: {step.action}",
                    content=step.output or "",
                    success=True
                )
                
                # Collect artifacts
                for artifact in step.artifacts:
                    workflow.context.artifacts.append(artifact)
                
                logger.info(f"[OK] Step {i+1} completed: {step.agent_name}")
            else:
                # Step failed but workflow can continue (e.g., skipped non-critical step)
                workflow.context.add_previous_result(
                    step_name=f"{step.agent_name}: {step.action}",
                    content=f"[SKIPPED] {step.error}",
                    success=False
                )
                logger.warning(f"[WARN] Step {i+1} skipped: {step.agent_name}")
            
            i += 1
        
        # All steps completed
        workflow.status = WorkflowStepStatus.COMPLETED
        workflow.completed_at = datetime.now().isoformat()
        workflow.final_output = self._build_final_output(workflow)
        
        logger.info(f"[DONE] Workflow completed: {workflow.name}")
        
        # Phase 3: Store workflow in long-term memory
        try:
            await memory_store.store_workflow_result(workflow)
            logger.debug(f"[MEMORY] Workflow stored in memory: {workflow.name}")
        except Exception as e:
            logger.warning(f"[MEMORY] Failed to store workflow: {e}")
        
        return workflow
    
    async def _execute_step_with_recovery(
        self,
        step: WorkflowStep,
        workflow: Workflow,
        context_id: str,
        available_agents: List[Dict]
    ) -> tuple[bool, bool]:
        """
        Execute a step with full error recovery support.
        
        Returns:
            Tuple of (success, should_continue)
            - success: Whether the step completed successfully
            - should_continue: Whether the workflow should continue
        """
        max_attempts = 3 if workflow.retry_policy else 1
        max_modify_attempts = 1  # Limit modify retries to prevent infinite loops
        current_task = step.input_prompt
        current_agent_id = step.agent_id
        current_agent_name = step.agent_name
        modify_count = 0  # Track modify attempts separately
        
        for attempt in range(max_attempts):
            step.retry_count = attempt
            
            try:
                # Build prompt with context
                prompt = self._build_step_prompt_with_context(step, workflow.context)
                
                # Get agent
                from .registry import registry
                agent = registry.get_agent(current_agent_id) or registry.get_agent_by_name(current_agent_name)
                
                if not agent:
                    raise ValueError(f"Agent not found: {current_agent_name}")
                
                # Execute
                response = await self.orchestrator._send_to_agent(
                    agent.url,
                    prompt,
                    context_id
                )
                
                step.output = response.get("content", "")
                
                # Parse artifacts if any
                raw_artifacts = response.get("artifacts", [])
                step.artifacts = self._parse_artifacts(raw_artifacts)
                
                step.mark_completed(step.output)
                
                # Phase 3: Check for handoff request in response
                handoff_request = await self._detect_and_handle_handoff(
                    step, workflow, available_agents, context_id
                )
                if handoff_request:
                    # Handoff was processed, mark step as completed with handoff
                    step.validation_result = {
                        "action": "handoff",
                        "target": handoff_request.target_agent_name,
                        "task": handoff_request.task_description
                    }
                    logger.info(f"[HANDOFF] Handoff executed to {handoff_request.target_agent_name}")
                
                # Supervisor validation (if enabled)
                if workflow.supervisor_enabled and self.supervisor.is_available:
                    decision = await self.supervisor.validate_step_result(
                        step, workflow, available_agents
                    )
                    step.validation_result = {
                        "action": decision.action,
                        "reasoning": decision.reasoning,
                        "confidence": decision.confidence
                    }
                    
                    if decision.action == "abort":
                        step.status = WorkflowStepStatus.FAILED
                        step.error = f"Supervisor aborted: {decision.reasoning}"
                        return False, False  # Failed, don't continue
                    
                    if decision.action == "modify" and decision.modified_task:
                        # Supervisor wants to modify and retry (limited)
                        modify_count += 1
                        if modify_count > max_modify_attempts:
                            logger.info(f"[MODIFY] Max modify attempts ({max_modify_attempts}) reached, accepting result")
                            return True, True  # Accept the result and continue
                        logger.info(f"[MODIFY] Supervisor requested modification ({modify_count}/{max_modify_attempts})")
                        current_task = decision.modified_task
                        step.input_prompt = current_task
                        continue  # Retry with modified task
                
                return True, True  # Success, continue
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Step attempt {attempt + 1}/{max_attempts} failed: {error_msg}")
                step.error = error_msg
                
                # Get recovery decision from supervisor
                if workflow.supervisor_enabled and self.supervisor.is_available:
                    decision = await self.supervisor.decide_error_recovery(
                        step, error_msg, workflow, available_agents
                    )
                    
                    logger.info(f"[RECOVERY] Recovery decision: {decision.action}")
                    
                    if decision.action == "abort":
                        step.status = WorkflowStepStatus.FAILED
                        return False, False  # Failed, don't continue
                    
                    if decision.action == "skip" and not step.is_critical:
                        step.status = WorkflowStepStatus.SKIPPED
                        return False, True  # Failed but continue
                    
                    if decision.action == "fallback" and decision.fallback_agent_id:
                        # Try fallback agent
                        logger.info(f"🔀 Trying fallback agent")
                        current_agent_id = decision.fallback_agent_id
                        fallback_agent = next(
                            (a for a in available_agents if a.get('id') == decision.fallback_agent_id),
                            None
                        )
                        if fallback_agent:
                            current_agent_name = fallback_agent.get('name', current_agent_name)
                        continue
                    
                    if decision.action == "modify" and decision.modified_task:
                        current_task = decision.modified_task
                        step.input_prompt = current_task
                        continue
                    
                    # Default: retry
                    if attempt < max_attempts - 1:
                        backoff = workflow.retry_policy.backoff_seconds if workflow.retry_policy else 1.0
                        await asyncio.sleep(backoff * (attempt + 1))
                        continue
                else:
                    # No supervisor, simple retry
                    if attempt < max_attempts - 1:
                        backoff = workflow.retry_policy.backoff_seconds if workflow.retry_policy else 1.0
                        await asyncio.sleep(backoff * (attempt + 1))
                        continue
        
        # All attempts failed
        step.status = WorkflowStepStatus.FAILED
        
        if not step.is_critical:
            step.status = WorkflowStepStatus.SKIPPED
            return False, True  # Failed but continue for non-critical
        
        return False, False  # Failed, don't continue
    
    async def _detect_and_handle_handoff(
        self,
        step: WorkflowStep,
        workflow: 'Workflow',
        available_agents: List[Dict],
        context_id: str
    ) -> Optional[HandoffRequest]:
        """
        Phase 3: Detect and handle handoff requests in agent responses.
        
        If an agent's response suggests handing off to another agent,
        this method will dynamically add a new step to the workflow.
        
        Args:
            step: The completed step to check for handoff
            workflow: The parent workflow
            available_agents: Available agents for handoff
            context_id: Conversation context ID
            
        Returns:
            HandoffRequest if handoff was detected and processed, None otherwise
        """
        if not step.output:
            return None
        
        # Detect handoff request in response
        handoff_request = await handoff_detector.detect(
            step.output,
            available_agents,
            step.agent_name
        )
        
        if not handoff_request:
            return None
        
        # Find target agent
        target_agent = None
        for agent in available_agents:
            if agent.get('name', '').lower() == handoff_request.target_agent_name.lower():
                target_agent = agent
                break
            # Partial match
            if handoff_request.target_agent_name.lower() in agent.get('name', '').lower():
                target_agent = agent
                break
        
        if not target_agent:
            logger.warning(f"[HANDOFF] Target agent not found: {handoff_request.target_agent_name}")
            return None
        
        logger.info(f"[HANDOFF] Detected: {step.agent_name} -> {target_agent.get('name')}")
        logger.info(f"[HANDOFF] Task: {handoff_request.task_description[:100]}")
        
        # Build context for handoff
        handoff_context = AgentContext(
            task_description=handoff_request.task_description,
            original_user_request=workflow.context.original_user_request if workflow.context else "",
            workflow_id=workflow.id,
            step_index=workflow.current_step_index + 1
        )
        
        # Add previous step result to context
        handoff_context.add_previous_result(
            step_name=f"{step.agent_name}: {step.action}",
            content=step.output,
            success=True
        )
        
        # Add any context data from the handoff request
        handoff_context.metadata.update(handoff_request.context_data)
        
        # Create new step for handoff target
        handoff_step = WorkflowStep(
            agent_id=target_agent.get('id', ''),
            agent_name=target_agent.get('name', ''),
            action=f"handoff_{handoff_request.reason.value}",
            input_prompt=handoff_request.task_description,
            task_description=handoff_request.task_description,
            use_previous_output=True,
            context=handoff_context,
            is_critical=False  # Handoff steps are non-critical by default
        )
        
        # Insert handoff step into workflow (right after current step)
        insert_idx = workflow.current_step_index + 1
        workflow.steps.insert(insert_idx, handoff_step)
        
        logger.info(f"[HANDOFF] Added step {insert_idx + 1}: {handoff_step.agent_name}")
        
        # Update workflow metadata
        workflow.metadata["handoffs"] = workflow.metadata.get("handoffs", [])
        workflow.metadata["handoffs"].append({
            "from": step.agent_name,
            "to": target_agent.get('name'),
            "reason": handoff_request.reason.value,
            "task": handoff_request.task_description[:100]
        })
        
        return handoff_request
    
    def _build_step_prompt_with_context(self, step: WorkflowStep, context: AgentContext) -> str:
        """
        Build prompt with structured context using [CONTEXT]+[TASK] format.
        
        에이전트 팀 요구사항에 맞춘 형식:
        [CONTEXT]
        {이전 단계의 결과 데이터}
        
        [TASK]
        {현재 단계의 작업 지시}
        """
        parts = []
        
        # Add previous results if needed (에이전트 팀 요구 형식)
        if step.use_previous_output and context.previous_results:
            last_result = context.previous_results[-1]
            content = last_result['content']
            
            # Jira 분석 결과는 길 수 있으므로 충분한 길이 허용 (5000자)
            if len(content) > 5000:
                content = content[:5000] + "\n... (데이터 일부 생략)"
            
            # 에이전트 팀 요구 형식: [CONTEXT]\n{데이터}\n\n[TASK]\n{작업}
            parts.append(f"""[CONTEXT]
{content}""")
        
        # Add task description with clear marker
        parts.append(f"""[TASK]
{step.input_prompt}""")
        
        return "\n\n".join(parts)
    
    def _parse_artifacts(self, raw_artifacts: List[Any]) -> List[Artifact]:
        """Parse raw artifact data into Artifact objects"""
        artifacts = []
        
        for raw in raw_artifacts:
            if isinstance(raw, dict):
                artifact = Artifact(
                    type=ArtifactType(raw.get('type', 'text')),
                    name=raw.get('name', 'artifact'),
                    content=raw.get('content', ''),
                    mime_type=raw.get('mime_type', 'text/plain'),
                    url=raw.get('url'),
                    metadata=raw.get('metadata', {})
                )
                artifacts.append(artifact)
            elif isinstance(raw, Artifact):
                artifacts.append(raw)
        
        return artifacts
    
    def _build_step_prompt(self, step: WorkflowStep, previous_output: Optional[str]) -> str:
        """
        Build the prompt for a workflow step (legacy compatibility).
        Uses [CONTEXT]+[TASK] format for agent compatibility.
        """
        if step.use_previous_output and previous_output:
            # 충분한 길이 허용 (5000자)
            content = previous_output
            if len(content) > 5000:
                content = content[:5000] + "\n... (데이터 일부 생략)"
            
            return f"""[CONTEXT]
{content}

[TASK]
{step.input_prompt}"""
        
        return step.input_prompt
    
    def _build_final_output(self, workflow: Workflow) -> str:
        """Build the final output from all workflow steps"""
        outputs = []
        
        outputs.append(f"## [WORKFLOW] 워크플로우 완료: {workflow.description}\n")
        
        if workflow.reasoning:
            outputs.append(f"*분석: {workflow.reasoning}*\n")
        
        # Summary stats
        completed = len(workflow.get_completed_steps())
        failed = len(workflow.get_failed_steps())
        skipped = len([s for s in workflow.steps if s.status == WorkflowStepStatus.SKIPPED])
        
        outputs.append(f"**결과 요약**: {completed} 성공 / {failed} 실패 / {skipped} 건너뜀\n")
        
        for i, step in enumerate(workflow.steps):
            if step.status == WorkflowStepStatus.COMPLETED:
                status_emoji = "[OK]"
            elif step.status == WorkflowStepStatus.SKIPPED:
                status_emoji = "[SKIP]"
            else:
                status_emoji = "[FAIL]"
            
            outputs.append(f"### {status_emoji} Step {i+1}: {step.agent_name}")
            outputs.append(f"*작업: {step.action}*\n")
            
            if step.output:
                outputs.append(step.output)
            
            if step.error:
                outputs.append(f"**오류:** {step.error}")
            
            # Show supervisor validation if available
            if step.validation_result:
                val = step.validation_result
                outputs.append(f"\n*Supervisor: {val.get('action')} (confidence: {val.get('confidence', 0):.0%})*")
            
            outputs.append("")
        
        return "\n".join(outputs)


# =============================================================================
# Global instances
# =============================================================================

# Legacy pattern-based analyzer (for backward compatibility)
workflow_analyzer_pattern = PatternBasedWorkflowAnalyzer()

# New hybrid analyzer (LLM + pattern fallback) - USE THIS
workflow_analyzer = HybridWorkflowAnalyzer()

# Convenience function for async analysis
async def analyze_workflow(
    user_message: str,
    available_agents: List[Dict],
    previous_response: Optional[str] = None
) -> Optional[Workflow]:
    """
    Convenience function to analyze workflow using the hybrid analyzer.
    This is the recommended way to detect multi-agent workflows.
    """
    return await workflow_analyzer.analyze(user_message, available_agents, previous_response)
