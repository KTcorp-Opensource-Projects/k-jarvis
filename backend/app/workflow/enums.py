from enum import Enum

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
