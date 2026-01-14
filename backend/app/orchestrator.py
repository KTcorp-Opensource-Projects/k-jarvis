"""
A2A Agent Orchestrator
Core orchestration logic for routing requests to agents and handling responses
"""
import json
import re
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any, List
from loguru import logger
import httpx
from tenacity import AsyncRetrying, retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import get_settings
from .models import (
    ChatRequest, ChatResponse, ChatMessage, Conversation,
    MessageRole, TaskState, StreamEvent, AgentRoutingInfo
)
from .registry import registry
from .router import router  # Legacy router (fallback)
from .hybrid_router import get_hybrid_router  # New hybrid router with pgvector
from .conversation_service import conversation_service
from .workflow import analyze_workflow, WorkflowExecutor, Workflow, WorkflowStepStatus
from .llm_client import get_llm_client
from .mcp_token_service import get_mcp_token_service
from .token_cache import get_token_cache
from .database import get_db_session

class GlobalHttpClient:
    """
    Global HTTP Client Singleton for Connection Pooling.
    Initializes a shared httpx.AsyncClient to reuse TCP connections.
    """
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            # Lazy initialization if not initialized via lifespan (safety net)
            # Ideally initialized in main.py lifespan
            cls._client = httpx.AsyncClient(
                timeout=90.0,
                verify=False,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
        return cls._client

    @classmethod
    async def initialize(cls):
        if cls._client is None:
            logger.info("[GlobalHttpClient] Initializing global HTTP client (Pool: 20/100)")
            cls._client = httpx.AsyncClient(
                timeout=90.0,
                verify=False,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )

    @classmethod
    async def close(cls):
        if cls._client:
            logger.info("[GlobalHttpClient] Closing global HTTP client")
            await cls._client.aclose()
            cls._client = None



class ConversationSummarizer:
    """
    대화 히스토리를 요약하여 에이전트에게 맥락을 전달합니다.
    
    기능:
    1. 최근 대화 내용 요약
    2. 중요 아티팩트 정보 추출 (페이지 ID, 이슈 번호 등)
    3. 에이전트별 처리 기록 추출
    """
    
    def __init__(self, max_history: int = 5, use_llm_summary: bool = True):
        self.max_history = max_history
        self.use_llm_summary = use_llm_summary
        self.llm_client = get_llm_client() if use_llm_summary else None
    
    async def summarize(
        self,
        conversation: Conversation,
        current_message: str,
        target_agent: Optional[str] = None
    ) -> str:
        """
        대화 히스토리를 요약하여 컨텍스트 문자열 생성.
        
        Args:
            conversation: 현재 대화 객체
            current_message: 현재 사용자 메시지
            target_agent: 대상 에이전트 이름 (해당 에이전트 관련 정보 강조)
            
        Returns:
            에이전트에게 전달할 컨텍스트가 포함된 메시지
        """
        if len(conversation.messages) <= 1:
            # 첫 메시지면 히스토리 없음
            return current_message
        
        # 최근 메시지 추출 (현재 메시지 제외)
        recent_messages = conversation.messages[-(self.max_history + 1):-1] if len(conversation.messages) > 1 else []
        
        if not recent_messages:
            return current_message
        
        # 1. 중요 아티팩트 정보 추출
        artifacts_info = self._extract_artifacts(recent_messages)
        
        # 2. 대화 요약 생성
        if self.use_llm_summary and self.llm_client and self.llm_client.is_available():
            summary = await self._generate_llm_summary(recent_messages, target_agent)
        else:
            summary = self._generate_simple_summary(recent_messages, target_agent)
        
        # 3. 컨텍스트 메시지 구성
        context_parts = []
        
        if summary:
            context_parts.append(f"[CONVERSATION HISTORY]\n{summary}")
        
        if artifacts_info:
            context_parts.append(f"[RELEVANT INFO]\n{artifacts_info}")
        
        context_parts.append(f"[CURRENT REQUEST]\n{current_message}")
        
        return "\n\n".join(context_parts)
    
    def _extract_artifacts(self, messages: List[ChatMessage]) -> str:
        """메시지에서 중요한 아티팩트 정보 추출 (페이지 ID, 이슈 번호, URL 등)"""
        artifacts = []
        
        for msg in messages:
            content = msg.content
            
            # Confluence 페이지 ID/URL 추출
            page_ids = re.findall(r'pages/(\d+)', content)
            if page_ids:
                artifacts.append(f"- Confluence Page IDs: {', '.join(set(page_ids))}")
            
            # Jira 이슈 키 추출
            issue_keys = re.findall(r'([A-Z]+-\d+)', content)
            if issue_keys:
                artifacts.append(f"- Jira Issues: {', '.join(set(issue_keys))}")
            
            # URL 추출
            urls = re.findall(r'https?://[^\s\)]+', content)
            if urls:
                for url in urls[:3]:  # 최대 3개
                    artifacts.append(f"- URL: {url}")
            
            # 에이전트 정보
            if msg.metadata:
                agent = msg.metadata.get("agent")
                if agent:
                    artifacts.append(f"- Processed by: {agent}")
        
        return "\n".join(list(dict.fromkeys(artifacts)))  # 중복 제거
    
    def _generate_simple_summary(
        self,
        messages: List[ChatMessage],
        target_agent: Optional[str] = None
    ) -> str:
        """간단한 대화 요약 생성 (LLM 없이)"""
        summary_parts = []
        
        for i, msg in enumerate(messages[-3:], 1):  # 최근 3개만
            role = "User" if msg.role == MessageRole.USER else "Assistant"
            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            # 줄바꿈 제거
            content_preview = content_preview.replace("\n", " ")
            
            agent_info = ""
            if msg.metadata and msg.metadata.get("agent"):
                agent_info = f" [{msg.metadata['agent']}]"
            
            summary_parts.append(f"{i}. {role}{agent_info}: {content_preview}")
        
        return "\n".join(summary_parts)
    
    async def _generate_llm_summary(
        self,
        messages: List[ChatMessage],
        target_agent: Optional[str] = None
    ) -> str:
        """LLM을 사용한 대화 요약 생성"""
        try:
            # 대화 내용 구성
            conversation_text = []
            for msg in messages[-5:]:  # 최근 5개
                role = "User" if msg.role == MessageRole.USER else "Assistant"
                agent_info = f" ({msg.metadata.get('agent')})" if msg.metadata and msg.metadata.get('agent') else ""
                conversation_text.append(f"{role}{agent_info}: {msg.content[:300]}")
            
            prompt = f"""다음 대화를 2-3문장으로 간결하게 요약해주세요.
특히 다음 정보에 집중하세요:
- 사용자가 요청한 주요 작업
- 생성되거나 수정된 리소스 (페이지, 이슈 등)
- 현재 진행 상황

대화 내용:
{chr(10).join(conversation_text)}

요약:"""
            
            response = await self.llm_client.chat_completion([
                {"role": "user", "content": prompt}
            ], temperature=0.3, max_tokens=200)
            
            return response.strip()
            
        except Exception as e:
            logger.warning(f"[SUMMARIZER] LLM summary failed, using simple summary: {e}")
            return self._generate_simple_summary(messages, target_agent)


class A2AOrchestrator:
    """
    Main orchestrator that:
    1. Receives user messages
    2. Routes to appropriate agents via intelligent routing
    3. Handles A2A protocol communication
    4. Manages conversation state (DB-backed for authenticated users)
    5. Provides conversation history context to agents
    """
    
    def __init__(self):
        # 메모리 캐시 (비인증 사용자용 / 빠른 액세스용)
        self._conversations: Dict[str, Conversation] = {}
        self._settings = get_settings()
        # Workflow executor for agent chaining
        self._workflow_executor = WorkflowExecutor(self)
        # Conversation summarizer for context-aware agent communication
        self._summarizer = ConversationSummarizer(max_history=5, use_llm_summary=True)
    
    def get_or_create_conversation(self, conversation_id: Optional[str] = None) -> Conversation:
        """Get existing conversation or create new one (in-memory)"""
        if conversation_id and conversation_id in self._conversations:
            return self._conversations[conversation_id]
        
        conversation = Conversation()
        self._conversations[conversation.id] = conversation
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID (in-memory)"""
        return self._conversations.get(conversation_id)
    
    def list_conversations(self) -> list[Conversation]:
        """List all conversations (in-memory)"""
        return list(self._conversations.values())
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation (in-memory)"""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False
    
    async def process_message(
        self, 
        request: ChatRequest,
        user_id: Optional[str] = None,
        kauth_user_id: Optional[str] = None,  # Option C: K-Auth user ID for MCPHub
        jwt_token: Optional[str] = None  # Directive 007: Raw Token
    ) -> ChatResponse:
        """
        Process a user message:
        1. Save to conversation (DB for authenticated, memory for anonymous)
        2. Route to appropriate agent
        3. Get response from agent (with conversation history for context)
        4. Return response
        """
        # Get or create conversation
        if user_id:
            # DB-backed conversation for authenticated users
            conversation = await conversation_service.get_or_create_conversation(
                request.conversation_id,
                user_id
            )
            # Also cache in memory for reference task IDs
            self._conversations[conversation.id] = conversation
        else:
            # In-memory conversation for anonymous users
            conversation = self.get_or_create_conversation(request.conversation_id)
        
        # Add user message to conversation
        user_message = ChatMessage(
            role=MessageRole.USER,
            content=request.message
        )
        conversation.messages.append(user_message)
        conversation.updated_at = datetime.utcnow()
        
        # Save user message to DB if authenticated
        if user_id:
            await conversation_service.add_message(
                conversation.id,
                MessageRole.USER,
                request.message
            )
        
        # ========================================
        # Check for Multi-Agent Workflow (Agent Chaining) - Phase 1 Improved
        # Now uses LLM-based analysis with pattern fallback
        # ========================================
        available_agents = [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "url": a.url,
                "skills": [s.model_dump() for s in a.skills]
            }
            for a in registry.list_agents(include_offline=False)
        ]
        
        # Get previous response for context (supports "이 결과를 저장해줘" type requests)
        previous_response = None
        if conversation.messages:
            for msg in reversed(conversation.messages):
                if msg.role == MessageRole.ASSISTANT:
                    previous_response = msg.content
                    break
        
        # Use new async LLM-based workflow analyzer (with pattern fallback)
        workflow = await analyze_workflow(
            request.message, 
            available_agents,
            previous_response
        )
        
        if workflow and len(workflow.steps) >= 1:
            analyzer_type = workflow.metadata.get("analyzer", "unknown")
            logger.info(f"[WORKFLOW] Multi-agent workflow detected ({analyzer_type}): {workflow.name} ({len(workflow.steps)} steps)")
            if workflow.reasoning:
                logger.info(f"   Reasoning: {workflow.reasoning}")
            # Phase 2: Pass available_agents for Supervisor fallback support
            return await self._execute_workflow(workflow, conversation, user_id, available_agents)
        
        # ========================================
        # Single Agent Routing (Normal Flow)
        # ========================================
        # Route to agent using Hybrid Router (pgvector + keyword)
        hybrid_router = get_hybrid_router()
        routing_decision = await hybrid_router.route(request.message, request.enabled_agent_ids)
        
        # Fallback to legacy router if hybrid router fails
        if not routing_decision:
            logger.debug("[Routing] Hybrid router returned None, falling back to legacy router")
            routing_decision = await router.route(request.message, request.enabled_agent_ids)
        
        if routing_decision:
            logger.info(f"Routing to agent: {routing_decision.agent_name} ({routing_decision.reasoning})")
            
            # Get reference task IDs from previous interactions (A2A Standard)
            reference_task_ids = self._get_reference_task_ids(conversation)
            
            # Generate context-enriched message with conversation history
            enriched_message = await self._summarizer.summarize(
                conversation,
                request.message,
                target_agent=routing_decision.agent_name
            )
            logger.debug(f"[CONTEXT] Enriched message with history: {len(enriched_message)} chars")
            
            # Option C: Pass kauth_user_id to agent for MCPHub token lookup
            if kauth_user_id:
                logger.debug(f"[A2A] Will pass kauth_user_id to agent: {kauth_user_id[:8]}...")
            
            # Send message to agent via A2A protocol (Standard Compliant)
            agent_response = await self._send_to_agent(
                routing_decision.agent_url,
                enriched_message,  # Now includes conversation history context
                conversation.id,  # contextId for multi-turn
                reference_task_ids,
                user_id,
                kauth_user_id,  # Option C: K-Auth user ID for MCPHub token lookup
                jwt_token  # Directive 007: Pass Raw Token
            )
            
            # Extract task_id from response (A2A Standard)
            task_id = agent_response.get("task_id")
            
            # Create response
            response = ChatResponse(
                conversation_id=conversation.id,
                content=agent_response.get("content", "Agent did not provide a response."),
                agent_used=routing_decision.agent_name,
                task_state=TaskState(agent_response.get("state", "completed")),
                artifacts=agent_response.get("artifacts", []),
                metadata={
                    "routing": {
                        "agent_id": routing_decision.agent_id,
                        "confidence": routing_decision.confidence,
                        "reasoning": routing_decision.reasoning
                    },
                    "task_id": task_id  # A2A Standard: Store for referenceTaskIds
                }
            )
        else:
            # No suitable agent found - use fallback response
            logger.info("No suitable agent found, using fallback response")
            task_id = None
            response = ChatResponse(
                conversation_id=conversation.id,
                content=self._get_fallback_response(request.message),
                agent_used=None,
                task_state=TaskState.COMPLETED,
                metadata={"routing": {"status": "no_agent_matched"}}
            )
        
        # Add assistant message to conversation with task_id (A2A Standard)
        assistant_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response.content,
            metadata={
                "agent": response.agent_used,
                "task_id": task_id  # Store task_id for referenceTaskIds
            }
        )
        conversation.messages.append(assistant_message)
        
        # Save assistant message to DB if authenticated
        if user_id:
            await conversation_service.add_message(
                conversation.id,
                MessageRole.ASSISTANT,
                response.content,
                agent_used=response.agent_used,
                task_id=task_id,
                metadata={"routing": response.metadata.get("routing")}
            )
        
        # Update conversation title if first message
        if len(conversation.messages) == 2:
            new_title = request.message[:50] + ("..." if len(request.message) > 50 else "")
            conversation.title = new_title
            if user_id:
                await conversation_service.update_conversation_title(conversation.id, new_title)
        
        return response
    
    async def _execute_workflow(
        self,
        workflow: Workflow,
        conversation: Conversation,
        user_id: Optional[str] = None,
        available_agents: Optional[List[Dict]] = None
    ) -> ChatResponse:
        """
        Execute a multi-agent workflow (Agent Chaining).
        
        Phase 2 Enhancement: Now passes available_agents for Supervisor fallback.
        
        Args:
            workflow: The workflow to execute
            conversation: Current conversation
            user_id: Optional user ID for DB persistence
            available_agents: Available agents for Supervisor fallback
            
        Returns:
            ChatResponse with combined results from all workflow steps
        """
        logger.info(f"[WORKFLOW] Starting workflow execution: {workflow.name}")
        logger.info(f"   Supervisor: {'enabled' if workflow.supervisor_enabled else 'disabled'}")
        
        # Execute the workflow with Supervisor support
        completed_workflow = await self._workflow_executor.execute(
            workflow,
            conversation.id,
            user_id,
            available_agents or []
        )
        
        # Build response based on workflow results
        if completed_workflow.status == WorkflowStepStatus.COMPLETED:
            content = completed_workflow.final_output or "워크플로우가 완료되었습니다."
            
            # Collect all artifacts from all steps
            all_artifacts = []
            agents_used = []
            for step in completed_workflow.steps:
                # Convert Artifact objects to dicts for JSON serialization
                for artifact in step.artifacts:
                    if hasattr(artifact, 'to_dict'):
                        all_artifacts.append(artifact.to_dict())
                    elif isinstance(artifact, dict):
                        all_artifacts.append(artifact)
                if step.status == WorkflowStepStatus.COMPLETED:
                    agents_used.append(step.agent_name)
            
            response = ChatResponse(
                conversation_id=conversation.id,
                content=content,
                agent_used=" → ".join(agents_used),  # Show chained agents
                task_state=TaskState.COMPLETED,
                artifacts=all_artifacts,
                metadata={
                    "workflow": {
                        "id": workflow.id,
                        "name": workflow.name,
                        "steps": len(workflow.steps),
                        "agents": agents_used
                    }
                }
            )
        else:
            # Workflow failed
            failed_step = next(
                (s for s in completed_workflow.steps if s.status == WorkflowStepStatus.FAILED),
                None
            )
            error_msg = failed_step.error if failed_step else "Unknown error"
            
            response = ChatResponse(
                conversation_id=conversation.id,
                content=f"워크플로우 실행 중 오류가 발생했습니다: {error_msg}",
                agent_used=failed_step.agent_name if failed_step else None,
                task_state=TaskState.FAILED,
                metadata={
                    "workflow": {
                        "id": workflow.id,
                        "name": workflow.name,
                        "error": error_msg
                    }
                }
            )
        
        # Add assistant message to conversation
        assistant_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response.content,
            metadata={
                "workflow": workflow.name,
                "agents": response.metadata.get("workflow", {}).get("agents", [])
            }
        )
        conversation.messages.append(assistant_message)
        
        # Save to DB if authenticated
        if user_id:
            await conversation_service.add_message(
                conversation.id,
                MessageRole.ASSISTANT,
                response.content,
                agent_used=response.agent_used,
                metadata=response.metadata
            )
        
        logger.info(f"[WORKFLOW] Workflow completed: {workflow.name} - Status: {completed_workflow.status}")
        
        return response
    
    async def process_message_stream(
        self,
        request: ChatRequest,
        user_id: Optional[str] = None,
        kauth_user_id: Optional[str] = None,  # Option C: K-Auth user ID for MCPHub
        jwt_token: Optional[str] = None  # Directive 007: Raw Token
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Process a user message with streaming response.
        """
        # Get or create conversation
        if user_id:
            conversation = await conversation_service.get_or_create_conversation(
                request.conversation_id,
                user_id
            )
            self._conversations[conversation.id] = conversation
        else:
            conversation = self.get_or_create_conversation(request.conversation_id)
        
        # Add user message
        user_message = ChatMessage(
            role=MessageRole.USER,
            content=request.message
        )
        conversation.messages.append(user_message)
        
        # Save user message to DB if authenticated
        if user_id:
            await conversation_service.add_message(
                conversation.id,
                MessageRole.USER,
                request.message
            )
        
        # Emit initial event
        yield StreamEvent(
            event="start",
            data={
                "conversation_id": conversation.id,
                "message_id": str(uuid.uuid4())
            }
        )
        
        # Route to agent using Hybrid Router (pgvector + keyword)
        hybrid_router = get_hybrid_router()
        routing_decision = await hybrid_router.route(request.message, request.enabled_agent_ids)
        
        # Fallback to legacy router if hybrid router fails
        if not routing_decision:
            logger.debug("[Routing] Hybrid router returned None, falling back to legacy router")
            routing_decision = await router.route(request.message, request.enabled_agent_ids)
        
        # Emit routing info
        yield StreamEvent(
            event="routing",
            data={
                "agent": routing_decision.agent_name if routing_decision else None,
                "confidence": routing_decision.confidence if routing_decision else 0
            }
        )
        
        if routing_decision:
            # Get reference task IDs (A2A Standard)
            reference_task_ids = self._get_reference_task_ids(conversation)
            
            # Generate context-enriched message with conversation history
            enriched_message = await self._summarizer.summarize(
                conversation,
                request.message,
                target_agent=routing_decision.agent_name
            )
            
            # Stream from agent
            full_content = ""
            async for chunk in self._stream_from_agent(
                routing_decision.agent_url,
                enriched_message,  # Now includes conversation history context
                conversation.id,
                conversation.id,
                reference_task_ids,
                user_id,
                jwt_token=jwt_token  # Directive 007: Pass Raw Token
            ):
                full_content += chunk
                yield StreamEvent(
                    event="content",
                    data={"text": chunk, "agent": routing_decision.agent_name}
                )
            
            # Add to conversation
            assistant_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=full_content,
                metadata={"agent": routing_decision.agent_name}
            )
            conversation.messages.append(assistant_message)
            
            # Save to DB if authenticated
            if user_id:
                await conversation_service.add_message(
                    conversation.id,
                    MessageRole.ASSISTANT,
                    full_content,
                    agent_used=routing_decision.agent_name
                )
            
        else:
            # Fallback response
            fallback = self._get_fallback_response(request.message)
            yield StreamEvent(
                event="content",
                data={"text": fallback, "agent": None}
            )
            
            assistant_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=fallback
            )
            conversation.messages.append(assistant_message)
            
            # Save to DB if authenticated
            if user_id:
                await conversation_service.add_message(
                    conversation.id,
                    MessageRole.ASSISTANT,
                    fallback
                )
        
        # Update title if first message
        if len(conversation.messages) == 2 and user_id:
            new_title = request.message[:50] + ("..." if len(request.message) > 50 else "")
            await conversation_service.update_conversation_title(conversation.id, new_title)
        
        # Emit completion
        yield StreamEvent(
            event="done",
            data={"conversation_id": conversation.id}
        )
    
    def _get_reference_task_ids(self, conversation: Conversation, max_refs: int = 5) -> list:
        """
        Get reference task IDs from previous interactions (A2A Standard).
        
        A2A uses referenceTaskIds to allow agents to understand 
        which previous tasks the current message relates to.
        """
        task_ids = []
        for msg in conversation.messages[-max_refs:]:
            if msg.metadata and "task_id" in msg.metadata:
                task_ids.append(msg.metadata["task_id"])
        return task_ids if task_ids else None
    

    
    async def _send_to_agent(
        self,
        agent_url: str,
        message: str,
        context_id: str,
        reference_task_ids: list = None,
        user_id: Optional[str] = None,
        kauth_user_id: Optional[str] = None,
        jwt_token: Optional[str] = None  # Directive 007: Raw Token
    ) -> Dict[str, Any]:
        """
        Send message to agent using A2A protocol (Standard + Legacy) with Global Client & Retries.
        
        Retry Policy:
        - Retries performed on HTTP transport layer only.
        - Message IDs and Request IDs are generated ONCE to ensure idempotency.
        """
        try:
            # Generate request ID (ONCE)
            request_id = str(uuid.uuid4())
            
            # Build headers
            headers = {
                "Content-Type": "application/json",
                "X-Request-Id": request_id
            }
            
            if user_id:
                headers["X-User-Id"] = user_id
            
            if kauth_user_id:
                # Directive 007: Use X-Mcp-User-Id (standardized)
                headers["X-Mcp-User-Id"] = kauth_user_id
                # Legacy Support (Temporary)
                headers["X-MCPHub-User-Id"] = kauth_user_id
                logger.debug(f"[A2A] Added X-Mcp-User-Id header: {kauth_user_id[:8]}...")
            
            if jwt_token:
                # Directive 007: Identity Propagation
                headers["Authorization"] = f"Bearer {jwt_token}"
                logger.debug(f"[A2A] Added Authorization header: Bearer {jwt_token[:10]}...")
            
            logger.debug(f"[A2A] Request ID: {request_id}")
            
            # Use Global Client (Connection Pooling)
            client = GlobalHttpClient.get_client()
            
            # Message Construction (ONCE)
            message_parts = [{"text": message}]
            message_obj = {
                "role": "user",
                "parts": message_parts,
                "messageId": str(uuid.uuid4()),
                "contextId": context_id
            }
            if reference_task_ids:
                message_obj["referenceTaskIds"] = reference_task_ids
            
            # Standard Payload (PascalCase) (ONCE)
            standard_payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "SendMessage",
                "params": {"message": message_obj}
            }
            
            # Execute Request with Retry Logic (Idempotent)
            response = None
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.PoolTimeout)),
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=4),
                reraise=True
            ):
                with attempt:
                    response = await client.post(
                        f"{agent_url}/tasks/send",
                        json=standard_payload,
                        headers=headers
                    )
            
            # Process Response
            if response and response.status_code == 200:
                result = response.json()
                if "error" in result and result.get("error", {}).get("code") == -32601:
                    logger.info("[A2A] Standard method not supported, falling back to legacy method")
                    # Legacy fallback logic here (Note: Legacy fallback does NOT auto-retry internally yet)
                    return await self._send_to_agent_legacy(
                        client, agent_url, message, context_id, 
                        reference_task_ids, headers
                    )
                return self._parse_a2a_response(result)
            else:
                logger.info(f"[A2A] Standard method failed (HTTP {response.status_code if response else 'None'}), trying legacy")
                return await self._send_to_agent_legacy(
                    client, agent_url, message, context_id,
                    reference_task_ids, headers
                )
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to agent at {agent_url}")
            return {"content": "Agent request timed out.", "state": "failed"}
        except Exception as e:
            logger.error(f"Error communicating with agent: {e}")
            return {"content": f"Error communicating with agent: {str(e)}", "state": "failed"}

    async def _send_to_agent_legacy(
        self,
        client: httpx.AsyncClient,
        agent_url: str,
        message: str,
        context_id: str,
        reference_task_ids: list = None,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Legacy A2A method for backward compatibility.
        Uses lowercase/slash method names (message/send).
        
        This will be deprecated in Phase 2.
        """
        try:
            # Legacy Part structure with "kind" key
            message_parts = [
                {
                    "kind": "text",
                    "text": message
                }
            ]
            
            message_obj = {
                "role": "user",
                "parts": message_parts,
                "messageId": str(uuid.uuid4()),
                "contextId": context_id
            }
            
            if reference_task_ids:
                message_obj["referenceTaskIds"] = reference_task_ids
            
            # Legacy method name
            legacy_payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "message/send",  # Legacy: lowercase/slash
                "params": {
                    "message": message_obj
                }
            }
            
            response = await client.post(
                f"{agent_url}/tasks/send",
                json=legacy_payload,
                headers=headers or {}
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_a2a_response(result)
            else:
                logger.error(f"Agent returned status {response.status_code}")
                return {
                    "content": f"Agent error: HTTP {response.status_code}",
                    "state": "failed"
                }
                
        except Exception as e:
            logger.error(f"Legacy A2A call failed: {e}")
            return {"content": f"Error communicating with agent: {str(e)}", "state": "failed"}
    
    async def _get_user_mcp_token(self, user_id: str) -> Optional[str]:
        """
        사용자의 MCP Hub 토큰을 가져옵니다.
        
        1. Redis 캐시 확인 (TTL 5분)
        2. 캐시 miss면 DB에서 조회 후 캐시에 저장
        """
        try:
            from uuid import UUID
            user_uuid = UUID(user_id)
            
            # 1. 캐시 확인
            cache = get_token_cache()
            cached_token = await cache.get(user_uuid)
            if cached_token:
                return cached_token
            
            # 2. DB에서 조회
            async with get_db_session() as db:
                service = get_mcp_token_service()
                token = await service.get_token(db, user_uuid)
                
                # 3. 캐시에 저장
                if token:
                    await cache.set(user_uuid, token)
                
                return token
                
        except Exception as e:
            logger.warning(f"[MCP Token] Failed to get token for user {user_id}: {e}")
            return None
    
    async def _stream_from_agent(
        self,
        agent_url: str,
        message: str,
        context_id: str,
        reference_task_ids: list = None,
        user_id: Optional[str] = None,
        jwt_token: Optional[str] = None  # Directive 007: Raw Token
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from agent using A2A protocol SSE (Standard Compliant).
        
        A2A Standard Multi-turn:
        - contextId: Maintains conversation context
        - referenceTaskIds: References previous tasks
        
        Custom Extension:
        - X-MCP-Hub-Token: User-specific MCPHub token
        - X-Request-Id: Request tracking ID for distributed tracing
        - X-User-Id: User identifier
        """
        try:
            # Generate request ID for distributed tracing
            request_id = str(uuid.uuid4())
            
            # Build headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "X-Request-Id": request_id  # 분산 트레이싱용 요청 ID
            }
            
            # Add User-Id header if available
            if user_id:
                headers["X-User-Id"] = user_id
            
            # Add MCP Hub Token if user is authenticated
            if user_id:
                mcp_token = await self._get_user_mcp_token(user_id)
                if mcp_token:
                    headers["X-MCP-Hub-Token"] = mcp_token
            
            # Directive 007: Identity Propagation
            if jwt_token:
                headers["Authorization"] = f"Bearer {jwt_token}"
                logger.debug(f"[A2A Stream] Added Authorization header: Bearer {jwt_token[:10]}...")
            
            logger.debug(f"[A2A Stream] Request ID: {request_id}")
            
            # Use Global Client (Connection Pooling)
            client = GlobalHttpClient.get_client()
            
            # A2A Standard message object (Google Spec)
            message_obj = {
                "role": "user",
                "parts": [{"text": message}],  # A2A Standard: Direct text key
                "messageId": str(uuid.uuid4()),
                "contextId": context_id
            }
            
            # Add referenceTaskIds if available (A2A Standard)
            if reference_task_ids:
                message_obj["referenceTaskIds"] = reference_task_ids
            
            # A2A Standard: StreamMessage (PascalCase)
            # Legacy fallback: message/stream
            payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "StreamMessage",  # A2A Standard: PascalCase
                "params": {
                    "message": message_obj
                }
            }
            
            # Use /tasks/send for streaming (some agents use this endpoint)
            # method: "message/stream"으로 구분, Accept 헤더로 SSE 요청
            async with client.stream(
                "POST",
                f"{agent_url}/tasks/send",
                json=payload,
                headers=headers
            ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            if "content" in data:
                                yield data["content"]
                            elif "text" in data:
                                yield data["text"]
                                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            # Fallback to non-streaming (A2A Standard)
            result = await self._send_to_agent(agent_url, message, context_id, reference_task_ids, user_id)
            yield result.get("content", "Error occurred during streaming.")
    
    def _parse_a2a_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse A2A JSON-RPC response to extract content.
        
        A2A Standard Response (Google Specification):
        - result.message: Standard response with message object
          - role: "agent"
          - parts: [{ "text": "..." }]  # Direct text key (standard)
        - result.task: Task object with status
        
        Legacy Response (backward compatibility):
        - result.artifacts: Array of artifact objects
        - Parts with "kind" or "type" keys
        
        Supports both standard and legacy formats for Phase 1 compatibility.
        """
        try:
            result = response.get("result", {})
            
            # Extract task_id and context_id (A2A Standard)
            task_id = result.get("id")
            context_id = result.get("contextId") or result.get("sessionId")
            
            def is_text_part(part: Dict) -> bool:
                """
                Check if part is text.
                A2A Standard: { "text": "..." } - direct text key
                Legacy: { "kind": "text", "text": "..." } or { "type": "text", "text": "..." }
                """
                # Standard: direct "text" key without kind/type
                if "text" in part and "kind" not in part and "type" not in part:
                    return True
                # Legacy: with kind or type
                return part.get("kind") == "text" or part.get("type") == "text"
            
            def get_text_from_parts(parts: List) -> str:
                """Extract text from parts list (supports standard and legacy)"""
                texts = []
                for p in parts:
                    # Standard format: { "text": "..." }
                    if "text" in p:
                        text = p.get("text", "")
                        if text:
                            texts.append(text)
                    # File format: { "file": { ... } }
                    elif "file" in p:
                        file_info = p.get("file", {})
                        texts.append(f"[File: {file_info.get('name', 'unknown')}]")
                    # Data format: { "data": { ... } }
                    elif "data" in p:
                        texts.append("[Data object]")
                return " ".join(texts)
            
            content = ""
            artifacts = []
            state = "completed"
            
            # Priority 1: A2A Standard - result.message (Google Spec)
            if "message" in result:
                message = result["message"]
                if isinstance(message, dict):
                    parts = message.get("parts", [])
                    content = get_text_from_parts(parts)
                    logger.debug("[A2A] Parsed standard result.message format")
            
            # Priority 2: A2A Standard - result.task.status.message
            if "task" in result and not content:
                task = result["task"]
                task_id = task.get("id", task_id)
                if "status" in task:
                    status = task["status"]
                    state = status.get("state", "completed")
                    status_msg = status.get("message", {})
                    if isinstance(status_msg, dict):
                        parts = status_msg.get("parts", [])
                        content = get_text_from_parts(parts)
                        logger.debug("[A2A] Parsed standard result.task.status.message format")
            
            # Priority 3: Legacy - result.artifacts
            if not content:
                for artifact in result.get("artifacts", []):
                    artifact_parts = artifact.get("parts", [])
                    for part in artifact_parts:
                        if is_text_part(part):
                            text = part.get("text", "")
                            if text and not content:
                                content = text
                            if text:
                                artifacts.append({"text": text})
                        elif part.get("kind") == "data" or part.get("type") == "data" or "data" in part:
                            artifacts.append({"data": part.get("data", {})})
                if content:
                    logger.debug("[A2A] Parsed legacy result.artifacts format")
            
            # Priority 4: Legacy - result.status
            if "status" in result and not content:
                state = result["status"].get("state", "completed")
                status_msg = result["status"].get("message", {})
                if isinstance(status_msg, dict):
                    parts = status_msg.get("parts", [])
                    content = get_text_from_parts(parts)
                    logger.debug("[A2A] Parsed legacy result.status.message format")
            
            return {
                "content": content or "Task completed.",
                "state": state,
                "artifacts": artifacts,
                "task_id": task_id,
                "context_id": context_id
            }
            
        except Exception as e:
            logger.error(f"Error parsing A2A response: {e}")
            return {"content": "Error parsing agent response", "state": "failed"}
    
    def _get_fallback_response(self, message: str) -> str:
        """Generate fallback response when no agent is available."""
        return (
            "죄송합니다. 현재 요청을 처리할 수 있는 적절한 에이전트가 등록되어 있지 않습니다. "
            "관리자에게 문의하시거나 다른 질문을 시도해 주세요.\n\n"
            f"입력하신 내용: \"{message}\"\n\n"
            "현재 등록된 에이전트 목록을 확인하시려면 '/agents' 명령어를 사용해 주세요."
        )


# Global orchestrator instance
orchestrator = A2AOrchestrator()

