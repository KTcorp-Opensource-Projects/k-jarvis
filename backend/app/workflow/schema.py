import uuid
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .enums import WorkflowStepStatus, ErrorRecoveryStrategy, ArtifactType, HandoffReason

# ==================== Handoff Schemas ====================

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

# ==================== Context & Artifact Schemas ====================

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
            summary_parts.append(f"\\nPrevious Results ({len(self.previous_results)}):")
            for i, result in enumerate(self.previous_results[-3:], 1):  # Last 3 results
                summary_parts.append(f"  {i}. [{result['step']}]: {result['content'][:200]}...")
        
        if self.artifacts:
            summary_parts.append(f"\\nArtifacts ({len(self.artifacts)}):")
            for artifact in self.artifacts[-3:]:  # Last 3 artifacts
                summary_parts.append(f"  - {artifact.name} ({artifact.type.value})")
        
        if self.constraints:
            summary_parts.append(f"\\nConstraints: {', '.join(self.constraints)}")
        
        return "\\n".join(summary_parts)
    
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

# ==================== Workflow Schemas ====================

@dataclass
class RetryPolicy:
    """Retry policy for workflow steps"""
    max_retries: int = 3
    backoff_seconds: float = 1.0
    retry_on_errors: List[str] = field(default_factory=lambda: ["timeout", "connection", "rate_limit"])
    fallback_agent_id: Optional[str] = None  # Agent to use if all retries fail
    allow_skip: bool = False  # Whether step can be skipped on failure

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
