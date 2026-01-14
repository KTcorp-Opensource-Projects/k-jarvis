import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from loguru import logger

from .schema import Workflow, WorkflowStep, AgentContext, Artifact, ArtifactType, HandoffRequest
from .enums import WorkflowStepStatus
from .supervisor import supervisor_llm
from .handoff import handoff_detector
from .memory import memory_store

class WorkflowExecutor:
    """Executes multi-agent workflows step by step."""
    
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
        workflow.status = WorkflowStepStatus.RUNNING
        available_agents = available_agents or []
        
        if not workflow.context:
            workflow.context = AgentContext(
                original_user_request=workflow.description,
                workflow_id=workflow.id
            )
        
        if len(workflow.steps) > workflow.max_iterations:
            logger.warning(f"Workflow has {len(workflow.steps)} steps, limiting to {workflow.max_iterations}")
            workflow.steps = workflow.steps[:workflow.max_iterations]
        
        logger.info(f"[START] Starting workflow execution: {workflow.name}")
        
        i = 0
        while i < len(workflow.steps):
            step = workflow.steps[i]
            workflow.current_step_index = i
            
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
                workflow.context.add_previous_result(
                    step_name=f"{step.agent_name}: {step.action}",
                    content=step.output or "",
                    success=True
                )
                for artifact in step.artifacts:
                    workflow.context.artifacts.append(artifact)
                logger.info(f"[OK] Step {i+1} completed: {step.agent_name}")
            else:
                workflow.context.add_previous_result(
                    step_name=f"{step.agent_name}: {step.action}",
                    content=f"[SKIPPED] {step.error}",
                    success=False
                )
                logger.warning(f"[WARN] Step {i+1} skipped: {step.agent_name}")
            
            i += 1
        
        workflow.status = WorkflowStepStatus.COMPLETED
        workflow.completed_at = datetime.now().isoformat()
        workflow.final_output = self._build_final_output(workflow)
        
        logger.info(f"[DONE] Workflow completed: {workflow.name}")
        
        try:
            await memory_store.store_workflow_result(workflow)
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
        max_attempts = 3 if workflow.retry_policy else 1
        max_modify_attempts = 1
        current_task = step.input_prompt
        current_agent_id = step.agent_id
        current_agent_name = step.agent_name
        modify_count = 0
        
        for attempt in range(max_attempts):
            step.retry_count = attempt
            
            try:
                from ..registry import registry
                
                prompt = self._build_step_prompt_with_context(step, workflow.context)
                
                agent = registry.get_agent(current_agent_id) or registry.get_agent_by_name(current_agent_name)
                
                if not agent:
                    raise ValueError(f"Agent not found: {current_agent_name}")
                
                response = await self.orchestrator._send_to_agent(
                    agent.url,
                    prompt,
                    context_id
                )
                
                step.output = response.get("content", "")
                raw_artifacts = response.get("artifacts", [])
                step.artifacts = self._parse_artifacts(raw_artifacts)
                step.mark_completed(step.output)
                
                handoff_request = await self._detect_and_handle_handoff(
                    step, workflow, available_agents, context_id
                )
                if handoff_request:
                    step.validation_result = {
                        "action": "handoff",
                        "target": handoff_request.target_agent_name
                    }
                
                if workflow.supervisor_enabled and self.supervisor.is_available:
                    decision = await self.supervisor.validate_step_result(
                        step, workflow, available_agents
                    )
                    step.validation_result = {
                        "action": decision.action,
                        "confidence": decision.confidence
                    }
                    
                    if decision.action == "abort":
                        step.status = WorkflowStepStatus.FAILED
                        step.error = f"Supervisor aborted: {decision.reasoning}"
                        return False, False
                    
                    if decision.action == "modify" and decision.modified_task:
                        modify_count += 1
                        if modify_count > max_modify_attempts:
                            return True, True
                        current_task = decision.modified_task
                        step.input_prompt = current_task
                        continue
                
                return True, True
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Step attempt {attempt + 1}/{max_attempts} failed: {error_msg}")
                step.error = error_msg
                
                if workflow.supervisor_enabled and self.supervisor.is_available:
                    decision = await self.supervisor.decide_error_recovery(
                        step, error_msg, workflow, available_agents
                    )
                    
                    if decision.action == "abort":
                        step.status = WorkflowStepStatus.FAILED
                        return False, False
                    
                    if decision.action == "skip" and not step.is_critical:
                        step.status = WorkflowStepStatus.SKIPPED
                        return False, True
                    
                    if decision.action == "fallback" and decision.fallback_agent_id:
                        current_agent_id = decision.fallback_agent_id
                        continue
                    
                    if decision.action == "modify" and decision.modified_task:
                        current_task = decision.modified_task
                        step.input_prompt = current_task
                        continue
                    
                    if attempt < max_attempts - 1:
                        backoff = workflow.retry_policy.backoff_seconds if workflow.retry_policy else 1.0
                        await asyncio.sleep(backoff * (attempt + 1))
                        continue
                else:
                    if attempt < max_attempts - 1:
                        backoff = workflow.retry_policy.backoff_seconds if workflow.retry_policy else 1.0
                        await asyncio.sleep(backoff * (attempt + 1))
                        continue
        
        step.status = WorkflowStepStatus.FAILED
        if not step.is_critical:
            step.status = WorkflowStepStatus.SKIPPED
            return False, True
        
        return False, False

    async def _detect_and_handle_handoff(
        self,
        step: WorkflowStep,
        workflow: Workflow,
        available_agents: List[Dict],
        context_id: str
    ) -> Optional[HandoffRequest]:
        if not step.output:
            return None
        
        handoff_request = await handoff_detector.detect(
            step.output,
            available_agents,
            step.agent_name
        )
        
        if not handoff_request:
            return None
        
        target_agent = None
        for agent in available_agents:
            if agent.get('name', '').lower() == handoff_request.target_agent_name.lower():
                target_agent = agent
                break
            if handoff_request.target_agent_name.lower() in agent.get('name', '').lower():
                target_agent = agent
                break
        
        if not target_agent:
            return None
        
        handoff_context = AgentContext(
            task_description=handoff_request.task_description,
            original_user_request=workflow.context.original_user_request if workflow.context else "",
            workflow_id=workflow.id,
            step_index=workflow.current_step_index + 1
        )
        
        handoff_context.add_previous_result(
            step_name=f"{step.agent_name}: {step.action}",
            content=step.output,
            success=True
        )
        handoff_context.metadata.update(handoff_request.context_data)
        
        handoff_step = WorkflowStep(
            agent_id=target_agent.get('id', ''),
            agent_name=target_agent.get('name', ''),
            action=f"handoff_{handoff_request.reason.value}",
            input_prompt=handoff_request.task_description,
            task_description=handoff_request.task_description,
            use_previous_output=True,
            context=handoff_context,
            is_critical=False
        )
        
        workflow.steps.insert(workflow.current_step_index + 1, handoff_step)
        
        workflow.metadata["handoffs"] = workflow.metadata.get("handoffs", [])
        workflow.metadata["handoffs"].append({
            "from": step.agent_name,
            "to": target_agent.get('name'),
            "reason": handoff_request.reason.value,
            "task": handoff_request.task_description[:100]
        })
        
        return handoff_request

    def _build_step_prompt_with_context(self, step: WorkflowStep, context: AgentContext) -> str:
        parts = []
        if step.use_previous_output and context.previous_results:
            last_result = context.previous_results[-1]
            content = last_result['content']
            if len(content) > 5000:
                content = content[:5000] + "\n... (데이터 일부 생략)"
            parts.append(f"[CONTEXT]\n{content}")
        
        parts.append(f"[TASK]\n{step.input_prompt}")
        return "\n\n".join(parts)

    def _parse_artifacts(self, raw_artifacts: List[Any]) -> List[Artifact]:
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

    def _build_final_output(self, workflow: Workflow) -> str:
        outputs = []
        outputs.append(f"## [WORKFLOW] 워크플로우 완료: {workflow.description}\n")
        if workflow.reasoning:
            outputs.append(f"*분석: {workflow.reasoning}*\n")
        
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
            
            outputs.append("")
        
        return "\n".join(outputs)
